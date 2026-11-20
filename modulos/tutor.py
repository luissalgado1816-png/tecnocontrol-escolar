#Modificacion ultimo modulo
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from pymysql import MySQLError
from auth import rol_requerido
import db
import reglas

bp = Blueprint('tutor', __name__, url_prefix='/tutor')
ROL = 'consulta_seguimiento'
# Vista inicial de agenda de franjas y lista de estudiantes

def _tutor():
    docente = db.query('SELECT * FROM docentes WHERE id_usuario = %s', (g.user['id_usuario'],), one=True)
    if not docente or not docente['habilitado_tutor'] or docente['estado_laboral'] != 'Activo':
        abort(403)
    return docente


@bp.get('/franjas')
@rol_requerido(ROL)
def franjas():
    tutor = _tutor()
    valor_fecha = request.args.get('fecha',reglas.hoy().isoformat())
    seleccion = reglas.fecha(valor_fecha)
    errores = []
    if not seleccion:
        errores.append('Selecciona una fecha válida.')
    filas = db.query('SELECT v.*,b.etiqueta AS horario,m.nombre AS materia FROM v_franjas_cupo v '
                     'JOIN bloques_horarios b ON b.id_bloque = v.id_bloque JOIN materias m ON m.id_materia = v.id_materia '
                     'WHERE v.id_docente = %s AND v.fecha = %s ORDER BY b.hora_inicio',
                     (tutor['id_docente'],seleccion)) if seleccion else []
    id_franja = reglas.entero(request.args.get('franja'))
    elegida = None
    citas = []
    if request.args.get('franja'):
        elegida = reglas.datos_franja(id_franja)
        if not elegida or elegida['id_docente'] != tutor['id_docente']:
            abort(404)
        if reglas.fecha(elegida['fecha']) != seleccion:
            abort(404)
        citas = reglas.citas('r.id_franja = %s AND f.id_docente = %s',(id_franja,tutor['id_docente']))
    return render_template('tutor/franjas.html',filas=filas,fecha=valor_fecha,errores=errores,elegida=elegida,citas=citas)


def _cita(id_reserva, id_docente, bloquear=False):
    consulta = reglas.CONSULTA_CITAS+' WHERE r.id_reserva = %s AND f.id_docente = %s'
    return db.query(consulta+(' FOR UPDATE' if bloquear else ''),(id_reserva,id_docente),one=True)


def _opciones(cita):
    estudiante = db.query('SELECT * FROM estudiantes WHERE id_estudiante = %s',(cita['id_estudiante'],),one=True)
    posterior = (reglas.fecha(cita['fecha']),reglas.hora_texto(cita['hora_inicio']))
    return [f for f in reglas.oferta_estudiante(estudiante,id_docente=cita['id_docente'],posterior=posterior) if f['lugares_libres'] > 0]


