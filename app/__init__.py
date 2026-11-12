"""Fábrica de la aplicación Flask del Sistema Integral de Gestión de Restaurante (SIGR)."""
import os
import sqlite3
from pathlib import Path

from flask import Flask, request
from werkzeug.security import generate_password_hash

from .db import close_db, get_db, init_db
from .seguridad import ROLES, error  # noqa: F401  (ROLES se re-exporta)

VERSION = "1.0.0"


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.update(
        VERSION=VERSION,
        SECRET_KEY=os.environ.get("SIGR_SECRET_KEY", "cambiar-en-produccion"),
        DATABASE=os.environ.get(
            "SIGR_DATABASE",
            str(Path(app.root_path).parent / "instance" / "sigr.db"),
        ),
        ADMIN_EMAIL=os.environ.get("SIGR_ADMIN_EMAIL", "admin@sigr.local"),
        ADMIN_PASSWORD=os.environ.get("SIGR_ADMIN_PASSWORD", "admin12345"),
        MAX_RESERVAS_POR_HORA=int(os.environ.get("SIGR_MAX_RESERVAS_HORA", "10")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)

    with app.app_context():
        _crear_admin_inicial(app)

    from .auth import bp as auth_bp
    from .caja import bp as caja_bp
    from .menu import bp as menu_bp
    from .pedidos import bp as pedidos_bp
    from .reservas import bp as reservas_bp

    for blueprint in (auth_bp, menu_bp, pedidos_bp, reservas_bp, caja_bp):
        app.register_blueprint(blueprint)

    @app.get("/")
    def inicio():
        return {"sistema": "SIGR", "version": VERSION, "documentacion": "README.md"}

    @app.get("/api/salud")
    def salud():
        return {"estado": "ok"}

    @app.errorhandler(404)
    def no_encontrado(_):
        return error("Recurso no encontrado.", 404)

    @app.errorhandler(405)
    def metodo_no_permitido(_):
        return error("Método no permitido.", 405)

    @app.errorhandler(500)
    def error_interno(_):
        return error("Error interno del servidor.", 500)

    return app


def _crear_admin_inicial(app):
    """Crea el primer administrador si no existe ninguno."""
    db = get_db()
    if db.execute("SELECT 1 FROM usuarios WHERE rol = 'ADMIN'").fetchone():
        return
    db.execute(
        "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, 'ADMIN')",
        (
            "Administrador",
            app.config["ADMIN_EMAIL"],
            generate_password_hash(app.config["ADMIN_PASSWORD"]),
        ),
    )
    db.commit()
    if not app.config.get("TESTING") and app.config["ADMIN_PASSWORD"] == "admin12345":
        app.logger.warning(
            "Administrador creado con contraseña por defecto. Cámbiela con SIGR_ADMIN_PASSWORD."
        )
