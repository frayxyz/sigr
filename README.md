# SIGR - Sistema Integral de Gestión de Restaurante

Aplicación web para gestionar **pedidos**, **reservas**, **administración de menús**, **control de caja** y **generación de reportes** de un restaurante.

- Lenguaje: Python 3.10 o superior
- Framework: Flask 3.1
- Base de datos: SQLite (archivo local, sin servidor externo)
- Pruebas: `unittest` (incluido en Python)
- Licencia: MIT (ver `LICENSE.txt`)

## Requisitos

- Python 3.10 o superior
- Git (para clonar el repositorio)

## Instalación y ejecución

```bash
git clone https://github.com/frayxyz/sigr.git
cd sigr
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
python run.py
```

La API queda disponible en `http://127.0.0.1:5000`. Compruebe que funciona abriendo `http://127.0.0.1:5000/api/salud`, que debe responder `{"estado": "ok"}`.

Para ejecutar las pruebas de integración:

```bash
python -m unittest discover -s tests -v
```

Consulte `docs/MANUAL_DESPLIEGUE.md` para la configuración en un servidor y `docs/ESQUEMA_BD.md` para el modelo de datos.

## Estructura del proyecto

```
sigr/
├── app/
│   ├── __init__.py     Fábrica de la aplicación y administrador inicial
│   ├── auth.py         Autenticación y gestión de usuarios
│   ├── menu.py         CRUD de categorías y platos
│   ├── pedidos.py      Registro y seguimiento de pedidos
│   ├── reservas.py     Reservas por fecha y hora
│   ├── caja.py         Cierre de caja y reportes de ventas
│   ├── seguridad.py    Sesiones y control de acceso por rol
│   ├── db.py           Conexión a SQLite
│   └── schema.sql      Esquema de la base de datos
├── tests/
│   ├── base.py                 Clase base y datos comunes de las pruebas
│   ├── test_autenticacion.py
│   ├── test_menu.py
│   ├── test_reservas.py
│   ├── test_pedidos.py
│   └── test_caja.py
├── docs/
│   ├── ESQUEMA_BD.md
│   └── MANUAL_DESPLIEGUE.md
├── run.py              Punto de entrada
├── requirements.txt
├── CHANGELOG.md
├── LICENSE.txt
└── README.md
```

## Roles

| Rol       | Puede                                                                                   |
|-----------|-----------------------------------------------------------------------------------------|
| CLIENTE   | Registrarse, consultar el menú, crear pedidos y reservas, ver y cancelar sus propios registros. |
| MESERO    | Todo lo anterior para cualquier cliente, cambiar el estado de los pedidos, ver todas las reservas. |
| ADMIN     | Todo lo anterior, administrar menú, usuarios, cierres de caja y reportes.               |

## Resumen de la API

Todas las respuestas son JSON. Las rutas que requieren sesión devuelven `401` si no hay sesión y `403` si el rol no tiene permiso.

### Autenticación

| Método | Ruta                   | Descripción                                      | Acceso   |
|--------|------------------------|--------------------------------------------------|----------|
| POST   | `/api/auth/registro`   | Registra un cliente (`nombre`, `email`, `password`) | Público  |
| POST   | `/api/auth/login`      | Inicia sesión (`email`, `password`)              | Público  |
| POST   | `/api/auth/logout`     | Cierra sesión                                    | Público  |
| GET    | `/api/auth/yo`         | Datos del usuario en sesión                      | Sesión   |
| GET    | `/api/usuarios`        | Lista usuarios                                   | ADMIN    |
| POST   | `/api/usuarios`        | Crea usuarios con rol `CLIENTE`, `MESERO` o `ADMIN` | ADMIN |

### Menú

| Método | Ruta                          | Descripción                       | Acceso |
|--------|-------------------------------|-----------------------------------|--------|
| GET    | `/api/categorias`             | Lista categorías                  | Público |
| POST   | `/api/categorias`             | Crea categoría                    | ADMIN  |
| PUT    | `/api/categorias/<id>`        | Actualiza categoría               | ADMIN  |
| DELETE | `/api/categorias/<id>`        | Elimina categoría sin platos      | ADMIN  |
| GET    | `/api/platos?categoria_id=`   | Lista platos (filtro opcional)    | Público |
| POST   | `/api/platos`                 | Crea plato                        | ADMIN  |
| PUT    | `/api/platos/<id>`            | Actualiza plato (precio, disponibilidad, etc.) | ADMIN |
| DELETE | `/api/platos/<id>`            | Elimina plato                     | ADMIN  |

