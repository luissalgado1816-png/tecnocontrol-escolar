# TecnoControl Escolar

Aplicación de gestión de asesorías del Instituto Tecnológico de Zacatepec. Los cinco módulos del proyecto comparten los horarios de clases, las franjas publicadas y el historial de cada atención. La aplicación utiliza Flask, PyMySQL, MariaDB y Bootstrap local.

## Instalación en Windows

Utilizar Python 3.14, XAMPP con MariaDB 10.4.32 y una terminal **CMD**. Descargar o clonar el proyecto y abrir en VS Code la carpeta que contiene `app.py`. Los comandos siguientes se ejecutan desde esa carpeta. Las rutas de XAMPP corresponden a su instalación predeterminada.

1. Iniciar **MySQL** desde el panel de XAMPP. La aplicación utiliza `127.0.0.1`, puerto `3306`, con la cuenta local predeterminada de XAMPP.
2. Crear el esquema inicial con sus tablas, vistas y disparadores.

   ```bat
   "C:\xampp\mysql\bin\mysql.exe" -u root < database.sql
   ```

3. Cargar las retículas y los datos de demostración.

   ```bat
   "C:\xampp\mysql\bin\mysql.exe" -u root < semilladml.sql
   ```

4. Crear el entorno de Python del proyecto.

   ```bat
   python -m venv venv
   ```

5. Activar el entorno. En CMD aparece `(venv)` al inicio de la línea.

   ```bat
   venv\Scripts\activate.bat
   ```

6. Instalar las dependencias.

   ```bat
   python -m pip install -r requirements.txt
   ```

7. Iniciar la aplicación.

   ```bat
   python app.py
   ```

