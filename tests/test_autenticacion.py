"""Pruebas de autenticación, gestión de usuarios y control de roles."""
from base import SigrTestCase, ADMIN


class AutenticacionTests(SigrTestCase):

    def test_administrador_inicial_puede_iniciar_sesion(self):
        r = self.client.post("/api/auth/login", json=ADMIN)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["rol"], "ADMIN")

    def test_credenciales_incorrectas(self):
        r = self.client.post("/api/auth/login", json={"email": ADMIN["email"], "password": "mala"})
        self.assertEqual(r.status_code, 401)

    def test_registro_crea_cliente_y_rechaza_email_duplicado(self):
        datos = {"nombre": "Ana", "email": "ana@test.com", "password": "clave12345"}
        self.assertEqual(self.client.post("/api/auth/registro", json=datos).status_code, 201)
        self.assertEqual(self.client.post("/api/auth/registro", json=datos).status_code, 409)

    def test_registro_exige_contrasena_minima(self):
        r = self.client.post("/api/auth/registro", json={
            "nombre": "Ana", "email": "ana2@test.com", "password": "corta",
        })
        self.assertEqual(r.status_code, 400)

    def test_ruta_protegida_sin_sesion_responde_401(self):
        self.assertEqual(self.client.get("/api/usuarios").status_code, 401)

    def test_cliente_no_puede_usar_funciones_de_administrador(self):
        cliente, _ = self.nuevo_cliente()
        self.assertEqual(cliente.get("/api/usuarios").status_code, 403)

    def test_admin_crea_mesero_que_puede_iniciar_sesion(self):
        admin = self.login_admin()
        r = admin.post("/api/usuarios", json={
            "nombre": "Mesero 1", "email": "mesero@sigr.com", "password": "clave12345", "rol": "MESERO",
        })
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)
        r = self.client.post("/api/auth/login", json={"email": "mesero@sigr.com", "password": "clave12345"})
        self.assertEqual(r.get_json()["rol"], "MESERO")
