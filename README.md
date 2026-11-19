# TecnoControl Escolar

Sistema web académico de asesorías del Instituto Tecnológico de Zacatepec.
Python, Flask, PyMySQL, MariaDB y Jinja2 con Bootstrap local.

## Estado de esta entrega

| Módulo | Estado |
| --- | --- |
| 1 · Acceso, sesiones y restablecimiento | Conservado del proyecto recibido |
| 2 · Administración de estudiantes y docentes | Implementado |
| 3 · Coordinación de Tutorías | Pendiente de incorporar |
| 4 · Reservas e historial del estudiante | Pendiente de incorporar |
| 5 · Atención y seguimiento del tutor | Pendiente de incorporar |

Los estados indican código implementado. La evidencia de comprobación y sus
límites se detallan en docs/VALIDACION_MODULO_2.md.
Se conserva modulos/_init_.py tal como lo entregó el estudiante.

## Requisitos

- Python 3.14 en el equipo de demostración.
- MariaDB 10.4.32 de XAMPP, con MySQL iniciado desde su panel.
- Un navegador Firefox o Microsoft Edge.
- Dependencias de requirements.txt: Flask 3.1.3 y PyMySQL 1.2.4, con sus versiones fijadas.
- El puerto de MariaDB por defecto es 3306; Flask usa 127.0.0.1:5000.

Bootstrap se incluye en static/vendor/bootstrap. No hay descargas de fuentes,
JavaScript o CSS desde CDN durante el uso de la aplicación. Apache no es necesario
para servir Flask; solo se usa si se elige phpMyAdmin como herramienta SQL.

## Instalación nueva para la docente

1. Descarga el repositorio completo y descomprímelo. Abre la carpeta que contiene app.py.
2. Instala Python y XAMPP con MariaDB, si aún no están disponibles.
3. Inicia MySQL en XAMPP. Con Database Client de VS Code o phpMyAdmin, ejecuta
   database.sql y después semilladml.sql, completos y en ese orden.
   database.sql elimina y vuelve a crear tecnocontrol_escolar: esta instrucción
   corresponde únicamente a una instalación nueva o a una base de demostración descartable.
4. Abre CMD en la carpeta del proyecto y prepara el entorno:

```bat
python -m venv venv
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

5. La configuración predeterminada conecta a 127.0.0.1:3306, usuario root, sin
   contraseña, base tecnocontrol_escolar. Si tu instalación es distinta, configura
   DB_HOST, DB_PORT, DB_USER, DB_PASSWORD y DB_NAME como variables de entorno antes
   de iniciar. DB_SOCKET es opcional y normalmente no se usa en Windows.
6. Para conservar la firma de sesión entre reinicios, configura una SECRET_KEY propia
   y estable en ese equipo. La aplicación genera una si no se define.
7. Inicia Flask:

```bat
python app.py
```

8. Abre http://127.0.0.1:5000. Cierra la aplicación desde la terminal con Ctrl+C.
   La depuración está desactivada por defecto. No hace falta modificar el código
   para cambiar los parámetros locales de conexión.

## Actualizar el proyecto que Luis ya tiene funcionando

Conserva tu venv, tu base y tus datos. Aplica los paquetes de los módulos en orden
2, 3, 4 y 5, copiando las rutas de la carpeta archivos/ a la raíz del repositorio.
Cada paquete explica qué agregar, reemplazar y conservar. Guarda una etapa,
comprueba su funcionamiento y registra su commit con GitHub Desktop antes de la
siguiente. Estos módulos utilizan el esquema existente: no es necesario volver
a ejecutar database.sql ni recargar semilladml.sql para incorporar la actualización.
Reinicia Flask después de actualizar Python y recarga el navegador con Ctrl+F5
después de actualizar CSS o JavaScript.

## Cuentas de demostración de semilladml.sql

| Perfil/persona | Usuario | Contraseña de la semilla |
| --- | --- | --- |
| Administrador Escolar | adminescolar0001 | Admin2026* |
| Coordinación de Tutorías | coordinadortutoria0001 | Coord2026* |
| Tutor Daniel Vargas León | maestro0001 | Tutor2026* |
| Tutor Julián Vega Soto | maestro0002 | Tutor2026* |
| Tutora Sara León Ruiz | maestro0003 | Tutor2026* |
| David Santos Cruz, Investigación y no habilitado | maestro0004 | Docente2026* |
| Luis Ivan Salgado Rivera | 22090748 | 2209074812345 |
| Renata Cruz Luna | 26090022 | 2609002212345 |
| Miguel Vera Díaz | 26090023 | 2609002312345 |

Estas son cuentas de prueba. Si restableciste una contraseña en tu base local,
usa su valor actual. Las contraseñas del SQL son hashes scrypt. Las altas nuevas
usan la contraseña definitiva que captura Administración, no la fórmula de la
cuenta de ejemplo de Luis.

## Reglas y recorrido de referencia

Administración registra fichas y clases. Coordinación habilita a docentes activos,
autoriza materias de su departamento y publica franjas por carrera y fecha.
El estudiante reserva su primera cita. El tutor registra la atención y un acuerdo
individual, con cierre o seguimiento para el mismo estudiante y tutor.

Se mantienen semestre calculado en solo lectura; prefijos C/T; correo con dominio
@zacatepec.tecnm.mx; bloques de una hora; cupo fijo de 10; materias de la carga
vigente; horarios compatibles y consultas limitadas al perfil.

La recuperación local conserva usuario o número de control y correo registrados,
y habilita el cambio de contraseña en esa misma pantalla, sin envío de correos,
SMS ni autorización administrativa.

database.sql define 16 tablas, dos vistas y cinco triggers.
La semilla incluye nueve cuentas, cuatro docentes, tres estudiantes, 37 clases
de estudiantes, dos clases de docente, tres franjas y dos reservas iniciales.
No incluye todavía la reserva ni el acuerdo de Luis.

Caso del recorrido: Luis 22090748, Ingeniería de Software con Daniel DOC-104;
viernes 20/11/2026 de 11:00–12:00 y seguimiento martes 24/11/2026 de 12:00–13:00.
Las fechas de la oferta se comparan con el reloj local del equipo. Si se ejecuta
después de esas fechas, Coordinación puede publicar otras franjas futuras válidas.
No se agregan automáticamente citas para simular el recorrido.

## Pruebas aisladas

Con el venv activo y desde la raíz:

```bat
python -m unittest discover -s tests -t . -v
```

La suite crea archivos SQLite temporales, usa copias de los catálogos y cuentas
de la semilla y sustituye la conexión dentro de las pruebas. No escribe en XAMPP,
no restablece cuentas reales y no borra periodos de tu base. Comprueba recorridos
de Flask y reglas de aplicación. No sustituye la validación de bloqueos y triggers
en MariaDB real ni las pruebas de navegador. El reloj de las pruebas está fijado
al 19/11/2026, sin cambiar el reloj de la aplicación.

## Estructura del código

- app.py, auth.py, db.py y config.py: base compartida y módulo 1 conservado.
- modulos/: rutas por perfil; los comentarios identifican RF y reglas relevantes.
- reglas.py: comprobaciones compartidas y consultas de coherencia.
- templates/: vistas Jinja2; static/: estilos institucionales y scripts locales.
- tests/: comprobaciones aisladas; docs/: validación y trazabilidad por etapa.
- database.sql y semilladml.sql: esquema y datos reproducibles de referencia.
