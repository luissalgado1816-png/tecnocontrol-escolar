# Reglas compartidas de validacion y coherencia de datos (Modulos 2, 3, 4 y 5)
from datetime import date, datetime, timedelta
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


# Disponibilidad, presentacion, historial y reportes de Coordinacion (Modulo 3)

# Convierte una hora devuelta por MariaDB a texto HH:MM
def hora_texto(valor):
    # Los campos TIME de MariaDB pueden recibirse como timedelta.
    if isinstance(valor, timedelta):
        segundos = int(valor.total_seconds())
        return f'{segundos//3600:02d}:{(segundos%3600)//60:02d}'
    if hasattr(valor, 'strftime'):
        return valor.strftime('%H:%M')
    return str(valor or '')[:5]


# Presenta una fecha en formato DD/MM/YYYY
def fecha_texto(valor):
    f = fecha(valor)
    return f.strftime('%d/%m/%Y') if f else ''


# Muestra el nombre del dia junto con la fecha de la asesoria
def fecha_dia(valor):
    f = fecha(valor)
    if not f:
        return ''
    dias = (*DIAS, 'Sábado', 'Domingo')
    return dias[f.weekday()]+' '+fecha_texto(f)


# Registra los formatos de fecha, hora y bloque para las plantillas Jinja2
def registrar_filtros(app):
    app.jinja_env.filters.update(fecha=fecha_texto, fecha_dia=fecha_dia, hora=hora_texto,
                                bloque=lambda valor: str(valor or '').replace('-', '–'))


# Obtiene materias autorizadas y bloques libres para publicar una franja
def opciones_franja(id_docente, id_carrera, dia_fecha, bloquear=False):
    # Al guardar, las lecturas se bloquean dentro de la transaccion de la ruta.
    lock = ' FOR UPDATE' if bloquear else ''
    # Solo permite publicar para un tutor habilitado con estado Activo.
    docente = db.query('SELECT * FROM docentes WHERE id_docente = %s'+lock, (id_docente,), one=True)
    if not docente or not docente['habilitado_tutor'] or docente['estado_laboral'] != 'Activo':
        return [], [], 'Elige un tutor habilitado y activo.'
    # Comprueba que la carrera seleccionada este activa.
    carrera = db.query('SELECT id_carrera FROM carreras WHERE id_carrera = %s AND activa = 1', (id_carrera,), one=True)
    if not carrera:
        return [], [], 'Selecciona una carrera.'
    # Cruza perfil del tutor, departamento y catalogo de la carrera.
    materias = db.query(
        'SELECT m.id_materia, m.nombre FROM tutor_materias tm JOIN materias m ON m.id_materia = tm.id_materia '
        'JOIN carrera_materia cm ON cm.id_materia = m.id_materia WHERE tm.id_docente = %s '
        'AND m.id_departamento = %s AND cm.id_carrera = %s ORDER BY m.nombre'+lock,
        (id_docente, docente['id_departamento'], id_carrera),
    )
    # Rechaza fechas pasadas y dias de fin de semana.
    if not dia_fecha or dia_fecha < hoy() or dia_fecha.weekday() > 4:
        return materias, [], 'Selecciona una fecha de lunes a viernes que no haya pasado.'
    # Excluye los bloques de clase del tutor para ese dia de la semana.
    ocupados = {f['id_bloque'] for f in db.query(
        'SELECT id_bloque FROM horario_docente WHERE id_docente = %s AND dia_semana = %s'+lock,
        (id_docente, DIAS[dia_fecha.weekday()]),
    )}
    # La clave UNIQUE tambien ocupa el bloque de una franja cancelada.
    ocupados.update(f['id_bloque'] for f in db.query(
        'SELECT id_bloque FROM franjas_asesoria WHERE id_docente = %s AND fecha = %s'+lock,
        (id_docente, dia_fecha),
    ))
    # Conserva los bloques libres; para hoy excluye las horas ya iniciadas.
    bloques = []
    for b in db.query('SELECT id_bloque, etiqueta, hora_inicio FROM bloques_horarios ORDER BY hora_inicio'):
        if b['id_bloque'] in ocupados:
            continue
        if dia_fecha == hoy() and hora_texto(b['hora_inicio']) <= ahora().strftime('%H:%M'):
            continue
        bloques.append({'id_bloque': b['id_bloque'], 'etiqueta': b['etiqueta']})
    return materias, bloques, '' if bloques else 'No hay bloques disponibles para esta fecha.'


# Obtiene el rango del reporte y valida que Desde no sea posterior a Hasta
def rango_reporte(args):
    # Si no se eligieron fechas, usa el primer y ultimo dia del mes actual.
    inicio_mes = hoy().replace(day=1)
    siguiente = (inicio_mes.replace(day=28)+timedelta(days=4)).replace(day=1)
    desde = fecha(args.get('desde', inicio_mes.isoformat()))
    hasta = fecha(args.get('hasta', (siguiente-timedelta(days=1)).isoformat()))
    if not desde or not hasta or desde > hasta:
        raise ReglaNegocio('Selecciona un rango de fechas válido: Desde no puede ser posterior a Hasta.')
    return desde, hasta


