
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from pymysql import MySQLError
from auth import rol_requerido
import db
import reglas

bp = Blueprint('estudiante', __name__, url_prefix='/estudiante')
ROL = 'consulta_seguimiento_est'


def _estudiante():
    estudiante = db.query('SELECT * FROM estudiantes WHERE id_usuario = %s', (g.user['id_usuario'],), one=True)
    if not estudiante:
        abort(403)
    return estudiante


@bp.get('/reservar')
@rol_requerido(ROL)
def reservar():
    estudiante = _estudiante()
    materias = db.query('SELECT DISTINCT m.id_materia,m.nombre FROM horario_estudiante h '
                        'JOIN materias m ON m.id_materia = h.id_materia JOIN carrera_materia cm ON cm.id_materia = m.id_materia '
                        'WHERE h.id_estudiante = %s AND cm.id_carrera = %s ORDER BY m.nombre',
                        (estudiante['id_estudiante'],estudiante['id_carrera']))
    seleccion = reglas.entero(request.args.get('materia'))
    if seleccion not in {m['id_materia'] for m in materias}:
        seleccion = None
    filas = reglas.oferta_estudiante(estudiante,id_materia=seleccion) if seleccion else []
    return render_template('estudiante/reservar.html', materias=materias,seleccion=seleccion,
                           disponibles=[f for f in filas if f['lugares_libres'] > 0],
                           agotadas=[f for f in filas if f['lugares_libres'] == 0],estudiante=estudiante)


@bp.route('/reservar/<int:id_franja>',methods=['GET','POST'])
@rol_requerido(ROL)
def confirmar(id_franja):
    estudiante = _estudiante()
    franja = reglas.datos_franja(id_franja)
    if not franja:
        abort(404)
    try:
        if request.method == 'POST':
            # Lecturas actuales tras bloquear: cuenta, cupo y carga pueden haber cambiado.
            with db.transaction():
                reglas.bloquear_docente(franja['id_docente'])
                actual = reglas.bloquear_estudiante(estudiante['id_estudiante'])
                actual_franja = reglas.datos_franja(id_franja,bloquear=True)
                reglas.validar_reserva(actual,actual_franja,bloquear=True)
                db.insert("INSERT INTO reservas_asesoria (id_franja,id_estudiante,tipo_cita,id_reserva_origen,estado_cita) "
                          "VALUES (%s,%s,'Inicial',NULL,'Programada')",(id_franja,actual['id_estudiante']))
            flash('La cita queda Programada y aparece en Mi historial.','success')
            return redirect(url_for('estudiante.historial'))
        libres = reglas.validar_reserva(estudiante,franja)
    except (reglas.ReglaNegocio,MySQLError):
        flash('La franja ya no está disponible. Consulta la oferta actualizada.','warning')
        return redirect(url_for('estudiante.reservar',materia=franja['id_materia']))
    return render_template('estudiante/confirmar.html',franja=franja,libres=libres)


@bp.get('/historial')
@rol_requerido(ROL)
def historial():
    estudiante = _estudiante()
    filas = reglas.citas('r.id_estudiante = %s',(estudiante['id_estudiante'],))
    return render_template('estudiante/historial.html',filas=filas)
