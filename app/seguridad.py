"""Autenticación por sesión y control de acceso por rol."""
from functools import wraps

from flask import g, jsonify, session

from .db import get_db

ROLES = ("CLIENTE", "MESERO", "ADMIN")


def error(mensaje, codigo):
    return jsonify({"error": mensaje}), codigo


def usuario_actual():
    """Devuelve el usuario de la sesión activa o None."""
    if "usuario" not in g:
        g.usuario = None
        uid = session.get("usuario_id")
        if uid is not None:
            g.usuario = get_db().execute(
                "SELECT id, nombre, email, rol FROM usuarios WHERE id = ? AND activo = 1",
                (uid,),
            ).fetchone()
    return g.usuario


def requiere_sesion(*roles):
    """Decorador: exige sesión iniciada y, opcionalmente, uno de los roles indicados."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            usuario = usuario_actual()
            if usuario is None:
                return error("Debe iniciar sesión.", 401)
            if roles and usuario["rol"] not in roles:
                return error("No tiene permisos para esta operación.", 403)
            return vista(*args, **kwargs)

        return envoltura

    return decorador
