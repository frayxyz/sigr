"""Módulo de cierre de caja y reportes de ventas."""
from datetime import date, datetime

from flask import Blueprint, request

from .db import get_db
from .pedidos import ESTADOS_ABIERTOS
from .seguridad import error, requiere_sesion, usuario_actual

bp = Blueprint("caja", __name__, url_prefix="/api")


def _fecha_valida(texto):
    try:
        return datetime.strptime(str(texto), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


@bp.post("/caja/cierres")
@requiere_sesion("ADMIN")
def cerrar_caja():
    """Cierra la caja de un día. Solo permitido si no quedan pedidos abiertos de esa fecha."""
    usuario = usuario_actual()
    fecha = _fecha_valida((request.get_json(silent=True) or {}).get("fecha"))
    if fecha is None:
        return error("Fecha no válida (use AAAA-MM-DD).", 400)

    db = get_db()
    if db.execute("SELECT 1 FROM cierres_caja WHERE fecha = ?", (fecha,)).fetchone():
        return error("La caja de esa fecha ya fue cerrada.", 409)

    marcadores = ",".join("?" * len(ESTADOS_ABIERTOS))
    abiertos = db.execute(
        f"""SELECT COUNT(*) FROM pedidos
            WHERE date(creado_en) = ? AND estado IN ({marcadores})""",
        (fecha, *ESTADOS_ABIERTOS),
    ).fetchone()[0]
    if abiertos:
        return error(f"Existen {abiertos} pedido(s) sin entregar o cancelar en esa fecha.", 409)

    resumen = db.execute(
        """SELECT COUNT(*) AS num_pedidos, COALESCE(SUM(total), 0) AS total
           FROM pedidos WHERE date(creado_en) = ? AND estado = 'ENTREGADO'""",
        (fecha,),
    ).fetchone()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = db.execute(
        """INSERT INTO cierres_caja (fecha, num_pedidos, total_ventas, creado_por, creado_en)
           VALUES (?, ?, ?, ?, ?)""",
        (fecha, resumen["num_pedidos"], round(resumen["total"], 2), usuario["id"], ahora),
    )
    db.commit()
    return dict(
        db.execute("SELECT * FROM cierres_caja WHERE id = ?", (cur.lastrowid,)).fetchone()
    ), 201


@bp.get("/caja/cierres")
@requiere_sesion("ADMIN")
def listar_cierres():
    filas = get_db().execute(
        "SELECT * FROM cierres_caja ORDER BY fecha DESC"
    ).fetchall()
    return {"cierres": [dict(f) for f in filas]}


@bp.get("/reportes/ventas")
@requiere_sesion("ADMIN")
def reporte_ventas():
    """Ventas entregadas entre dos fechas (por defecto, el día actual)."""
    hoy = date.today().strftime("%Y-%m-%d")
    desde = _fecha_valida(request.args.get("desde", hoy))
    hasta = _fecha_valida(request.args.get("hasta", desde or hoy))
    if desde is None or hasta is None or desde > hasta:
        return error("Rango de fechas no válido (use AAAA-MM-DD, desde <= hasta).", 400)

    db = get_db()
    por_dia = db.execute(
        """SELECT date(creado_en) AS fecha, COUNT(*) AS num_pedidos,
                  ROUND(SUM(total), 2) AS total
           FROM pedidos
           WHERE estado = 'ENTREGADO' AND date(creado_en) BETWEEN ? AND ?
           GROUP BY date(creado_en) ORDER BY fecha""",
        (desde, hasta),
    ).fetchall()
    platos = db.execute(
        """SELECT pi.nombre_plato AS plato, SUM(pi.cantidad) AS cantidad,
                  ROUND(SUM(pi.subtotal), 2) AS ingresos
           FROM pedido_items pi JOIN pedidos p ON p.id = pi.pedido_id
           WHERE p.estado = 'ENTREGADO' AND date(p.creado_en) BETWEEN ? AND ?
           GROUP BY pi.nombre_plato ORDER BY ingresos DESC""",
        (desde, hasta),
    ).fetchall()
    total = round(sum(f["total"] for f in por_dia), 2)
    return {
        "desde": desde,
        "hasta": hasta,
        "total_ventas": total,
        "por_dia": [dict(f) for f in por_dia],
        "platos_vendidos": [dict(f) for f in platos],
    }
