# TecnoControl Escolar

Proyecto académico de un sistema web para la gestión de asesorías escolares del Instituto Tecnológico de Zacatepec. Utiliza Python, Flask, PyMySQL y MariaDB, con plantillas Jinja2 y Bootstrap incluido en el proyecto.

## Estado actual

| Módulo | Contenido | Estado |
| --- | --- | --- |
| 1 | Inicio y cierre de sesión, acceso por perfil y restablecimiento de contraseña | Implementado |
| 2 | Administración de estudiantes y docentes, fichas y horarios base | Implementado |
| 3 | Coordinación de Tutorías: habilitación, perfiles, franjas, historial y reporte general | Integrado; pendiente de comprobación funcional con MariaDB en el equipo de demostración |
| 4 | Reservas e historial del estudiante | Implementado; pendiente de comprobación funcional con MariaDB en el equipo de demostración |
| 5 | Atención, acuerdos, seguimiento y reporte del tutor | Pendiente de incorporar |

Esta versión contiene los módulos 1, 2, 3 y 4. El estudiante dispone de oferta de asesorías, confirmación de reserva y consulta de su historial. Las funciones de atención, registro de acuerdos, seguimiento y reporte del tutor quedan pendientes del módulo 5.

## Requisitos

- Python 3.14.
- MariaDB 10.4.32, incluido en XAMPP.
- Un navegador Firefox o Microsoft Edge.
- Dependencias indicadas en `requirements.txt`, entre ellas Flask 3.1.3 y PyMySQL 1.2.4.
- Puerto local 3306 para MariaDB y puerto 5000 para la aplicación Flask.

Bootstrap está incluido en `static/vendor/bootstrap/`; los estilos y scripts se sirven desde el propio proyecto. Flask sirve la aplicación web. Apache solo es necesario si se utiliza phpMyAdmin para administrar la base de datos.

## Instalación en Windows

### 1. Preparar el proyecto

Descarga el repositorio y descomprímelo. Abre en VS Code la carpeta que contiene `app.py`, `requirements.txt` y los scripts SQL.

### 2. Crear y cargar la base de datos

Inicia MySQL desde el panel de XAMPP. En Database Client de VS Code o en phpMyAdmin, ejecuta los scripts completos en este orden:

1. `database.sql`: crea la base `tecnocontrol_escolar`, las 16 tablas, las dos vistas y los cinco triggers.
2. `semilladml.sql`: carga los catálogos y los datos de demostración.

**Esta carga corresponde a una instalación nueva.** `database.sql` elimina y vuelve a crear la base de datos. Si la aplicación ya está instalada, conserva la base existente al incorporar los módulos siguientes; estas actualizaciones utilizan el mismo esquema.

### 3. Preparar el entorno de Python

Abre una terminal CMD en la carpeta principal del proyecto y ejecuta:

