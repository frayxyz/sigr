# Manual de despliegue - SIGR

Este manual describe cómo instalar, configurar y poner en marcha el SIGR en un equipo Windows o Linux.

## 1. Requisitos

| Componente | Versión mínima | Comprobación              |
|------------|----------------|---------------------------|
| Python     | 3.10           | `python --version`        |
| pip        | 23             | `python -m pip --version` |
| Git        | 2.30           | `git --version`           |

## 2. Obtener el código

```bash
git clone https://github.com/frayxyz/sigr.git
cd sigr
git checkout main
```

## 3. Crear el entorno virtual e instalar dependencias

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Configurar variables de entorno

Antes de iniciar, defina las variables siguientes. Ejemplo en PowerShell:

```powershell
$env:SIGR_SECRET_KEY = "una-clave-larga-y-aleatoria"
$env:SIGR_ADMIN_EMAIL = "admin@restaurante.com"
$env:SIGR_ADMIN_PASSWORD = "una-contraseña-segura"
$env:SIGR_DATABASE = "D:\sigr-datos\sigr.db"
$env:SIGR_MAX_RESERVAS_HORA = "10"
```

Ejemplo en Linux / macOS:

```bash
export SIGR_SECRET_KEY="una-clave-larga-y-aleatoria"
export SIGR_ADMIN_EMAIL="admin@restaurante.com"
export SIGR_ADMIN_PASSWORD="una-contraseña-segura"
export SIGR_DATABASE="/var/lib/sigr/sigr.db"
```

| Variable                  | Obligatoria en producción | Descripción                              |
|---------------------------|---------------------------|------------------------------------------|
| `SIGR_SECRET_KEY`         | Sí                        | Firma las cookies de sesión              |
| `SIGR_ADMIN_PASSWORD`     | Sí                        | Contraseña del administrador inicial     |
| `SIGR_ADMIN_EMAIL`        | No                        | Email del administrador inicial          |
| `SIGR_DATABASE`           | No                        | Ruta del archivo SQLite                  |
| `SIGR_MAX_RESERVAS_HORA`  | No                        | Reservas máximas por franja horaria      |

El administrador inicial se crea solo la primera vez que se inicia la aplicación con una base de datos sin administradores. Los cambios posteriores de `SIGR_ADMIN_PASSWORD` no modifican la cuenta existente.

## 5. Verificar la instalación

```bash
python -m unittest discover -s tests -v
```

Todas las pruebas deben terminar con `OK`.

## 6. Iniciar el servicio

Desarrollo local:

```bash
python run.py
```

Comprobación:

```bash
curl http://127.0.0.1:5000/api/salud
```

Respuesta esperada: `{"estado": "ok"}`.

## 7. Puesta en producción

`run.py` usa el servidor de desarrollo de Flask. Para un entorno de producción use un servidor WSGI como Waitress (Windows) o Gunicorn (Linux):

```bash
pip install waitress
waitress-serve --call --host=0.0.0.0 --port=5000 app:create_app
```

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 "app:create_app()"
```

Recomendaciones:
- Coloque el servicio detrás de un proxy inverso (Nginx o IIS) con HTTPS.
- Establezca `SESSION_COOKIE_SECURE=True` cuando el sitio se sirva por HTTPS (requiere ajustar `app/__init__.py`).
- Haga copias de seguridad periódicas del archivo SQLite.
- Ejecute el servicio con un usuario del sistema sin privilegios de administrador.

## 8. Copias de seguridad y restauración

La base de datos es un único archivo. Con el servicio detenido:

```bash
copy sigr.db sigr_respaldo_AAAAMMDD.db     # Windows
cp sigr.db sigr_respaldo_$(date +%Y%m%d).db # Linux
```

Para restaurar, detenga el servicio y reemplace el archivo `sigr.db` por la copia.

## 9. Actualización de versión

```bash
git fetch origin
git checkout <etiqueta-o-commit>
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Haga siempre una copia de seguridad de la base de datos antes de actualizar. El esquema se crea con `IF NOT EXISTS`, pero los cambios estructurales deben revisarse en `CHANGELOG.md`.

## 10. Solución de problemas

| Síntoma                                      | Causa probable                                   | Solución                                                  |
|----------------------------------------------|--------------------------------------------------|-----------------------------------------------------------|
| `ModuleNotFoundError: flask`                 | Entorno virtual no activado                      | Active `.venv` y ejecute `pip install -r requirements.txt` |
| `401 Debe iniciar sesión`                    | Falta la cookie de sesión                        | Inicie sesión con `POST /api/auth/login`                  |
| `403 No tiene permisos`                      | El rol no permite la operación                   | Use una cuenta con el rol adecuado                        |
| `409` al cerrar caja                         | Hay pedidos abiertos o la caja ya estaba cerrada | Entregue o cancele los pedidos, o revise el historial     |
| `sqlite3.OperationalError: unable to open`   | La carpeta de `SIGR_DATABASE` no existe o no tiene permisos | Cree la carpeta y asigne permisos de escritura |
