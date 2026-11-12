# Changelog

Todas las modificaciones relevantes del proyecto SIGR se documentan en este archivo.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado es [SemVer](https://semver.org/lang/es/).

## [1.0.0] - 2026-11-11 - Línea base inicial

Primera versión estable del código fuente. Esta es la línea base sobre la que se controlarán los cambios futuros.

### Añadido

- **Autenticación de usuarios:** registro de clientes, inicio y cierre de sesión por cookie, y control de acceso por rol (CLIENTE, MESERO, ADMIN).
- **Gestión de usuarios (ADMIN):** listado y creación de usuarios con cualquier rol.
- **Menú digital:** CRUD de categorías y platos, con control de disponibilidad y precio.
- **Pedidos:** creación con cálculo automático del total, seguimiento por estado y flujo controlado de transiciones (`PENDIENTE`, `EN_PREPARACION`, `LISTO`, `ENTREGADO`, `CANCELADO`).
- **Reservas:** registro por fecha y hora, control de disponibilidad por franja, validación de fechas pasadas y cancelación.
- **Cierre de caja:** cierre diario que impide dejar pedidos abiertos y evita cierres duplicados.
- **Reportes:** ventas por día y ranking de platos vendidos en un rango de fechas.
- **Documentación técnica:** `README.md`, `CHANGELOG.md`, `LICENSE.txt` (MIT), esquema de base de datos y manual de despliegue.
- **Pruebas de integración:** 25 casos con `unittest` que cubren autenticación, menú, pedidos, reservas, caja y reportes.

### Notas de la línea base

- Todos los módulos iniciales compilan y sus pruebas se ejecutan sin errores.
- Las funcionalidades críticas (login, pedidos, reservas, cierre de caja) están cubiertas por pruebas de integración.
- El seguimiento de pedidos se realiza por consulta de la API; no incluye notificaciones en tiempo real por WebSocket.
- La interfaz es una API JSON. No incluye vistas HTML.