```bat
python -m venv venv
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

### 4. Revisar la conexión

La configuración de `config.py` utiliza estos valores predeterminados:

| Variable de entorno | Valor predeterminado | Uso |
| --- | --- | --- |
| `DB_HOST` | `127.0.0.1` | Dirección del servidor MariaDB |
| `DB_PORT` | `3306` | Puerto de MariaDB |
| `DB_USER` | `root` | Usuario de conexión |
| `DB_PASSWORD` | Vacío | Contraseña de conexión |
| `DB_NAME` | `tecnocontrol_escolar` | Base de datos de la aplicación |

Si la instalación de MariaDB tiene otros datos de acceso, define las variables correspondientes en la terminal antes de iniciar Flask. Por ejemplo, si el usuario de MariaDB tiene contraseña:

```bat
set DB_PASSWORD=tu_contrasena_local
```

También se puede definir `SECRET_KEY` con un valor propio y estable para conservar la firma de las sesiones entre reinicios. Si no se define, la aplicación genera una clave al iniciarse. `DB_SOCKET` es opcional para instalaciones que utilicen un socket local.

### 5. Iniciar la aplicación

Con el entorno virtual activo y MariaDB en ejecución:

```bat
python app.py
```

Abre [http://127.0.0.1:5000](http://127.0.0.1:5000) en el navegador. Para detener Flask, presiona `Ctrl+C` en su terminal.

En aperturas posteriores basta con iniciar MariaDB, abrir CMD en la carpeta del proyecto, activar el entorno y ejecutar la aplicación:

```bat
venv\Scripts\activate.bat
python app.py
```

## Cuentas de demostración

Estas cuentas se crean al ejecutar `semilladml.sql` en una instalación nueva:

| Perfil o persona | Usuario | Contraseña inicial de demostración |
| --- | --- | --- |
| Administrador Escolar | `adminescolar0001` | `Admin2026*` |
| Coordinación de Tutorías | `coordinadortutoria0001` | `Coord2026*` |
| Tutor Daniel Vargas León | `maestro0001` | `Tutor2026*` |
| Tutor Julián Vega Soto | `maestro0002` | `Tutor2026*` |
| Tutora Sara León Ruiz | `maestro0003` | `Tutor2026*` |
| David Santos Cruz, no habilitado como tutor | `maestro0004` | `Docente2026*` |
| Luis Ivan Salgado Rivera | `22090748` | `2209074812345` |
| Renata Cruz Luna | `26090022` | `2609002212345` |
| Miguel Vera Díaz | `26090023` | `2609002312345` |

David tiene estado laboral Investigación y su cuenta está inactiva. Los demás usuarios de la semilla están activos. El estudiante puede acceder a las funciones del módulo 4. Los tutores pueden iniciar sesión; sus funciones de atención y reporte quedan pendientes de incorporar el módulo 5.

Si una contraseña ya se cambió en la base local, debe utilizarse su valor actual. Las contraseñas se almacenan como hashes scrypt. Al registrar personas nuevas, Administración captura una contraseña definitiva y su confirmación.

## Funciones disponibles por perfil

- **Acceso:** inicio y cierre de sesión, navegación según el perfil y restablecimiento de contraseña mediante el usuario o número de control y el correo institucional registrado, en la misma pantalla.
- **Administración Escolar:** registro, consulta y edición de estudiantes y docentes, sus datos de acceso y sus horarios base.
- **Coordinación de Tutorías:** consulta de docentes, habilitación de tutores activos, autorización de materias de su departamento, publicación de franjas, consulta del historial por número de control y reporte general por fechas, carrera y tutor.
- **Estudiante:** selección de materias de su carga vigente, consulta de franjas compatibles, visualización de lugares disponibles y franjas sin cupo, confirmación de una reserva inicial y consulta de su propio historial de citas, acuerdos y seguimientos registrados.

El código del módulo 3 contempla cupo fijo de 10 lugares, bloques de una hora, materias autorizadas para el tutor y la carrera, fechas de lunes a viernes y horarios sin cruces con clases ni con otras franjas del tutor. Las escrituras relacionadas se agrupan en transacciones con confirmación o reversión de cambios.

El módulo 4 consulta la oferta para estudiantes inscritos, según su carrera y las materias de su carga vigente. Excluye horarios incompatibles con sus clases o con otras reservas y permite reservar con tutores habilitados y activos. Las franjas sin lugares se muestran como **Sin cupo**, con la acción de reserva deshabilitada.

Al confirmar, el sistema vuelve a validar la disponibilidad, el cupo y la elegibilidad del estudiante. Impide duplicar una reserva del mismo estudiante en la misma franja. Si la operación es válida, guarda la cita con estado **Programada** y muestra **Mi historial**; si la disponibilidad cambió, presenta un aviso y devuelve a la oferta. La identidad del estudiante se obtiene de su sesión autenticada.

La consulta del historial puede mostrar acuerdos y citas de seguimiento existentes en la base de datos. El registro de la atención y la creación de acuerdos y seguimientos corresponden al módulo 5.

## Base de datos y datos de demostración

`database.sql` define 16 tablas InnoDB, dos vistas calculadas y cinco triggers, con codificación `utf8mb4` y cotejamiento `utf8mb4_unicode_ci`.

La semilla contiene nueve cuentas, cuatro docentes, tres estudiantes, 37 registros de horario de estudiantes, dos de horario docente, tres franjas y dos reservas iniciales. No contiene acuerdos ni reservas para el estudiante 22090748.

Las franjas de demostración están fechadas el 20, 24 y 25 de noviembre de 2026. La disponibilidad se calcula con la fecha y hora locales del equipo; para una demostración posterior se pueden publicar otras franjas futuras válidas desde Coordinación.

Los historiales y reportes consultan los registros existentes en la base de datos. La información ilustrativa de los wireframes no se carga automáticamente como datos.

## Archivos principales

| Ruta | Función |
| --- | --- |
| `app.py` | Configuración de Flask, registro de módulos, navegación, protección de formularios y manejo de errores |
| `auth.py` | Inicio y cierre de sesión, control de perfiles y restablecimiento de contraseña |
| `config.py` | Parámetros de conexión y configuración de sesiones |
| `db.py` | Conexiones, consultas parametrizadas y transacciones |
| `reglas.py` | Validaciones compartidas, disponibilidad, elegibilidad y cupo de reservas, y consultas de historial |
| `modulos/admin.py` | Gestión de estudiantes y docentes |
| `modulos/coordinacion.py` | Funciones de Coordinación de Tutorías |
| `modulos/estudiante.py` | Oferta de asesorías, confirmación de reservas e historial del estudiante |
| `modulos/tutor.py` | Rutas iniciales del tutor, pendientes del módulo 5 |
| `templates/` | Plantillas HTML de las pantallas |
| `templates/estudiante/` | Oferta de franjas, confirmación de reserva e historial del estudiante |
| `static/` | Estilos institucionales, JavaScript y Bootstrap local |
| `database.sql` | Estructura reproducible de la base de datos |
| `semilladml.sql` | Catálogos y datos de demostración |
| `requirements.txt` | Dependencias de Python |

