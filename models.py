from datetime import datetime, timezone

from extensions import db


class Instrument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    label_octal = db.Column(db.String(3), nullable=False)
    encoding = db.Column(db.String(8), nullable=False, default="BNR")
    units = db.Column(db.String(32), nullable=False, default="")
    minimum = db.Column(db.Float, nullable=False)
    maximum = db.Column(db.Float, nullable=False)
    resolution = db.Column(db.Float, nullable=False, default=1.0)
    sdi = db.Column(db.Integer, nullable=False, default=0)
    ssm = db.Column(db.Integer, nullable=False, default=0)
    envios = db.relationship("Envio", back_populates="instrument", cascade="all, delete-orphan")


class Envio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey("instrument.id"), nullable=False)
    value = db.Column(db.Float, nullable=False)
    word = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="preparado")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    instrument = db.relationship("Instrument", back_populates="envios")
