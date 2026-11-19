# Reglas compartidas de validacion y coherencia de datos (Modulo 2)
from datetime import date, datetime
import re
import db

DIAS = ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes')

# Excepcion controlada para mostrar errores de negocio en el formulario
class ReglaNegocio(ValueError):
    pass

# Convierte texto a entero positivo o devuelve None si no es valido
def entero(valor):
    texto = str(valor or '').strip()
    if not re.fullmatch(r'[0-9]{1,10}', texto):
        return None
    numero = int(texto)
    return numero if numero > 0 else None

# Devuelve fecha y hora actual del sistema
def ahora():
    return datetime.now()

# Devuelve la fecha actual
def hoy():
    return ahora().date()

# Convierte cadena YYYY-MM-DD a objeto date seguro
def fecha(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        texto = str(valor or '')
        if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', texto):
            return None
        return date.fromisoformat(texto)
    except ValueError:
        return None

# Obtiene el nombre del dia habil (Lunes a Viernes) a partir de una fecha
def dia(valor):
    f = fecha(valor)
    return DIAS[f.weekday()] if f and f.weekday() < 5 else ''

# Bloquea la fila del docente durante una transaccion de edicion
def bloquear_docente(id_docente):
    fila = db.query('SELECT * FROM docentes WHERE id_docente = %s FOR UPDATE', (id_docente,), one=True)
    if fila is None:
        raise ReglaNegocio('El docente ya no está registrado.')
    return fila

# Bloquea la fila del estudiante durante una transaccion de edicion
def bloquear_estudiante(id_estudiante):
    fila = db.query('SELECT * FROM estudiantes WHERE id_estudiante = %s FOR UPDATE', (id_estudiante,), one=True)
    if fila is None:
        raise ReglaNegocio('El estudiante ya no está registrado.')
    return fila

# Verifica que editar carrera o carga no afecte asesorias programadas del alumno
def validar_edicion_estudiante(actual, form, filas):
    pendientes = db.query(
        "SELECT f.fecha, f.id_bloque, f.id_carrera, f.id_materia FROM reservas_asesoria r "
        "JOIN franjas_asesoria f ON f.id_franja = r.id_franja "
        "WHERE r.id_estudiante = %s AND r.estado_cita = 'Programada' "
        "AND f.estado = 'Publicada' AND f.fecha >= %s FOR UPDATE",
        (actual['id_estudiante'], hoy()),
    )
    materias = {f['materia'] for f in filas}
    ocupados = {(f['dia'], f['bloque']) for f in filas}
    for cita in pendientes:
        if (cita['id_carrera'] != form['id_carrera'] or cita['id_materia'] not in materias
                or (dia(cita['fecha']), cita['id_bloque']) in ocupados):
            raise ReglaNegocio('El cambio afecta una asesoría programada. Conserva su carrera, materia y horario compatible antes de guardar.')

# Verifica coherencia de departamento y no traslape con franjas publicadas (RN-09)
def validar_edicion_docente(actual, form, filas):
    incompatibles = db.query(
        'SELECT tm.id_materia FROM tutor_materias tm JOIN materias m ON m.id_materia = tm.id_materia '
        'WHERE tm.id_docente = %s AND m.id_departamento <> %s FOR UPDATE',
        (actual['id_docente'], form['id_departamento']),
    )
    if incompatibles:
        raise ReglaNegocio('El departamento no coincide con su perfil de asesorías. Coordinación debe revisar las materias autorizadas antes de cambiarlo.')
    franjas = db.query(
        "SELECT fecha, id_bloque FROM franjas_asesoria WHERE id_docente = %s "
        "AND estado = 'Publicada' AND fecha >= %s FOR UPDATE", (actual['id_docente'], hoy()),
    )
    ocupados = {(f['dia'], f['bloque']) for f in filas}
    if any((dia(f['fecha']), f['id_bloque']) in ocupados for f in franjas):
        raise ReglaNegocio('Una clase coincide con una franja de asesoría publicada. Corrige el horario antes de guardar.')
