"""Pruebas de cierre de caja y reportes de ventas."""
from datetime import datetime
from base import SigrTestCase


class CajaYReporteTests(SigrTestCase):

    def test_cierre_de_caja_con_pedidos_entregados(self):
        admin = self.login_admin()
        _, plato = self.crear_menu(admin)
        cliente, _ = self.nuevo_cliente()
        pedido = cliente.post("/api/pedidos", json={
            "items": [{"plato_id": plato["id"], "cantidad": 2}]
        }).get_json()

        hoy = datetime.now().strftime("%Y-%m-%d")
        # Con un pedido abierto no se puede cerrar la caja del día.
        self.assertEqual(admin.post("/api/caja/cierres", json={"fecha": hoy}).status_code, 409)

        for estado in ("EN_PREPARACION", "LISTO", "ENTREGADO"):
            admin.patch(f"/api/pedidos/{pedido['id']}/estado", json={"estado": estado})

        r = admin.post("/api/caja/cierres", json={"fecha": hoy})
        self.assertEqual(r.status_code, 201, r.get_json())
        self.assertEqual(r.get_json()["num_pedidos"], 1)
        self.assertEqual(r.get_json()["total_ventas"], 50000)

        # No se puede cerrar dos veces la misma fecha.
        self.assertEqual(admin.post("/api/caja/cierres", json={"fecha": hoy}).status_code, 409)

    def test_reporte_de_ventas_diarias(self):
        admin = self.login_admin()
        _, plato = self.crear_menu(admin)
        cliente, _ = self.nuevo_cliente()
        pedido = cliente.post("/api/pedidos", json={
            "items": [{"plato_id": plato["id"], "cantidad": 3}]
        }).get_json()
        for estado in ("EN_PREPARACION", "LISTO", "ENTREGADO"):
            admin.patch(f"/api/pedidos/{pedido['id']}/estado", json={"estado": estado})

        hoy = datetime.now().strftime("%Y-%m-%d")
        r = admin.get(f"/api/reportes/ventas?desde={hoy}&hasta={hoy}")
        datos = r.get_json()
        self.assertEqual(datos["total_ventas"], 75000)
        self.assertEqual(datos["platos_vendidos"][0]["cantidad"], 3)

    def test_reporte_rechaza_rango_invertido(self):
        admin = self.login_admin()
        r = admin.get("/api/reportes/ventas?desde=2026-02-01&hasta=2026-01-01")
        self.assertEqual(r.status_code, 400)
