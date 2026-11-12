"""Clase base y datos comunes para las pruebas de integración del SIGR."""
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app import create_app

ADMIN = {"email": "admin@sigr.local", "password": "admin12345"}


def _manana():
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


class SigrTestCase(unittest.TestCase):
    max_reservas = 10

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        ruta_db = Path(self._tmp.name) / "test.db"
        self.app = create_app({
            "TESTING": True,
            "DATABASE": str(ruta_db),
            "MAX_RESERVAS_POR_HORA": self.max_reservas,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self._tmp.cleanup()

    def nuevo_cliente(self, email="cliente@test.com"):
        cliente = self.app.test_client()
        r = cliente.post("/api/auth/registro", json={
            "nombre": "Cliente Prueba", "email": email, "password": "clave12345",
        })
        self.assertEqual(r.status_code, 201, r.get_json())
        r = cliente.post("/api/auth/login", json={"email": email, "password": "clave12345"})
        self.assertEqual(r.status_code, 200)
        return cliente, r.get_json()

    def login_admin(self):
        r = self.client.post("/api/auth/login", json=ADMIN)
        self.assertEqual(r.status_code, 200)
        return self.client

    def crear_menu(self, admin):
        cat = admin.post("/api/categorias", json={"nombre": "Platos fuertes"}).get_json()
        plato = admin.post("/api/platos", json={
            "categoria_id": cat["id"], "nombre": "Bandeja paisa", "precio": 25000,
        })
        self.assertEqual(plato.status_code, 201, plato.get_json())
        return cat, plato.get_json()
