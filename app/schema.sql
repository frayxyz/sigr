-- Esquema de base de datos del SIGR (SQLite 3)
-- Se ejecuta de forma idempotente al iniciar la aplicación.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    rol             TEXT    NOT NULL CHECK (rol IN ('CLIENTE', 'MESERO', 'ADMIN')),
    activo          INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS categorias (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE,
    descripcion     TEXT
);

CREATE TABLE IF NOT EXISTS platos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id    INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
    nombre          TEXT    NOT NULL,
    descripcion     TEXT,
    precio          REAL    NOT NULL CHECK (precio >= 0),
    disponible      INTEGER NOT NULL DEFAULT 1 CHECK (disponible IN (0, 1))
);

CREATE TABLE IF NOT EXISTS pedidos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    estado          TEXT    NOT NULL DEFAULT 'PENDIENTE'
                    CHECK (estado IN ('PENDIENTE', 'EN_PREPARACION', 'LISTO', 'ENTREGADO', 'CANCELADO')),
    total           REAL    NOT NULL CHECK (total >= 0),
    creado_en       TEXT    NOT NULL,
    actualizado_en  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id       INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    plato_id        INTEGER REFERENCES platos(id) ON DELETE SET NULL,
    nombre_plato    TEXT    NOT NULL,
    precio_unitario REAL    NOT NULL CHECK (precio_unitario >= 0),
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    subtotal        REAL    NOT NULL CHECK (subtotal >= 0)
);

CREATE TABLE IF NOT EXISTS reservas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    fecha           TEXT    NOT NULL,
    hora            TEXT    NOT NULL,
    personas        INTEGER NOT NULL CHECK (personas BETWEEN 1 AND 20),
    estado          TEXT    NOT NULL DEFAULT 'CONFIRMADA'
                    CHECK (estado IN ('CONFIRMADA', 'CANCELADA')),
    creado_en       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS cierres_caja (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL UNIQUE,
    num_pedidos     INTEGER NOT NULL CHECK (num_pedidos >= 0),
    total_ventas    REAL    NOT NULL CHECK (total_ventas >= 0),
    creado_por      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    creado_en       TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_platos_categoria ON platos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_usuario ON pedidos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);
CREATE INDEX IF NOT EXISTS idx_reservas_fecha_hora ON reservas(fecha, hora);