# Consulta compartida del historial, acuerdos y cita de seguimiento vinculada
# Modulo 5: incluye el estado del seguimiento para mostrar su situacion actual.
CONSULTA_CITAS = '''
 SELECT r.id_reserva, r.id_franja, r.id_estudiante, r.tipo_cita, r.id_reserva_origen, r.estado_cita,
 e.matricula, CONCAT_WS(' ', e.nombres, e.apellido_paterno, e.apellido_materno) AS estudiante,
 f.fecha, f.id_docente, f.id_carrera, f.id_materia, f.id_bloque, b.etiqueta AS horario, b.hora_inicio,
 c.nombre AS carrera, m.nombre AS materia,
 CONCAT_WS(' ', d.nombres, d.apellido_paterno, d.apellido_materno) AS docente,
 a.id_acuerdo, a.descripcion_acuerdo, a.estado_acuerdo,
 s.id_reserva AS siguiente_id, s.estado_cita AS siguiente_estado,
 sf.fecha AS siguiente_fecha, sb.etiqueta AS siguiente_horario
 FROM reservas_asesoria r
 JOIN estudiantes e ON e.id_estudiante = r.id_estudiante
 JOIN franjas_asesoria f ON f.id_franja = r.id_franja
 JOIN bloques_horarios b ON b.id_bloque = f.id_bloque
 JOIN carreras c ON c.id_carrera = f.id_carrera
 JOIN materias m ON m.id_materia = f.id_materia
 JOIN docentes d ON d.id_docente = f.id_docente
 LEFT JOIN acuerdos a ON a.id_reserva = r.id_reserva
 LEFT JOIN reservas_asesoria s ON s.id_reserva_origen = r.id_reserva
 LEFT JOIN franjas_asesoria sf ON sf.id_franja = s.id_franja
 LEFT JOIN bloques_horarios sb ON sb.id_bloque = sf.id_bloque
'''


# Consulta historiales y reportes con condiciones internas y valores parametrizados
def citas(where, params):
    return db.query(CONSULTA_CITAS+' WHERE '+where+' ORDER BY f.fecha, b.hora_inicio, e.matricula', params)


# Reservas y oferta de asesorias del estudiante (Modulo 4)
# La oferta informa; la confirmacion vuelve a comprobar los datos antes de guardar.
# Texto SQL compartido para consultar franja, tutor, materia, carrera y horario.
CONSULTA_FRANJA = '''
 SELECT f.*, b.etiqueta AS horario, b.hora_inicio, c.nombre AS carrera, c.activa AS carrera_activa,
 m.nombre AS materia, m.id_departamento AS departamento_materia,
 d.id_departamento AS departamento_docente, d.habilitado_tutor, d.estado_laboral,
 CONCAT_WS(' ',d.nombres,d.apellido_paterno,d.apellido_materno) AS docente
 FROM franjas_asesoria f JOIN bloques_horarios b ON b.id_bloque = f.id_bloque
 JOIN carreras c ON c.id_carrera = f.id_carrera JOIN materias m ON m.id_materia = f.id_materia
 JOIN docentes d ON d.id_docente = f.id_docente
'''


# Obtiene los datos de una franja y permite bloquearla durante la confirmacion
def datos_franja(id_franja, bloquear=False):
    return db.query(CONSULTA_FRANJA+' WHERE f.id_franja = %s'+(' FOR UPDATE' if bloquear else ''),
                    (id_franja,), one=True)


# Cuenta las reservas que ocupan un lugar en la franja
def reservas_activas(id_franja, bloquear=False):
    # Al confirmar, FOR UPDATE permite leer y bloquear las reservas actuales.
    return len(db.query("SELECT id_reserva FROM reservas_asesoria WHERE id_franja = %s "
                        "AND estado_cita <> 'Cancelada'"+(' FOR UPDATE' if bloquear else ''), (id_franja,)))


