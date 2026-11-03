import os
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

from arinc429 import build_word, encode_data, word_hex
from extensions import db
from models import Envio, Instrument


def create_app(test_config=None):
    app = Flask(__name__, instance_path=str(Path(__file__).parent / "instance"))
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///arinc429.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    def parse_instrument_form(instrument=None):
        name = request.form.get("name", "").strip()
        label = request.form.get("label_octal", "").strip()
        encoding = request.form.get("encoding", "BNR").strip().upper()
        units = request.form.get("units", "").strip()
        try:
            minimum = float(request.form["minimum"])
            maximum = float(request.form["maximum"])
            resolution = float(request.form["resolution"])
            sdi = int(request.form["sdi"])
            ssm = int(request.form["ssm"])
            # Validate label and bit fields using the real encoder.
            build_word(label, sdi, 0, ssm)
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("Revisa etiqueta octal, rango, resolución, SDI y SSM.") from exc
        if not name or encoding not in {"BNR", "UINT"}:
            raise ValueError("El nombre es obligatorio y la codificación debe ser BNR o UINT.")
        if minimum > maximum or resolution <= 0:
            raise ValueError("El mínimo debe ser menor o igual al máximo y la resolución > 0.")
        target = instrument or Instrument()
        target.name, target.label_octal, target.encoding = name, label, encoding
        target.units, target.minimum, target.maximum = units, minimum, maximum
        target.resolution, target.sdi, target.ssm = resolution, sdi, ssm
        return target

    def encode_for(instrument, value):
        if not instrument.minimum <= value <= instrument.maximum:
            raise ValueError("El valor está fuera del rango del instrumento.")
        data = encode_data(value, instrument.encoding, instrument.resolution)
        return build_word(instrument.label_octal, instrument.sdi, data, instrument.ssm)

    @app.get("/")
    def index():
        envios = Envio.query.order_by(Envio.created_at.desc()).all()
        return render_template("index.html", envios=envios, instruments=Instrument.query.order_by(Instrument.name).all())

    @app.route("/instrumentos/nuevo", methods=["GET", "POST"])
    @app.route("/instrumentos/<int:instrument_id>/editar", methods=["GET", "POST"])
    def instrument_form(instrument_id=None):
        instrument = db.get_or_404(Instrument, instrument_id) if instrument_id else None
        if request.method == "POST":
            try:
                target = parse_instrument_form(instrument)
                db.session.add(target)
                db.session.commit()
                flash("Instrumento guardado.", "success")
                return redirect(url_for("index"))
            except ValueError as exc:
                flash(str(exc), "error")
            except SQLAlchemyError:
                db.session.rollback()
                flash("No se pudo guardar el instrumento en la base de datos.", "error")
        return render_template("instrument_form.html", instrument=instrument)

    @app.post("/instrumentos/<int:instrument_id>/eliminar")
    def instrument_delete(instrument_id):
        instrument = db.get_or_404(Instrument, instrument_id)
        db.session.delete(instrument)
        db.session.commit()
        flash("Instrumento eliminado junto con sus envíos asociados.", "success")
        return redirect(url_for("index"))

    @app.route("/envios/nuevo", methods=["GET", "POST"])
    @app.route("/envios/<int:envio_id>/editar", methods=["GET", "POST"])
    def envio_form(envio_id=None):
        envio = db.get_or_404(Envio, envio_id) if envio_id else None
        instruments = Instrument.query.order_by(Instrument.name).all()
        if request.method == "POST":
            try:
                instrument = db.get_or_404(Instrument, int(request.form["instrument_id"]))
                value = float(request.form["value"])
                word = encode_for(instrument, value)
                target = envio or Envio()
                target.instrument, target.value, target.word = instrument, value, word
                target.status = "preparado"
                db.session.add(target)
                db.session.commit()
                flash("Envío creado/actualizado y palabra ARINC429 calculada; no se transmitió al hardware.", "success")
                return redirect(url_for("index"))
            except (KeyError, ValueError, TypeError) as exc:
                flash(str(exc) or "Revisa el valor ingresado.", "error")
            except SQLAlchemyError:
                db.session.rollback()
                flash("No se pudo guardar el envío en la base de datos.", "error")
        return render_template("envio_form.html", envio=envio, instruments=instruments)

    @app.post("/envios/<int:envio_id>/transmitir")
    def envio_transmit(envio_id):
        envio = db.get_or_404(Envio, envio_id)
        try:
            from serial_output import transmit_raw_word
            transmit_raw_word(envio.word)
            envio.status = "transmitido-serial"
            db.session.commit()
            flash("Bytes enviados al puerto serial configurado. Esto no confirma transmisión ARINC429 por el bus.", "success")
        except (RuntimeError, OSError, ValueError) as exc:
            flash(f"No se transmitió: {exc}", "error")
        return redirect(url_for("index"))

    @app.post("/envios/<int:envio_id>/eliminar")
    def envio_delete(envio_id):
        envio = db.get_or_404(Envio, envio_id)
        db.session.delete(envio)
        db.session.commit()
        flash("Envío eliminado.", "success")
        return redirect(url_for("index"))

    @app.get("/envios/<int:envio_id>")
    def envio_detail(envio_id):
        envio = db.get_or_404(Envio, envio_id)
        return render_template("envio_detail.html", envio=envio, word_hex=word_hex(envio.word))

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
