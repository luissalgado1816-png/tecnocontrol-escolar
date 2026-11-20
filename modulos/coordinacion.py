# Modulo 3: Rutas base del Coordinador de Tutorias (P-02)
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from pymysql import MySQLError
import db
import reglas
from auth import rol_requerido

bp = Blueprint('coordinacion', __name__, url_prefix='/coordinacion')
ROL = 'coordinador_tutorias'


@bp.get('/tutores')
@rol_requerido(ROL)
def tutores():
    filtros = {k: request.args.get(k, '').strip() for k in ('clave', 'paterno', 'materno', 'nombres')}
    filas = db.query(
        "SELECT d.*, dep.nombre AS departamento, CONCAT_WS(' ', d.nombres, d.apellido_paterno, d.apellido_materno) AS nombre "
        "FROM docentes d JOIN departamentos dep ON dep.id_departamento = d.id_departamento "
        "WHERE d.clave_docente LIKE %s AND d.apellido_paterno LIKE %s "
        "AND COALESCE(d.apellido_materno,'') LIKE %s AND d.nombres LIKE %s ORDER BY d.clave_docente",
        tuple('%'+filtros[k].replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%' for k in ('clave','paterno','materno','nombres')),
    )
    return render_template('coordinacion/tutores.html', filas=filas, filtros=filtros)


@bp.route('/tutores/<int:id_docente>', methods=['GET','POST'])
@rol_requerido(ROL)
def perfil(id_docente):
    docente = db.query(
        'SELECT d.*, dep.nombre AS departamento, CONCAT_WS(\' \', d.nombres, d.apellido_paterno, d.apellido_materno) AS nombre '
        'FROM docentes d JOIN departamentos dep ON dep.id_departamento = d.id_departamento WHERE d.id_docente = %s',
        (id_docente,), one=True,
    )
    if not docente:
        abort(404)
    materias = db.query('SELECT id_materia, nombre FROM materias WHERE id_departamento = %s ORDER BY nombre', (docente['id_departamento'],))
    seleccionadas = {m['id_materia'] for m in db.query('SELECT id_materia FROM tutor_materias WHERE id_docente = %s', (id_docente,))}
    habilitar = bool(docente['habilitado_tutor'])
    errores = []
    if request.method == 'POST':
        valores = request.form.getlist('materias')
        seleccionadas = {reglas.entero(v) for v in valores}
        habilitar = request.form.get('habilitado') == '1'
        try:
            with db.transaction():
                actual = reglas.bloquear_docente(id_docente)
                permitidas = {m['id_materia'] for m in db.query(
                    'SELECT id_materia FROM materias WHERE id_departamento = %s FOR UPDATE', (actual['id_departamento'],))}
                if None in seleccionadas or not seleccionadas <= permitidas:
                    raise reglas.ReglaNegocio('Selecciona únicamente materias del departamento del docente.')
                if actual['estado_laboral'] != 'Activo' and (habilitar or seleccionadas):
                    raise reglas.ReglaNegocio('Solo se puede habilitar como tutor a un docente activo.')
                if habilitar and not seleccionadas:
                    raise reglas.ReglaNegocio('Selecciona al menos una materia que pueda asesorar.')
                pendientes = db.query(
                    "SELECT r.id_reserva FROM reservas_asesoria r JOIN franjas_asesoria f ON f.id_franja = r.id_franja "
                    "WHERE f.id_docente = %s AND f.fecha >= %s AND f.estado = 'Publicada' AND r.estado_cita = 'Programada' FOR UPDATE",
                    (id_docente, reglas.hoy()),
                )
                if not habilitar and pendientes:
                    raise reglas.ReglaNegocio('El tutor tiene asesorías programadas. Conserva su habilitación para atenderlas.')
                anteriores = {m['id_materia'] for m in db.query('SELECT id_materia FROM tutor_materias WHERE id_docente = %s FOR UPDATE', (id_docente,))}
                retirar = anteriores-seleccionadas
                for materia in retirar:
                    if db.query('SELECT id_franja FROM franjas_asesoria WHERE id_docente = %s AND id_materia = %s LIMIT 1 FOR UPDATE', (id_docente,materia), one=True):
                        raise reglas.ReglaNegocio('No se puede retirar una materia que tiene franjas registradas; se conserva su historial.')
                    db.execute('DELETE FROM tutor_materias WHERE id_docente = %s AND id_materia = %s', (id_docente,materia))
                for materia in seleccionadas-anteriores:
                    db.execute('INSERT INTO tutor_materias (id_docente,id_materia) VALUES (%s,%s)', (id_docente,materia))
                db.execute('UPDATE docentes SET habilitado_tutor = %s WHERE id_docente = %s', (int(habilitar),id_docente))
                db.execute('UPDATE usuarios SET activo = %s WHERE id_usuario = %s', (int(habilitar),actual['id_usuario']))
        except reglas.ReglaNegocio as error:
            errores.append(str(error))
        except MySQLError as error:
            errores.append(db.mensaje_error(error))
        else:
            flash('Perfil de asesorías guardado. Se activó la cuenta del tutor.' if habilitar else 'Perfil de asesorías guardado.', 'success')
            return redirect(url_for('coordinacion.tutores'))
    return render_template('coordinacion/perfil.html', docente=docente, materias=materias, seleccionadas=seleccionadas, habilitar=habilitar, errores=errores)


def _catalogos_franjas():
    tutores = db.query("SELECT id_docente, CONCAT_WS(' ',nombres,apellido_paterno,apellido_materno) AS nombre FROM docentes WHERE habilitado_tutor = 1 AND estado_laboral = 'Activo' ORDER BY apellido_paterno")
    carreras = db.query('SELECT id_carrera,nombre FROM carreras WHERE activa = 1 ORDER BY nombre')
    return tutores,carreras


@bp.route('/franjas',methods=['GET','POST'])
@rol_requerido(ROL)
def franjas():
    tutores,carreras = _catalogos_franjas()
    fuente = request.form if request.method == 'POST' else request.args
    form = {k:fuente.get(k,'') for k in ('docente','carrera','materia','bloque')}
    form['fecha'] = fuente.get('fecha',reglas.hoy().isoformat())
    errores = []
    if request.method == 'POST':
        id_docente,id_carrera,id_materia,id_bloque = (reglas.entero(form[k]) for k in ('docente','carrera','materia','bloque'))
        try:
            if not all((id_docente,id_carrera,id_materia,id_bloque)):
                raise reglas.ReglaNegocio('Elige un tutor habilitado, una materia de su perfil y un bloque disponible.')
            if request.form.get('cupo_maximo','10') != '10':
                raise reglas.ReglaNegocio('El cupo es fijo de 10 lugares.')
            with db.transaction():
                reglas.bloquear_docente(id_docente)
                materias,bloques,mensaje = reglas.opciones_franja(id_docente,id_carrera,reglas.fecha(form['fecha']),bloquear=True)
                if id_materia not in {m['id_materia'] for m in materias}:
                    raise reglas.ReglaNegocio('La materia debe estar autorizada para el tutor, su departamento y la carrera elegida.')
                if id_bloque not in {b['id_bloque'] for b in bloques}:
                    raise reglas.ReglaNegocio(mensaje or 'El bloque ya está ocupado. Consulta el horario disponible.')
                db.insert('INSERT INTO franjas_asesoria (id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo,estado) VALUES (%s,%s,%s,%s,%s,10,\'Publicada\')',
                          (id_docente,id_carrera,id_materia,reglas.fecha(form['fecha']),id_bloque))
        except reglas.ReglaNegocio as error:
            errores.append(str(error))
        except MySQLError as error:
            errores.append(db.mensaje_error(error))
        else:
            flash('Franja de asesoría publicada correctamente.','success')
            return redirect(url_for('coordinacion.franjas'))
    materias,bloques,_ = reglas.opciones_franja(reglas.entero(form['docente']),reglas.entero(form['carrera']),reglas.fecha(form['fecha']))
    filas = db.query(
        "SELECT v.*,b.etiqueta AS horario,m.nombre AS materia,c.nombre AS carrera,CONCAT_WS(' ',d.nombres,d.apellido_paterno,d.apellido_materno) AS docente "
        "FROM v_franjas_cupo v JOIN bloques_horarios b ON b.id_bloque = v.id_bloque JOIN materias m ON m.id_materia = v.id_materia "
        "JOIN carreras c ON c.id_carrera = v.id_carrera JOIN docentes d ON d.id_docente = v.id_docente ORDER BY v.fecha,b.hora_inicio")
    return render_template('coordinacion/franjas.html', form=form,errores=errores,tutores=tutores,carreras=carreras,materias=materias,bloques=bloques,filas=filas,dia=reglas.dia(form['fecha']))


@bp.get('/franjas/opciones')
@rol_requerido(ROL)
def franjas_opciones():
    f=reglas.fecha(request.args.get('fecha'))
    materias,bloques,mensaje=reglas.opciones_franja(reglas.entero(request.args.get('docente')),reglas.entero(request.args.get('carrera')),f)
    return jsonify(materias=materias,bloques=bloques,dia=reglas.dia(f),mensaje=mensaje)


@bp.get('/historial')
@rol_requerido(ROL)
def historial():
    q=request.args.get('q','').strip().upper()
    estudiante=db.query("SELECT e.*,c.nombre AS carrera,CONCAT_WS(' ',e.nombres,e.apellido_paterno,e.apellido_materno) AS nombre FROM estudiantes e JOIN carreras c USING(id_carrera) WHERE matricula = %s",(q,),one=True) if q else None
    filas=reglas.citas('r.id_estudiante = %s',(estudiante['id_estudiante'],)) if estudiante else []
    return render_template('coordinacion/historial.html',q=q,estudiante=estudiante,filas=filas)


@bp.get('/reportes')
@rol_requerido(ROL)
def reportes():
    errores=[];filas=[]
    carreras=db.query('SELECT id_carrera,nombre FROM carreras ORDER BY nombre')
    tutores=db.query("SELECT id_docente,CONCAT_WS(' ',nombres,apellido_paterno,apellido_materno) AS nombre FROM docentes ORDER BY apellido_paterno")
    desde=request.args.get('desde','');hasta=request.args.get('hasta','')
    carrera=request.args.get('carrera','');tutor=request.args.get('tutor','')
    try:
        desde,hasta=reglas.rango_reporte(request.args)
        condiciones=['f.fecha >= %s','f.fecha <= %s'];params=[desde,hasta]
        for campo,valor,permitidos in [('id_carrera',carrera,{c['id_carrera'] for c in carreras}),('id_docente',tutor,{d['id_docente'] for d in tutores})]:
            if valor:
                id_=reglas.entero(valor)
                if id_ not in permitidos:raise reglas.ReglaNegocio('Selecciona una carrera y un tutor válidos para el reporte.')
                condiciones.append('f.'+campo+' = %s');params.append(id_)
        filas=reglas.citas(' AND '.join(condiciones),tuple(params))
    except reglas.ReglaNegocio as error:
        errores.append(str(error))
    return render_template('coordinacion/reportes.html',errores=errores,filas=filas,desde=desde,hasta=hasta,carrera=carrera,tutor=tutor,carreras=carreras,tutores=tutores)