@bp.route('/acuerdo/<int:id_reserva>',methods=['GET','POST'])
@rol_requerido(ROL)
def acuerdo(id_reserva):
    tutor = _tutor()
    cita = _cita(id_reserva,tutor['id_docente'])
    if not cita:
        abort(404)
    errores = []
    form = {'realizada':'1' if cita['estado_cita'] == 'Realizada' else '',
            'descripcion':cita['descripcion_acuerdo'] or '',
            'decision':'cerrar','franja':''}
    if cita['id_acuerdo']:
        form['decision'] = 'seguir' if cita['estado_acuerdo'] == 'En seguimiento' else 'cerrar'
        form['franja'] = str(cita['siguiente_id'] or '')
    if request.method == 'POST':
        form = {k:request.form.get(k,'').strip() for k in form}
        try:
            if form['realizada'] != '1':
                raise reglas.ReglaNegocio('Marca la atención como realizada antes de guardar el acuerdo.')
            if not form['descripcion'] or len(form['descripcion']) > 10000:
                raise reglas.ReglaNegocio('Escribe el acuerdo individual, con un máximo de 10000 caracteres.')
            if form['decision'] not in ('cerrar','seguir'):
                raise reglas.ReglaNegocio('Elige Cerrar acuerdo o Agendar seguimiento.')
            with db.transaction():
                docente_actual = reglas.bloquear_docente(tutor['id_docente'])
                estudiante = reglas.bloquear_estudiante(cita['id_estudiante'])
                actual = _cita(id_reserva,tutor['id_docente'],bloquear=True)
                if not docente_actual['habilitado_tutor'] or docente_actual['estado_laboral'] != 'Activo':
                    raise reglas.ReglaNegocio('El tutor ya no está habilitado.')
                if not actual or actual['id_acuerdo']:
                    raise reglas.ReglaNegocio('Esta cita ya tiene un acuerdo guardado. Consulta su registro.')
                if actual['estado_cita'] not in ('Programada','Realizada'):
                    raise reglas.ReglaNegocio('La atención debe corresponder a una cita programada o realizada.')
                if db.query('SELECT id_reserva FROM reservas_asesoria WHERE id_reserva_origen = %s FOR UPDATE',(id_reserva,)):
                    raise reglas.ReglaNegocio('La cita ya tiene un seguimiento vinculado.')
                # Orden requerido por los triggers: primero atención, después acuerdo,
                # finalmente seguimiento. Cualquier rechazo revierte las tres escrituras.
                db.execute("UPDATE reservas_asesoria SET estado_cita = 'Realizada' WHERE id_reserva = %s",(id_reserva,))
                estado = 'En seguimiento' if form['decision'] == 'seguir' else 'Cerrado'
                db.insert('INSERT INTO acuerdos(id_reserva,descripcion_acuerdo,estado_acuerdo) VALUES(%s,%s,%s)',
                          (id_reserva,form['descripcion'],estado))
                if form['decision'] == 'seguir':
                    nueva = reglas.datos_franja(reglas.entero(form['franja']),bloquear=True)
                    if not nueva or nueva['id_docente'] != tutor['id_docente']:
                        raise reglas.ReglaNegocio('Elige una franja de seguimiento del mismo tutor.')
                    origen = (reglas.fecha(actual['fecha']),reglas.hora_texto(actual['hora_inicio']))
                    if (reglas.fecha(nueva['fecha']),reglas.hora_texto(nueva['hora_inicio'])) <= origen:
                        raise reglas.ReglaNegocio('La franja de seguimiento debe ser posterior a la cita de origen.')
                    reglas.validar_reserva(estudiante,nueva,bloquear=True)
                    db.insert("INSERT INTO reservas_asesoria(id_franja,id_estudiante,tipo_cita,id_reserva_origen,estado_cita) "
                              "VALUES(%s,%s,'Seguimiento',%s,'Programada')",(nueva['id_franja'],estudiante['id_estudiante'],id_reserva))
        except reglas.ReglaNegocio as error:
            errores.append(str(error))
        except MySQLError as error:
            errores.append(db.mensaje_error(error))
        else:
            flash('El acuerdo queda '+estado+(' con una cita vinculada.' if estado == 'En seguimiento' else '.'),'success')
            return redirect(url_for('tutor.franjas',fecha=reglas.fecha(cita['fecha']).isoformat(),franja=cita['id_franja']))
    if errores:
        # Tras rollback se consulta otra vez: un segundo envío puede encontrar
        # un acuerdo que otra petición acaba de guardar.
        cita = _cita(id_reserva,tutor['id_docente'])
        if not cita:
            abort(404)
    opciones = _opciones(cita) if not cita['id_acuerdo'] else []
    return render_template('tutor/acuerdo.html',cita=cita,form=form,opciones=opciones,errores=errores)

# Vista inicial de reporte de asesorias impartidas
@bp.get('/reportes')
@rol_requerido(ROL)
def reportes():
    tutor = _tutor()
    errores = []
    filas = []
    try:
        desde,hasta = reglas.rango_reporte(request.args)
        filas = reglas.citas('f.id_docente = %s AND f.fecha >= %s AND f.fecha <= %s',(tutor['id_docente'],desde,hasta))
        desde,hasta = desde.isoformat(),hasta.isoformat()
    except reglas.ReglaNegocio as error:
        errores.append(str(error));desde=request.args.get('desde','');hasta=request.args.get('hasta','')
    return render_template('tutor/reportes.html',filas=filas,desde=desde,hasta=hasta,errores=errores)