### Pedidos

| Método | Ruta                             | Descripción                                                  | Acceso          |
|--------|----------------------------------|--------------------------------------------------------------|-----------------|
| POST   | `/api/pedidos`                   | Crea pedido: `{"items": [{"plato_id": 1, "cantidad": 2}]}`   | Sesión          |
| GET    | `/api/pedidos?estado=`           | Lista pedidos (el cliente solo ve los suyos)                 | Sesión          |
| GET    | `/api/pedidos/<id>`              | Detalle de un pedido con sus items                           | Sesión          |
| PATCH  | `/api/pedidos/<id>/estado`       | Cambia estado: `{"estado": "EN_PREPARACION"}`                | MESERO, ADMIN   |

Flujo de estados: `PENDIENTE → EN_PREPARACION → LISTO → ENTREGADO`. Un pedido puede cancelarse (`CANCELADO`) mientras no esté `LISTO` ni `ENTREGADO`. Las transiciones no permitidas responden `409`.

El seguimiento se hace consultando `GET /api/pedidos` o `GET /api/pedidos/<id>` (consulta periódica desde el cliente).

### Reservas

| Método | Ruta                            | Descripción                                              | Acceso |
|--------|---------------------------------|----------------------------------------------------------|--------|
| POST   | `/api/reservas`                 | Crea reserva: `{"fecha": "2026-11-20", "hora": "19:30", "personas": 4}` | Sesión |
| GET    | `/api/reservas?fecha=`          | Lista reservas (el cliente solo ve las suyas)            | Sesión |
| PATCH  | `/api/reservas/<id>/cancelar`   | Cancela una reserva                                      | Sesión |

Cada franja horaria admite un máximo de reservas confirmadas, configurable con `SIGR_MAX_RESERVAS_HORA` (por defecto 10).

### Caja y reportes

| Método | Ruta                          | Descripción                                                       | Acceso |
|--------|-------------------------------|-------------------------------------------------------------------|--------|
| POST   | `/api/caja/cierres`           | Cierra la caja de una fecha: `{"fecha": "2026-11-20"}`            | ADMIN  |
| GET    | `/api/caja/cierres`           | Historial de cierres                                              | ADMIN  |
| GET    | `/api/reportes/ventas`        | Ventas por día y platos más vendidos (`desde`, `hasta`)           | ADMIN  |

El cierre de caja se rechaza (`409`) si quedan pedidos abiertos de esa fecha o si la caja ya fue cerrada.

## Configuración por variables de entorno

| Variable                    | Por defecto                     | Descripción                                   |
|-----------------------------|---------------------------------|-----------------------------------------------|
| `SIGR_SECRET_KEY`           | `cambiar-en-produccion`         | Clave para firmar las cookies de sesión       |
| `SIGR_DATABASE`             | `instance/sigr.db`              | Ruta del archivo SQLite                       |
| `SIGR_ADMIN_EMAIL`          | `admin@sigr.local`              | Email del administrador inicial               |
| `SIGR_ADMIN_PASSWORD`       | `admin12345`                    | Contraseña del administrador inicial          |
| `SIGR_MAX_RESERVAS_HORA`    | `10`                            | Reservas máximas por franja horaria           |

**Importante:** cambie `SIGR_SECRET_KEY` y `SIGR_ADMIN_PASSWORD` antes de usar el sistema fuera de un entorno de pruebas.

## Documentación relacionada

- `CHANGELOG.md`: historial de cambios y versión de la línea base.
- `docs/ESQUEMA_BD.md`: tablas, campos y relaciones.
- `docs/MANUAL_DESPLIEGUE.md`: instalación, configuración y puesta en producción.
- `LICENSE.txt`: licencia MIT.
