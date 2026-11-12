"""Módulo de pedidos: registro y seguimiento de estado."""
from datetime import datetime

from flask import Blueprint, request

from .db import get_db
from .seguridad import error, requiere_sesion, usuario_actual

bp = Blueprint("pedidos", __name__, url_prefix="/api/pedidos")

PERSONAL = ("MESERO", "ADMIN")
ESTADOS = ("PENDIENTE", "EN_PREPARACION", "LISTO", "ENTREGADO", "CANCELADO")
ESTADOS_ABIERTOS = ("PENDIENTE", "EN_PREPARACION", "LISTO")

# Flujo permitido del pedido. ENTREGADO y CANCELADO son estados finales.
TRANSICIONES = {
    "PENDIENTE": {"EN_PREPARACION", "CANCELADO"},
    "EN_PREPARACION": {"LISTO", "CANCELADO"},
    "LISTO": {"ENTREGADO"},
    "ENTREGADO": set(),
    "CANCELADO": set(),
}


def _ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _pedido_completo(pedido_id):
    db = get_db()
    pedido = db.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if pedido is None:
        return None
    items = db.execute(
        """SELECT plato_id, nombre_plato, precio_unitario, cantidad, subtotal
           FROM pedido_items WHERE pedido_id = ? ORDER BY id""",
        (pedido_id,),
    ).fetchall()
    resultado = dict(pedido)
    resultado["items"] = [dict(i) for i in items]
    return resultado


@bp.post("")
@requiere_sesion("CLIENTE", "MESERO", "ADMIN")
def crear_pedido():
    usuario = usuario_actual()
    datos = request.get_json(silent=True) or {}
    items = datos.get("items")
    if not isinstance(items, list) or not items:
        return error("El pedido debe incluir al menos un plato.", 400)

    db = get_db()

    # Solo el personal puede registrar un pedido a nombre de otro cliente.
    cliente_id = usuario["id"]
    if usuario["rol"] in PERSONAL and datos.get("cliente_id") is not None:
        cliente = db.execute(
            "SELECT id FROM usuarios WHERE id = ? AND rol = 'CLIENTE' AND activo = 1",
            (datos["cliente_id"],),
        ).fetchone()
        if cliente is None:
            return error("El cliente indicado no existe.", 400)
        cliente_id = cliente["id"]

    lineas = []
    total = 0.0
    for item in items:
        if not isinstance(item, dict):
            return error("Cada item debe ser un objeto con plato_id y cantidad.", 400)
        cantidad = item.get("cantidad")
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
            return error("La cantidad debe ser un entero mayor que 0.", 400)
        plato = db.execute(
            "SELECT id, nombre, precio, disponible FROM platos WHERE id = ?",
            (item.get("plato_id"),),
        ).fetchone()
        if plato is None or not plato["disponible"]:
            return error(f"El plato {item.get('plato_id')} no existe o no está disponible.", 400)
        subtotal = round(plato["precio"] * cantidad, 2)
        total += subtotal
        lineas.append((plato["id"], plato["nombre"], plato["precio"], cantidad, subtotal))

    ahora = _ahora()
    cur = db.execute(
        """INSERT INTO pedidos (usuario_id, estado, total, creado_en, actualizado_en)
           VALUES (?, 'PENDIENTE', ?, ?, ?)""",
        (cliente_id, round(total, 2), ahora, ahora),
    )
    pedido_id = cur.lastrowid
    db.executemany(
        """INSERT INTO pedido_items (pedido_id, plato_id, nombre_plato, precio_unitario, cantidad, subtotal)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(pedido_id, *linea) for linea in lineas],
    )
    db.commit()
    return _pedido_completo(pedido_id), 201


@bp.get("")
@requiere_sesion("CLIENTE", "MESERO", "ADMIN")
def listar_pedidos():
    """Consulta de seguimiento: el cliente ve sus pedidos; el personal ve todos."""
    usuario = usuario_actual()
    estado = request.args.get("estado")
    if estado is not None and estado not in ESTADOS:
        return error("Estado no válido.", 400)

    sql = "SELECT id, usuario_id, estado, total, creado_en, actualizado_en FROM pedidos WHERE 1=1"
    params = []
    if usuario["rol"] == "CLIENTE":
        sql += " AND usuario_id = ?"
        params.append(usuario["id"])
    if estado:
        sql += " AND estado = ?"
        params.append(estado)
    sql += " ORDER BY id DESC"
    filas = get_db().execute(sql, params).fetchall()
    return {"pedidos": [dict(f) for f in filas]}


@bp.get("/<int:pedido_id>")
@requiere_sesion("CLIENTE", "MESERO", "ADMIN")
def obtener_pedido(pedido_id):
    usuario = usuario_actual()
    pedido = _pedido_completo(pedido_id)
    if pedido is None or (usuario["rol"] == "CLIENTE" and pedido["usuario_id"] != usuario["id"]):
        return error("Pedido no encontrado.", 404)
    return pedido


@bp.patch("/<int:pedido_id>/estado")
@requiere_sesion(*PERSONAL)
def cambiar_estado(pedido_id):
    nuevo = (request.get_json(silent=True) or {}).get("estado")
    db = get_db()
    pedido = db.execute("SELECT estado FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if pedido is None:
        return error("Pedido no encontrado.", 404)
    if nuevo not in ESTADOS:
        return error("Estado no válido.", 400)
    actual = pedido["estado"]
    if nuevo not in TRANSICIONES[actual]:
        return error(f"No se puede cambiar un pedido de {actual} a {nuevo}.", 409)
    db.execute(
        "UPDATE pedidos SET estado = ?, actualizado_en = ? WHERE id = ?",
        (nuevo, _ahora(), pedido_id),
    )
    db.commit()
    return _pedido_completo(pedido_id)
