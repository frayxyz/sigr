"""Módulo de menú digital: CRUD de categorías y platos."""
import sqlite3

from flask import Blueprint, request

from .db import get_db
from .seguridad import error, requiere_sesion

bp = Blueprint("menu", __name__, url_prefix="/api")


def _datos():
    return request.get_json(silent=True) or {}


def _categoria(categoria_id):
    fila = get_db().execute(
        "SELECT id, nombre, descripcion FROM categorias WHERE id = ?", (categoria_id,)
    ).fetchone()
    return dict(fila) if fila else None


def _plato(plato_id):
    fila = get_db().execute(
        """SELECT p.id, p.categoria_id, c.nombre AS categoria, p.nombre, p.descripcion,
                  p.precio, p.disponible
           FROM platos p JOIN categorias c ON c.id = p.categoria_id
           WHERE p.id = ?""",
        (plato_id,),
    ).fetchone()
    if fila is None:
        return None
    resultado = dict(fila)
    resultado["disponible"] = bool(resultado["disponible"])
    return resultado


# ---------- Categorías ----------

@bp.get("/categorias")
def listar_categorias():
    filas = get_db().execute(
        "SELECT id, nombre, descripcion FROM categorias ORDER BY nombre"
    ).fetchall()
    return {"categorias": [dict(f) for f in filas]}


@bp.post("/categorias")
@requiere_sesion("ADMIN")
def crear_categoria():
    datos = _datos()
    nombre = (datos.get("nombre") or "").strip()
    if not nombre:
        return error("El nombre de la categoría es obligatorio.", 400)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)",
            (nombre, datos.get("descripcion")),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("La categoría ya existe.", 409)
    return _categoria(cur.lastrowid), 201


@bp.put("/categorias/<int:categoria_id>")
@requiere_sesion("ADMIN")
def actualizar_categoria(categoria_id):
    if _categoria(categoria_id) is None:
        return error("Categoría no encontrada.", 404)
    datos = _datos()
    if "nombre" in datos and not (datos["nombre"] or "").strip():
        return error("El nombre no puede estar vacío.", 400)
    db = get_db()
    try:
        db.execute(
            "UPDATE categorias SET nombre = COALESCE(?, nombre), descripcion = COALESCE(?, descripcion) WHERE id = ?",
            (
                (datos["nombre"].strip() if "nombre" in datos else None),
                datos.get("descripcion"),
                categoria_id,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("Ya existe una categoría con ese nombre.", 409)
    return _categoria(categoria_id)


@bp.delete("/categorias/<int:categoria_id>")
@requiere_sesion("ADMIN")
def eliminar_categoria(categoria_id):
    if _categoria(categoria_id) is None:
        return error("Categoría no encontrada.", 404)
    db = get_db()
    try:
        db.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
        db.commit()
    except sqlite3.IntegrityError:
        return error("No se puede eliminar: la categoría tiene platos asociados.", 409)
    return {"mensaje": "Categoría eliminada."}


# ---------- Platos ----------

@bp.get("/platos")
def listar_platos():
    categoria_id = request.args.get("categoria_id", type=int)
    sql = """SELECT p.id, p.categoria_id, c.nombre AS categoria, p.nombre, p.descripcion,
                    p.precio, p.disponible
             FROM platos p JOIN categorias c ON c.id = p.categoria_id"""
    params = []
    if categoria_id is not None:
        sql += " WHERE p.categoria_id = ?"
        params.append(categoria_id)
    sql += " ORDER BY c.nombre, p.nombre"
    filas = get_db().execute(sql, params).fetchall()
    platos = []
    for f in filas:
        d = dict(f)
        d["disponible"] = bool(d["disponible"])
        platos.append(d)
    return {"platos": platos}


def _validar_precio(precio):
    return isinstance(precio, (int, float)) and not isinstance(precio, bool) and precio >= 0


@bp.post("/platos")
@requiere_sesion("ADMIN")
def crear_plato():
    datos = _datos()
    nombre = (datos.get("nombre") or "").strip()
    precio = datos.get("precio")
    if not nombre or not _validar_precio(precio):
        return error("Nombre y precio (número mayor o igual a 0) son obligatorios.", 400)
    if not isinstance(datos.get("categoria_id"), int):
        return error("categoria_id es obligatorio.", 400)
    db = get_db()
    try:
        cur = db.execute(
            """INSERT INTO platos (categoria_id, nombre, descripcion, precio, disponible)
               VALUES (?, ?, ?, ?, ?)""",
            (
                datos["categoria_id"],
                nombre,
                datos.get("descripcion"),
                round(float(precio), 2),
                1 if datos.get("disponible", True) else 0,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("La categoría indicada no existe.", 400)
    return _plato(cur.lastrowid), 201


@bp.put("/platos/<int:plato_id>")
@requiere_sesion("ADMIN")
def actualizar_plato(plato_id):
    actual = _plato(plato_id)
    if actual is None:
        return error("Plato no encontrado.", 404)
    datos = _datos()
    if "precio" in datos and not _validar_precio(datos["precio"]):
        return error("El precio debe ser un número mayor o igual a 0.", 400)
    if "nombre" in datos and not (datos["nombre"] or "").strip():
        return error("El nombre no puede estar vacío.", 400)
    valores = {
        "categoria_id": datos.get("categoria_id", actual["categoria_id"]),
        "nombre": (datos["nombre"].strip() if "nombre" in datos else actual["nombre"]),
        "descripcion": datos.get("descripcion", actual["descripcion"]),
        "precio": round(float(datos["precio"]), 2) if "precio" in datos else actual["precio"],
        "disponible": (1 if datos["disponible"] else 0) if "disponible" in datos else int(actual["disponible"]),
    }
    db = get_db()
    try:
        db.execute(
            """UPDATE platos SET categoria_id = ?, nombre = ?, descripcion = ?, precio = ?, disponible = ?
               WHERE id = ?""",
            (*valores.values(), plato_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("La categoría indicada no existe.", 400)
    return _plato(plato_id)


@bp.delete("/platos/<int:plato_id>")
@requiere_sesion("ADMIN")
def eliminar_plato(plato_id):
    if _plato(plato_id) is None:
        return error("Plato no encontrado.", 404)
    db = get_db()
    db.execute("DELETE FROM platos WHERE id = ?", (plato_id,))
    db.commit()
    return {"mensaje": "Plato eliminado. Los pedidos anteriores conservan su nombre y precio."}