8. Abrir el sistema en el navegador. [TecnoControl Escolar en este equipo](http://127.0.0.1:5000)

**En las siguientes sesiones**, iniciar MySQL en XAMPP, abrir la carpeta del proyecto en CMD y activar el entorno si la terminal se acaba de abrir. Con `(venv)` activo, ejecutar **`python app.py`**. Para cerrar, detener Flask con **Ctrl+C** y luego pulsar **Stop** en MySQL.

## Actualización de una instalación existente

La migración incorpora la cadena de asesorías a una base que ya utiliza el esquema anterior del sistema.

1. Respaldar la base de datos y detener Flask con **Ctrl+C**. Mantener **MySQL** activo en XAMPP.
2. Actualizar los archivos del proyecto y ejecutar la migración desde la carpeta del repositorio en CMD.

   ```bat
   "C:\xampp\mysql\bin\mysql.exe" -h 127.0.0.1 -P 3306 -u root --default-character-set=utf8mb4 --database=tecnocontrol_escolar < actualizar_cadena_asesorias.sql
   ```

3. Iniciar Flask nuevamente desde el entorno virtual.

   ```bat
   venv\Scripts\python.exe app.py
   ```

La migración permite guardar la materia asesorada en cada cita. Las citas previas se consultan con la materia de su franja. Si la instalación utiliza otra base o credenciales propias, usar los valores de conexión configurados para Flask en `config.py`.

Para revertir la actualización, aplicar `revertir_cadena_asesorias.sql` con la misma conexión y recuperar el código anterior antes de iniciar Flask. La reversión conserva los registros de citas. La versión anterior muestra la materia de la franja al consultarlos.

## Uso de los archivos SQL

Los archivos SQL se ejecutan por separado desde un cliente de MariaDB, según la operación. Flask se conecta a la base cargada y envía consultas o cambios. MariaDB ejecuta los disparadores instalados al insertar o actualizar los registros correspondientes.

| Archivo | Cuándo ejecutarlo |
| --- | --- |
| `database.sql` | En una instalación nueva. Crea la base, las tablas, las vistas y los disparadores, incluidas las reglas de la cadena y de restablecimiento de citas. |
| `semilladml.sql` | Después de `database.sql` en la instalación inicial. Carga los catálogos y prepara los datos de demostración si la base está vacía de usuarios. |
| `actualizar_cadena_asesorias.sql` | Al añadir el soporte de la cadena a una instalación que ya cuenta con el esquema anterior. Incorpora la materia asesorada y actualiza las reglas que la validan. |
| `restablecer_disponibilidad.sql` | Como mantenimiento, para volver a instalar el disparador que permite restaurar citas suspendidas. Requiere el esquema actualizado. El `database.sql` actual y la migración de cadena ya incluyen ese disparador. |
| `revertir_cadena_asesorias.sql` | Al volver a la versión anterior a la cadena. Aplicarlo como parte de la reversión y recuperar también el código anterior. |
| `Consultas.sql` | Si está en la copia de trabajo, abrirlo en el cliente SQL y ejecutar las sentencias que correspondan a la comprobación que se quiera realizar. |

## Cuentas de la instalación nueva

| Perfil | Usuario | Contraseña de demostración |
| --- | --- | --- |
| Administrador escolar | `adminescolar0001` | `Admin2026*` |
| Coordinador de Tutorías | `coordinadortutoria0001` | `Coord2026*` |
| Tutor | `maestro0001` a `maestro0009` | `Tutor2026*` |
| Lucía Cruz Pineda · Sistemas · 1.er semestre | `26090101` | `Alumno2026*` |
| Mateo Vega Ríos · Sistemas · 3.er semestre | `25090102` | `Alumno2026*` |
| Elisa Lara Solís · Electromecánica · 3.er semestre | `25090103` | `Alumno2026*` |

Los tres estudiantes tienen una identidad ficticia. El periodo escolar del ejemplo es agosto–diciembre de 2026. El año de ingreso y el ciclo determinan el semestre. Las dos semanas de franjas se calculan al importar la semilla por primera vez. Para una demostración posterior, utilizar **Franjas** en Coordinación para publicar las fechas vigentes.

### Docentes de la demostración

| Usuario | Docente | Grado del escenario | Asignatura de referencia |
| --- | --- | --- | --- |
| `maestro0001` | Ángel Sandoval Jacobo | Ing. | ACF-0901 · Cálculo diferencial |
| `maestro0002` | Ma. Guadalupe Rojas Vilchis | Ing. | AED-1285 · Fundamentos de programación |
| `maestro0003` | Jesús Manzo Espín | Mtro. | ACF-0902 · Cálculo integral |
| `maestro0004` | Felipe Castañeda Martínez | Mtro. | AED-1286 · Programación orientada a objetos |
| `maestro0005` | Ana Delia Moreno Altamirano | Dr. | ACF-0904 · Cálculo vectorial |
| `maestro0006` | José Antonio Velázquez Santana | Dr. | AED-1026 · Estructura de datos |
| `maestro0007` | Mariana Ríos Beltrán | Dr. | EMC-1011 · Electricidad y magnetismo |
| `maestro0008` | Gabriel Luna Serrano | Dr. | EMJ-1021 · Mecánica de materiales |
| `maestro0009` | Elena Ortega Vidal | Dr. | EMC-1018 · Máquinas y equipos térmicos I |

Los tres departamentos del escenario son Ciencias Básicas, Sistemas y Computación y Metalmecánica. Las seis primeras asignaciones corresponden a los nombres proporcionados para el proyecto. Los otros tres docentes, los grados, las autorizaciones, los horarios y las citas son datos del escenario. Las claves y los semestres de las asignaturas corresponden a las retículas entregadas.

## Recorrido de demostración

1. Ingresar como **Lucía** y abrir **Reservar asesoría**. Seleccionar **Cálculo diferencial** y **Semana siguiente**. El lunes a las 15:00 aparecen dos tutores. Pulsar ese horario en el calendario para abrir **Franjas de asesoría**, elegir un tutor y pulsar **Reservar**.
2. Pulsar **Confirmar reserva** para apartar el lugar. Abrir la cita en el calendario y pulsar **Confirmar** para confirmar la asistencia. Para probar la cancelación, pulsar **Cancelar** antes del inicio. El contador libera un lugar.
3. Consultar el jueves de esa semana a las 10:00 para probar el cruce con clase. La reserva requiere aceptar expresamente el cruce. El martes a las 17:00 hay otra franja de Cálculo diferencial con un único lugar, ocupado por una reserva de demostración.
4. Ingresar como **Mateo**, seleccionar **Cálculo vectorial** como materia inscrita, elegir **Cálculo integral** como materia para asesoría y consultar **Semana siguiente**. El martes, Jesús Manzo Espín ofrece una franja de Integral a las 16:00 y Ana Delia Moreno Altamirano ofrece una franja de Vectorial a las 15:00 que cubre Integral por su grado y la cadena. Al reservar con Ana Delia, la cita aparece como **Cálculo integral** en **Mi historial** y ocupa un lugar de su franja de Vectorial. En ese historial también se puede consultar el acuerdo de Estructura de datos y su seguimiento con lugar apartado.
5. Ingresar como **maestro0006**. En **Mis franjas**, consultar el miércoles de la semana siguiente y pulsar **Ver estudiantes** en la franja de las 16:00. Abrir **Registrar atención**. **Asistió** habilita la decisión. **Cerrado** admite anotaciones opcionales. **Agendar seguimiento** muestra las franjas posteriores del mismo tutor y materia con cupo y horario compatibles. **No asistió** permite guardar únicamente la inasistencia.
6. En **Administrar disponibilidad**, seleccionar un día o un rango. Revisar las franjas y los alumnos afectados antes de **Confirmar suspensión**. Los alumnos pueden consultar la cancelación en sus calendarios.
7. Ingresar como **Coordinación** para habilitar tutores, autorizar materias, publicar bloques o ajustar el cupo. El reporte abre el detalle de cada acuerdo en una ventana de consulta. En el reporte del docente, **En seguimiento** abre la atención guardada y permite regresar al mismo periodo consultado.

## Arquitectura y conexión a la base de datos

| Capa | Tecnología y función | Ubicación en el proyecto |
| --- | --- | --- |
| Presentación | Jinja genera HTML. Bootstrap y JavaScript controlan la presentación y la interacción de los calendarios y las ventanas. | `templates/` y `static/` |
| Aplicación | Flask recibe las peticiones HTTP. Las rutas y las reglas en Python verifican el perfil, la elegibilidad, el horario y el cupo. | `app.py`, `auth.py`, `modulos/` y `reglas.py` |
| Datos | PyMySQL conecta la aplicación con MariaDB, donde se guardan estudiantes, franjas, citas y acuerdos. | `db.py`, `config.py` y `database.sql` |

Al confirmar una reserva, el navegador envía la solicitud a `modulos/estudiante.py`. La ruta aplica las validaciones de `reglas.py` y guarda la reserva en MariaDB mediante `db.py`. Flask redirige a la pantalla de reserva, que muestra la cita y el cupo actualizado.

La función `get_db()` establece la conexión en la línea 28 de `db.py` mediante `pymysql.connect(**params)`. Los parámetros de conexión se configuran en `config.py`.

## Trazabilidad de los módulos

| Información | Registro de origen | Dónde se utiliza |
| --- | --- | --- |
| Semestre y materias inscritas | `periodos_escolares`, `estudiantes`, `carrera_materia.semestre` y `horario_estudiante` | Ficha de estudiante, calendario y selector de materia |
| Carga del docente | Ficha de docente, `horario_docente`, departamento, grado y `materias.posicion` | Perfil de asesorías, materias autorizables y celdas de clase protegidas |
| Autorización y alcance de la franja | Coordinación guarda `docentes.habilitado_tutor` y autoriza materias de la carga vigente en `tutor_materias`. La vista `v_materias_asesorables_franja` calcula qué materias cubre cada franja a partir de su carrera y materia publicada, la cadena y el grado del tutor. | Perfil del tutor, publicación y búsqueda de franjas |
| Horario y cupo | `franjas_asesoria`, `bloques_horarios` y `v_franjas_cupo` | Los calendarios de Coordinación, tutor y alumno muestran la misma franja |
| Materias vinculadas a la cita | `reservas_asesoria.id_materia_inscrita` identifica la materia que cursa el alumno. `reservas_asesoria.id_materia_asesorada` registra la materia que eligió para la cita. `franjas_asesoria.id_materia` identifica la materia con la que se publicó la franja. | El historial, el seguimiento y el bloqueo por materia usan la materia asesorada. El cupo de la franja se comparte entre las materias que cubre. |
| Apartado, confirmación y excepción de clase | `reservas_asesoria` vincula al alumno con la franja y registra la confirmación y la aceptación del cruce. | Contador de lugares, calendario e historial |
| Suspensión de un día o rango | `bloqueos_asesoria` y motivo de cancelación en las franjas y reservas afectadas | Disponibilidad del docente y cancelación visible al alumno |
| Atención y seguimiento | La cita conserva el resultado y las anotaciones opcionales de cierre. `acuerdos.id_reserva` enlaza con la cita atendida. `reservas_asesoria.id_reserva_origen` enlaza la siguiente cita | Consulta del acuerdo, historial por recorrido y reportes por periodo |

Al guardar Investigación o Sabático en la ficha de docente, se vacía el horario vigente y se cancelan las asesorías programadas de ese tutor. Al reactivarlo se puede asignar un horario nuevo.

El catálogo contiene 46 asignaturas con clave del plan ISIC-2010-224 y 45 del plan IEME-2010-210. Las materias compartidas conservan una sola clave en `materias` y su semestre particular en `carrera_materia`. Las cadenas del escenario son Cálculo diferencial → integral → vectorial, Fundamentos de programación → Programación orientada a objetos → Estructura de datos y Termodinámica → Transferencia de calor → Máquinas y equipos térmicos I. Las demás materias se tratan como independientes.

## Evolución del proyecto

Se conservaron los puntos de entrada `app.py`, `auth.py`, `db.py` y los cuatro módulos existentes en `modulos/`. La mejora amplió los formularios y la base de datos de la versión anterior. Los calendarios reutilizan una cuadrícula común en `static/js/calendario.js`. Las decisiones sobre cupos, horarios y elegibilidad se comprueban en el servidor al guardar.