# Valida elegibilidad, carrera, carga, horarios, duplicados y cupo de una reserva
def validar_reserva(estudiante, franja, bloquear=False, comprobar_cupo=True):
    """Reglas comunes para reserva inicial y seguimiento.

    Al escribir se bloquea docente, estudiante y franja, en ese orden.
    Las comprobaciones críticas usan lecturas actuales dentro de la transacción.
    """
    lock = ' FOR UPDATE' if bloquear else ''
    # Comprueba que la franja siga publicada y el estudiante este Inscrito.
    if not franja or franja['estado'] != 'Publicada':
        raise ReglaNegocio('La franja ya no está publicada.')
    if estudiante['estado'] != 'Inscrito':
        raise ReglaNegocio('Solo puede reservar un estudiante con estado Inscrito.')
    # Exige un tutor habilitado y activo, con departamento compatible.
    if (not franja['habilitado_tutor'] or franja['estado_laboral'] != 'Activo'
            or franja['departamento_docente'] != franja['departamento_materia']):
        raise ReglaNegocio('El tutor ya no está habilitado para esta asesoría.')
    # La asesoria debe pertenecer a la carrera activa del estudiante.
    if estudiante['id_carrera'] != franja['id_carrera'] or not franja['carrera_activa']:
        raise ReglaNegocio('La franja debe corresponder a tu carrera.')
    # Rechaza fines de semana, fechas pasadas y bloques que ya iniciaron.
    f = fecha(franja['fecha'])
    if not f or f.weekday() > 4 or f < hoy() or (f == hoy() and hora_texto(franja['hora_inicio']) <= ahora().strftime('%H:%M')):
        raise ReglaNegocio('La fecha y hora de la asesoría deben ser futuras y de lunes a viernes.')
    # Verifica la materia autorizada en el perfil del tutor y en la carrera.
    autorizada = db.query('SELECT tm.id_materia FROM tutor_materias tm JOIN carrera_materia cm ON cm.id_materia = tm.id_materia '
                         'WHERE tm.id_docente = %s AND tm.id_materia = %s AND cm.id_carrera = %s'+lock,
                         (franja['id_docente'],franja['id_materia'],franja['id_carrera']), one=True)
    if not autorizada:
        raise ReglaNegocio('La materia ya no pertenece al perfil autorizado del tutor y de la carrera.')
    # La materia debe formar parte de la carga vigente del estudiante.
    carga = db.query('SELECT id_materia FROM horario_estudiante WHERE id_estudiante = %s AND id_materia = %s'+lock,
                    (estudiante['id_estudiante'],franja['id_materia']))
    if not carga:
        raise ReglaNegocio('La materia debe estar inscrita en tu horario actual.')
    # Rechaza cruces con clases del estudiante o del tutor en ese dia y bloque.
    clase = db.query('SELECT id_horario_est FROM horario_estudiante WHERE id_estudiante = %s AND dia_semana = %s AND id_bloque = %s'+lock,
                     (estudiante['id_estudiante'],dia(f),franja['id_bloque']))
    clase_tutor = db.query('SELECT id_horario_doc FROM horario_docente WHERE id_docente = %s AND dia_semana = %s AND id_bloque = %s'+lock,
                           (franja['id_docente'],dia(f),franja['id_bloque']))
    if clase or clase_tutor:
        raise ReglaNegocio('La asesoría coincide con una clase del estudiante o del tutor.')
    # Evita repetir una reserva del estudiante dentro de la misma franja.
    duplicada = db.query('SELECT id_reserva FROM reservas_asesoria WHERE id_estudiante = %s AND id_franja = %s'+lock,
                         (estudiante['id_estudiante'],franja['id_franja']))
    if duplicada:
        raise ReglaNegocio('Ya tienes una reserva registrada en esta franja.')
    # Rechaza otra asesoria del estudiante que coincida en fecha y horario.
    traslape = db.query("SELECT r.id_reserva FROM reservas_asesoria r JOIN franjas_asesoria f ON f.id_franja = r.id_franja "
                        "WHERE r.id_estudiante = %s AND r.estado_cita <> 'Cancelada' AND f.fecha = %s AND f.id_bloque = %s"+lock,
                        (estudiante['id_estudiante'],f,franja['id_bloque']))
    if traslape:
        raise ReglaNegocio('Ya tienes otra asesoría en esa fecha y horario.')
    # Calcula los lugares libres y exige cupo cuando se confirma la reserva.
    libres = franja['cupo_maximo']-reservas_activas(franja['id_franja'],bloquear)
    if comprobar_cupo and libres <= 0:
        raise ReglaNegocio('La franja ya no tiene cupo.')
    return max(0,libres)


# Obtiene las franjas compatibles e incluye las agotadas para mostrar Sin cupo
def oferta_estudiante(estudiante, id_materia=None, id_docente=None, posterior=None):
    """Incluye agotadas para mostrar Sin cupo; no fabrica los ejemplos del wireframe."""
    # Filtra las franjas publicadas por carrera, fecha, materia y tutor.
    condiciones = ['f.id_carrera = %s', 'f.fecha >= %s', "f.estado = 'Publicada'"]
    params = [estudiante['id_carrera'],hoy()]
    if id_materia:
        condiciones.append('f.id_materia = %s'); params.append(id_materia)
    if id_docente:
        condiciones.append('f.id_docente = %s'); params.append(id_docente)
    filas = db.query(CONSULTA_FRANJA+' WHERE '+' AND '.join(condiciones)+' ORDER BY f.fecha,b.hora_inicio',tuple(params))
    salida = []
    for franja in filas:
        # Si se solicita una cita posterior, descarta horarios anteriores o iguales.
        if posterior and (fecha(franja['fecha']),hora_texto(franja['hora_inicio'])) <= posterior:
            continue
        # Comprueba la compatibilidad sin ocultar las franjas agotadas.
        try:
            libres = validar_reserva(estudiante,franja,comprobar_cupo=False)
        except ReglaNegocio:
            continue
        franja['lugares_libres'] = libres
        salida.append(franja)
    return salida

