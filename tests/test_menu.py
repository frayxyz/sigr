"""Pruebas del menú digital: categorías y platos."""
from base import SigrTestCase


class MenuTests(SigrTestCase):

    def test_crud_de_categorias_y_platos(self):
        admin = self.login_admin()
        cat, plato = self.crear_menu(admin)

        r = admin.put(f"/api/categorias/{cat['id']}", json={"descripcion": "Principales"})
        self.assertEqual(r.get_json()["descripcion"], "Principales")

        r = admin.put(f"/api/platos/{plato['id']}", json={"precio": 27000, "disponible": False})
        self.assertEqual(r.get_json()["precio"], 27000)
        self.assertFalse(r.get_json()["disponible"])

        listado = self.client.get("/api/platos").get_json()["platos"]
        self.assertEqual(len(listado), 1)

        self.assertEqual(admin.delete(f"/api/platos/{plato['id']}").status_code, 200)
        self.assertEqual(admin.get("/api/platos").get_json()["platos"], [])

    def test_no_se_elimina_categoria_con_platos(self):
        admin = self.login_admin()
        cat, _ = self.crear_menu(admin)
        self.assertEqual(admin.delete(f"/api/categorias/{cat['id']}").status_code, 409)

    def test_precio_negativo_se_rechaza(self):
        admin = self.login_admin()
        cat = admin.post("/api/categorias", json={"nombre": "Bebidas"}).get_json()
        r = admin.post("/api/platos", json={"categoria_id": cat["id"], "nombre": "Jugo", "precio": -1})
        self.assertEqual(r.status_code, 400)

    def test_cliente_no_puede_modificar_el_menu(self):
        cliente, _ = self.nuevo_cliente()
        cat = self.login_admin().post("/api/categorias", json={"nombre": "Entradas"}).get_json()
        self.assertEqual(cliente.post("/api/categorias", json={"nombre": "X"}).status_code, 403)
        r = cliente.post("/api/platos", json={"categoria_id": cat["id"], "nombre": "Sopa", "precio": 10})
        self.assertEqual(r.status_code, 403)
