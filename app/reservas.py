"""Módulo de reservas por fecha y hora."""
import sqlite3
from datetime import datetime

from flask import Blueprint, current_app, request

from .db import get_db
from .seguridad import error, requiere_sesion, usuario_actual

bp = Blueprint("reservas", __name__, url_prefix="/api/reservas")

PERSONAL = ("MESERO", "ADMIN")


def _reserva(reserva_id):
    fila = get_db().execute(
        "SELECT id, usuario_id, fecha, hora, personas, estado, creado_en FROM reservas WHERE id = ?",
        (reserva_id,),
    ).fetchone()
    return dict(fila) if fila else None


@bp.post("")
@requiere_sesion("CLIENTE", "MESERO", "ADMIN")
def crear_reserva():
    usuario = usuario_actual()
    datos = request.get_json(silent=True) or {}
    try:
        fecha = datetime.strptime(str(datos.get("fecha", "")), "%Y-%m-%d")
        hora = datetime.strptime(str(datos.get("hora", "")), "%H:%M")
    except ValueError:
        return error("Fecha (AAAA-MM-DD) u hora (HH:MM) no válidas.", 400)

    personas = datos.get("personas")
    if not isinstance(personas, int) or isinstance(personas, bool) or not 1 <= personas <= 20:
        return error("El número de personas debe estar entre 1 y 20.", 400)

    momento = datetime.combine(fecha.date(), hora.time())
    if momento < datetime.now():
        return error("No se pueden registrar reservas en el pasado.", 400)

    cliente_id = usuario["id"]
    if usuario["rol"] in PERSONAL and datos.get("cliente_id") is not None:
        cliente_id = datos["cliente_id"]

    fecha_txt = fecha.strftime("%Y-%m-%d")
    hora_txt = hora.strftime("%H:%M")
    db = get_db()
    ocupadas = db.execute(
        "SELECT COUNT(*) FROM reservas WHERE fecha = ? AND hora = ? AND estado = 'CONFIRMADA'",
        (fecha_txt, hora_txt),
    ).fetchone()[0]
    if ocupadas >= current_app.config["MAX_RESERVAS_POR_HORA"]:
        return error("No hay disponibilidad para ese horario.", 409)

    try:
        cur = db.execute(
            """INSERT INTO reservas (usuario_id, fecha, hora, personas, estado, creado_en)
               VALUES (?, ?, ?, ?, 'CONFIRMADA', ?)""",
            (cliente_id, fecha_txt, hora_txt, personas, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return error("El cliente indicado no existe.", 400)
    return _reserva(cur.lastrowid), 201


@bp.get("")
@requiere_sesion("CLIENTE", "MESERO", "ADMIN")
def listar_reservas():
    usuario = usuario_actual()
    fecha = request.args.get("fecha")
    sql = "SELECT id, usuario_id, fecha, hora, personas, estado, creado_en FROM reservas WHERE 1=1"
    params = []
    if usuario["rol"] == "CLIENTE":
        sql += " AND usuario_id = ?"
        params.append(usuario["id"])
    if fecha:
        sql += " AND fecha = ?"
        params.append(fecha)
    sql += " ORDER BY fecha, hora"
    filas = get_db().execute(sql, params).fetchall()
    return {"reservas": [dict(f) for f in filas]}


@bp.patch("/<int:reserva_id>/cancelar")
@requiere_sesion("CLIENTE", "MESERO", "ADMIN")
def cancelar_reserva(reserva_id):
    usuario = usuario_actual()
    reserva = _reserva(reserva_id)
    if reserva is None or (usuario["rol"] == "CLIENTE" and reserva["usuario_id"] != usuario["id"]):
        return error("Reserva no encontrada.", 404)
    if reserva["estado"] == "CANCELADA":
        return error("La reserva ya está cancelada.", 409)
    db = get_db()
    db.execute("UPDATE reservas SET estado = 'CANCELADA' WHERE id = ?", (reserva_id,))
    db.commit()
    return _reserva(reserva_id)
