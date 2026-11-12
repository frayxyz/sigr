"""Módulo de autenticación de usuarios: clientes, meseros y administrador."""
import sqlite3

from flask import Blueprint, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .seguridad import ROLES, error, requiere_sesion, usuario_actual

bp = Blueprint("auth", __name__, url_prefix="/api")


def _datos():
    return request.get_json(silent=True) or {}


@bp.post("/auth/registro")
def registro():
    """Registro público: crea siempre cuentas de tipo CLIENTE."""
    datos = _datos()
    nombre = (datos.get("nombre") or "").strip()
    email = (datos.get("email") or "").strip().lower()
    password = datos.get("password") or ""
    if not nombre or not email or len(password) < 8:
        return error("Nombre, email y contraseña (mínimo 8 caracteres) son obligatorios.", 400)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, 'CLIENTE')",
            (nombre, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("El email ya está registrado.", 409)
    return {"id": cur.lastrowid, "nombre": nombre, "email": email, "rol": "CLIENTE"}, 201


@bp.post("/auth/login")
def login():
    datos = _datos()
    email = (datos.get("email") or "").strip().lower()
    password = datos.get("password") or ""
    fila = get_db().execute(
        "SELECT id, nombre, email, rol, password_hash, activo FROM usuarios WHERE email = ?",
        (email,),
    ).fetchone()
    if fila is None or not fila["activo"] or not check_password_hash(fila["password_hash"], password):
        return error("Credenciales incorrectas.", 401)
    session.clear()
    session["usuario_id"] = fila["id"]
    return {"id": fila["id"], "nombre": fila["nombre"], "email": fila["email"], "rol": fila["rol"]}


@bp.post("/auth/logout")
def logout():
    session.clear()
    return {"mensaje": "Sesión cerrada."}


@bp.get("/auth/yo")
@requiere_sesion()
def yo():
    return dict(usuario_actual())


@bp.get("/usuarios")
@requiere_sesion("ADMIN")
def listar_usuarios():
    filas = get_db().execute(
        "SELECT id, nombre, email, rol, activo, creado_en FROM usuarios ORDER BY id"
    ).fetchall()
    return {"usuarios": [dict(f) for f in filas]}


@bp.post("/usuarios")
@requiere_sesion("ADMIN")
def crear_usuario():
    """Permite al administrador crear meseros, administradores o clientes."""
    datos = _datos()
    nombre = (datos.get("nombre") or "").strip()
    email = (datos.get("email") or "").strip().lower()
    password = datos.get("password") or ""
    rol = datos.get("rol", "MESERO")
    if rol not in ROLES:
        return error("Rol no válido. Use CLIENTE, MESERO o ADMIN.", 400)
    if not nombre or not email or len(password) < 8:
        return error("Nombre, email y contraseña (mínimo 8 caracteres) son obligatorios.", 400)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
            (nombre, email, generate_password_hash(password), rol),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("El email ya está registrado.", 409)
    return {"id": cur.lastrowid, "nombre": nombre, "email": email, "rol": rol}, 201
