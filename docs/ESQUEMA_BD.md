# Esquema de la base de datos

Motor: SQLite 3. El esquema completo está en `app/schema.sql` y se aplica automáticamente al iniciar la aplicación (`CREATE TABLE IF NOT EXISTS`).

## Diagrama de relaciones

```
usuarios 1 ──< pedidos 1 ──< pedido_items >── 1 platos >── 1 categorias
    │                                                  
    ├──< reservas
    │
    └──< cierres_caja (creado_por)
```

## Tablas

### usuarios

| Campo         | Tipo    | Restricciones                                       |
|---------------|---------|-----------------------------------------------------|
| id            | INTEGER | PK, autoincremental                                 |
| nombre        | TEXT    | NOT NULL                                            |
| email         | TEXT    | NOT NULL, UNIQUE                                    |
| password_hash | TEXT    | NOT NULL (hash con werkzeug, nunca la clave en claro) |
| rol           | TEXT    | NOT NULL, CHECK en `CLIENTE`, `MESERO`, `ADMIN`     |
| activo        | INTEGER | NOT NULL, por defecto 1, CHECK en 0 o 1             |
| creado_en     | TEXT    | NOT NULL, fecha y hora local                        |

### categorias

| Campo       | Tipo    | Restricciones          |
|-------------|---------|------------------------|
| id          | INTEGER | PK                     |
| nombre      | TEXT    | NOT NULL, UNIQUE       |
| descripcion | TEXT    |                        |

### platos

| Campo        | Tipo    | Restricciones                                      |
|--------------|---------|----------------------------------------------------|
| id           | INTEGER | PK                                                 |
| categoria_id | INTEGER | NOT NULL, FK a `categorias.id`, ON DELETE RESTRICT |
| nombre       | TEXT    | NOT NULL                                           |
| descripcion  | TEXT    |                                                    |
| precio       | REAL    | NOT NULL, CHECK `precio >= 0`                      |
| disponible   | INTEGER | NOT NULL, por defecto 1, CHECK en 0 o 1            |

### pedidos

| Campo          | Tipo    | Restricciones                                                                  |
|----------------|---------|--------------------------------------------------------------------------------|
| id             | INTEGER | PK                                                                             |
| usuario_id     | INTEGER | NOT NULL, FK a `usuarios.id`, ON DELETE RESTRICT                               |
| estado         | TEXT    | NOT NULL, por defecto `PENDIENTE`, CHECK en los cinco estados                  |
| total          | REAL    | NOT NULL, CHECK `total >= 0`                                                   |
| creado_en      | TEXT    | NOT NULL                                                                       |
| actualizado_en | TEXT    | NOT NULL                                                                       |

### pedido_items

Guarda una copia del nombre y precio del plato en el momento de la venta.

| Campo           | Tipo    | Restricciones                                              |
|-----------------|---------|------------------------------------------------------------|
| id              | INTEGER | PK                                                         |
| pedido_id       | INTEGER | NOT NULL, FK a `pedidos.id`, ON DELETE CASCADE             |
| plato_id        | INTEGER | FK a `platos.id`, ON DELETE SET NULL                       |
| nombre_plato    | TEXT    | NOT NULL (copia del nombre)                                |
| precio_unitario | REAL    | NOT NULL (copia del precio)                                |
| cantidad        | INTEGER | NOT NULL, CHECK `cantidad > 0`                             |
| subtotal        | REAL    | NOT NULL, CHECK `subtotal >= 0`                            |

### reservas

| Campo      | Tipo    | Restricciones                                             |
|------------|---------|-----------------------------------------------------------|
| id         | INTEGER | PK                                                        |
| usuario_id | INTEGER | NOT NULL, FK a `usuarios.id`                              |
| fecha      | TEXT    | NOT NULL, formato `AAAA-MM-DD`                            |
| hora       | TEXT    | NOT NULL, formato `HH:MM`                                 |
| personas   | INTEGER | NOT NULL, CHECK entre 1 y 20                              |
| estado     | TEXT    | NOT NULL, por defecto `CONFIRMADA`, CHECK en `CONFIRMADA`, `CANCELADA` |
| creado_en  | TEXT    | NOT NULL                                                  |

### cierres_caja

| Campo        | Tipo    | Restricciones                                       |
|--------------|---------|-----------------------------------------------------|
| id           | INTEGER | PK                                                  |
| fecha        | TEXT    | NOT NULL, UNIQUE (una caja cerrada por día)         |
| num_pedidos  | INTEGER | NOT NULL, CHECK `>= 0`                              |
| total_ventas | REAL    | NOT NULL, CHECK `>= 0`                              |
| creado_por   | INTEGER | NOT NULL, FK a `usuarios.id`                        |
| creado_en    | TEXT    | NOT NULL                                            |

## Índices

| Índice                    | Tabla     | Columnas        | Motivo                                 |
|---------------------------|-----------|-----------------|----------------------------------------|
| idx_platos_categoria      | platos    | categoria_id    | Filtrar el menú por categoría          |
| idx_pedidos_usuario       | pedidos   | usuario_id      | Historial de pedidos por cliente       |
| idx_pedidos_estado        | pedidos   | estado          | Consulta de pedidos abiertos           |
| idx_reservas_fecha_hora   | reservas  | fecha, hora     | Control de disponibilidad por franja   |

## Reglas de integridad

- Un pedido no puede quedar sin usuario ni sin items con cantidad positiva.
- Los precios se copian al pedido, por lo que un cambio o borrado de plato no altera pedidos anteriores.
- Solo puede existir un cierre de caja por fecha.
