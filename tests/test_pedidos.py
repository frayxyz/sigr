"""Pruebas de pedidos y seguimiento de estado."""
from base import SigrTestCase


class PedidoTests(SigrTestCase):

    def setUp(self):
        super().setUp()
        self.admin = self.login_admin()
        _, self.plato = self.crear_menu(self.admin)
        self.mesero = self.app.test_client()
        self.admin.post("/api/usuarios", json={
            "nombre": "Mesero", "email": "m@sigr.com", "password": "clave12345", "rol": "MESERO",
        })
        self.mesero.post("/api/auth/login", json={"email": "m@sigr.com", "password": "clave12345"})

    def test_cliente_crea_pedido_con_total_calculado(self):
        cliente, _ = self.nuevo_cliente()
        r = cliente.post("/api/pedidos", json={"items": [{"plato_id": self.plato["id"], "cantidad": 2}]})
        self.assertEqual(r.status_code, 201)
        pedido = r.get_json()
        self.assertEqual(pedido["estado"], "PENDIENTE")
        self.assertEqual(pedido["total"], 50000)
        self.assertEqual(pedido["items"][0]["nombre_plato"], "Bandeja paisa")

    def test_pedido_sin_items_o_con_cantidad_invalida(self):
        cliente, _ = self.nuevo_cliente()
        self.assertEqual(cliente.post("/api/pedidos", json={"items": []}).status_code, 400)
        r = cliente.post("/api/pedidos", json={"items": [{"plato_id": self.plato["id"], "cantidad": 0}]})
        self.assertEqual(r.status_code, 400)

    def test_plato_no_disponible_no_se_puede_pedir(self):
        self.admin.put(f"/api/platos/{self.plato['id']}", json={"disponible": False})
        cliente, _ = self.nuevo_cliente()
        r = cliente.post("/api/pedidos", json={"items": [{"plato_id": self.plato["id"], "cantidad": 1}]})
        self.assertEqual(r.status_code, 400)

    def test_flujo_completo_de_estados(self):
        cliente, _ = self.nuevo_cliente()
        pedido = cliente.post("/api/pedidos", json={
            "items": [{"plato_id": self.plato["id"], "cantidad": 1}]
        }).get_json()
        url = f"/api/pedidos/{pedido['id']}/estado"
        for estado in ("EN_PREPARACION", "LISTO", "ENTREGADO"):
            r = self.mesero.patch(url, json={"estado": estado})
            self.assertEqual(r.status_code, 200, r.get_json())
            self.assertEqual(r.get_json()["estado"], estado)

    def test_transicion_invalida_responde_409(self):
        cliente, _ = self.nuevo_cliente()
        pedido = cliente.post("/api/pedidos", json={
            "items": [{"plato_id": self.plato["id"], "cantidad": 1}]
        }).get_json()
        r = self.mesero.patch(f"/api/pedidos/{pedido['id']}/estado", json={"estado": "ENTREGADO"})
        self.assertEqual(r.status_code, 409)

    def test_cliente_solo_ve_sus_pedidos(self):
        ana, _ = self.nuevo_cliente("ana@test.com")
        luis, _ = self.nuevo_cliente("luis@test.com")
        pedido = ana.post("/api/pedidos", json={
            "items": [{"plato_id": self.plato["id"], "cantidad": 1}]
        }).get_json()
        self.assertEqual(luis.get(f"/api/pedidos/{pedido['id']}").status_code, 404)
        self.assertEqual(luis.get("/api/pedidos").get_json()["pedidos"], [])
        self.assertEqual(len(ana.get("/api/pedidos").get_json()["pedidos"]), 1)

    def test_eliminar_plato_conserva_nombre_y_precio_en_pedido(self):
        cliente, _ = self.nuevo_cliente()
        pedido = cliente.post("/api/pedidos", json={
            "items": [{"plato_id": self.plato["id"], "cantidad": 1}]
        }).get_json()
        self.admin.delete(f"/api/platos/{self.plato['id']}")
        r = cliente.get(f"/api/pedidos/{pedido['id']}").get_json()
        self.assertEqual(r["items"][0]["nombre_plato"], "Bandeja paisa")
        self.assertIsNone(r["items"][0]["plato_id"])
