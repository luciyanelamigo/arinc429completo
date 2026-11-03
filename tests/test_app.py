import unittest

from app import create_app
from extensions import db
from models import Envio, Instrument


class AppCrudTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "unit-test-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_and_delete_instrument_and_envio(self):
        response = self.client.post("/instrumentos/nuevo", data={
            "name": "Altitud", "label_octal": "204", "encoding": "BNR",
            "units": "ft", "minimum": "-1000", "maximum": "1000",
            "resolution": "1", "sdi": "0", "ssm": "0",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            instrument_id = db.session.query(Instrument.id).scalar()
        response = self.client.post("/envios/nuevo", data={
            "instrument_id": str(instrument_id), "value": "125",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            envio = Envio.query.one()
            self.assertEqual(envio.value, 125)
            self.assertEqual(envio.word.bit_count() % 2, 1)
            envio_id = envio.id
        response = self.client.post(f"/envios/{envio_id}/eliminar", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(Envio.query.count(), 0)

    def test_invalid_value_is_not_persisted(self):
        self.client.post("/instrumentos/nuevo", data={
            "name": "Indicador", "label_octal": "001", "encoding": "BNR",
            "units": "", "minimum": "0", "maximum": "10",
            "resolution": "1", "sdi": "0", "ssm": "0",
        })
        with self.app.app_context():
            instrument_id = Instrument.query.one().id
        response = self.client.post("/envios/nuevo", data={
            "instrument_id": str(instrument_id), "value": "11",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"fuera del rango", response.data)
        with self.app.app_context():
            self.assertEqual(Envio.query.count(), 0)


if __name__ == "__main__":
    unittest.main()
