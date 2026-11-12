"""Pruebas de reservas por fecha y hora."""
from datetime import datetime, timedelta
from base import SigrTestCase, _manana


class ReservaTests(SigrTestCase):
    max_reservas = 1

    def test_reserva_y_cancelacion(self):
        cliente, _ = self.nuevo_cliente()
        r = cliente.post("/api/reservas", json={"fecha": _manana(), "hora": "19:30", "personas": 4})
        self.assertEqual(r.status_code, 201)
        reserva = r.get_json()
        self.assertEqual(reserva["estado"], "CONFIRMADA")
        r = cliente.patch(f"/api/reservas/{reserva['id']}/cancelar")
        self.assertEqual(r.get_json()["estado"], "CANCELADA")

    def test_horario_completo_responde_409(self):
        ana, _ = self.nuevo_cliente("ana@test.com")
        luis, _ = self.nuevo_cliente("luis@test.com")
        datos = {"fecha": _manana(), "hora": "20:00", "personas": 2}
        self.assertEqual(ana.post("/api/reservas", json=datos).status_code, 201)
        self.assertEqual(luis.post("/api/reservas", json=datos).status_code, 409)

    def test_no_se_reserva_en_el_pasado(self):
        cliente, _ = self.nuevo_cliente()
        ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        r = cliente.post("/api/reservas", json={"fecha": ayer, "hora": "12:00", "personas": 2})
        self.assertEqual(r.status_code, 400)

    def test_formato_de_fecha_y_personas_invalidos(self):
        cliente, _ = self.nuevo_cliente()
        r = cliente.post("/api/reservas", json={"fecha": "11-11-2026", "hora": "12:00", "personas": 2})
        self.assertEqual(r.status_code, 400)
        r = cliente.post("/api/reservas", json={"fecha": _manana(), "hora": "12:00", "personas": 0})
        self.assertEqual(r.status_code, 400)
