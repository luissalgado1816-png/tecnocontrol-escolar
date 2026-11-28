# Modulo 3: Rutas base del Coordinador de Tutorias (P-02)
from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from pymysql import MySQLError
import db
import reglas
from auth import rol_requerido

bp = Blueprint("coordinacion", __name__, url_prefix="/coordinacion")
ROL = "coordinador_tutorias"


@bp.get("/tutores")
@rol_requerido(ROL)
def tutores():
    filtros = {
        k: request.args.get(k, "").strip()
        for k in ("clave", "paterno", "materno", "nombres")
    }
    filas = db.query(
        "SELECT d.*, dep.nombre AS departamento, CONCAT_WS(' ', d.nombres, d.apellido_paterno, d.apellido_materno) AS nombre "
        "FROM docentes d JOIN departamentos dep ON dep.id_departamento = d.id_departamento "
        "WHERE d.clave_docente LIKE %s AND d.apellido_paterno LIKE %s "
        "AND COALESCE(d.apellido_materno,'') LIKE %s AND d.nombres LIKE %s ORDER BY d.clave_docente",
        tuple(
            "%"
            + filtros[k].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            + "%"
            for k in ("clave", "paterno", "materno", "nombres")
        ),
    )
    return render_template("coordinacion/tutores.html", filas=filas, filtros=filtros)


@bp.route("/tutores/<int:id_docente>", methods=["GET", "POST"])
@rol_requerido(ROL)
def perfil(id_docente):
    docente = db.query(
        "SELECT d.*, dep.nombre AS departamento, CONCAT_WS(' ', d.nombres, d.apellido_paterno, d.apellido_materno) AS nombre "
        "FROM docentes d JOIN departamentos dep ON dep.id_departamento = d.id_departamento WHERE d.id_docente = %s",
        (id_docente,),
        one=True,
    )
    if not docente:
        abort(404)

    def elegibles():
        return db.query(
            "SELECT DISTINCT m.id_materia,m.nombre FROM v_materias_elegibles_tutor e "
            "JOIN v_horario_docente_actual h USING(id_docente,id_carrera,id_materia) "
            "JOIN materias m ON m.id_materia=e.id_materia "
            "WHERE e.id_docente=%s ORDER BY m.nombre",
            (id_docente,),
        )

    materias = elegibles()
    seleccionadas = {
        m["id_materia"]
        for m in db.query(
            "SELECT id_materia FROM tutor_materias WHERE id_docente=%s AND autorizada=1",
            (id_docente,),
        )
    }
    habilitar = bool(docente["habilitado_tutor"])
    errores = []
    if request.method == "POST":
        habilitar = request.form.get("habilitado") == "1"
        nuevas = (
            {reglas.entero(v) for v in request.form.getlist("materias")}
            if habilitar
            else set()
        )
        try:
            with db.transaction():
                actual = reglas.bloquear_docente(id_docente)
                if actual["estado_laboral"] != "Activo":
                    raise reglas.ReglaNegocio(
                        "Solo se puede habilitar como tutor a un docente activo."
                    )
                permitidas = {m["id_materia"] for m in elegibles()}
                if habilitar and (not nuevas or not nuevas <= permitidas):
                    raise reglas.ReglaNegocio(
                        "Selecciona materias permitidas por la carga y el grado del docente."
                    )
                anteriores = {
                    m["id_materia"]
                    for m in db.query(
                        "SELECT id_materia FROM tutor_materias WHERE id_docente=%s AND autorizada=1",
                        (id_docente,),
                    )
                }
                if not habilitar:
                    reglas.cancelar_franjas(
                        id_docente, "Tutor deshabilitado por Coordinación"
                    )
                # Las materias previas autorizadas antes de este cambio pueden tener
                # franjas vigentes. Guardar este formulario solo modifica la carga visible.
                retiradas = (anteriores & permitidas) - nuevas if habilitar else anteriores
                for materia in retiradas:
                    if habilitar:
                        reglas.cancelar_franjas(
                            id_docente,
                            "Materia retirada por Coordinación",
                            materia=materia,
                        )
                    db.execute(
                        "UPDATE tutor_materias SET autorizada=0 WHERE id_docente=%s AND id_materia=%s",
                        (id_docente, materia),
                    )
                for materia in nuevas - anteriores:
                    db.execute(
                        "INSERT INTO tutor_materias(id_docente,id_materia,autorizada) VALUES(%s,%s,1) "
                        "ON DUPLICATE KEY UPDATE autorizada=1",
                        (id_docente, materia),
                    )
                db.execute(
                    "UPDATE docentes SET habilitado_tutor=%s WHERE id_docente=%s",
                    (int(habilitar), id_docente),
                )
        except (reglas.ReglaNegocio, MySQLError) as e:
            errores.append(db.mensaje_error(e) if isinstance(e, MySQLError) else str(e))
            seleccionadas = nuevas
        else:
            flash("Perfil de asesorías guardado.", "success")
            return redirect(url_for("coordinacion.tutores"))
    return render_template(
        "coordinacion/perfil.html",
        docente=docente,
        materias=materias,
        seleccionadas=seleccionadas,
        habilitar=habilitar,
        errores=errores,
    )


def _catalogos_franjas():
    tutores = db.query(
        "SELECT id_docente, CONCAT_WS(' ',nombres,apellido_paterno,apellido_materno) AS nombre FROM docentes WHERE habilitado_tutor = 1 AND estado_laboral = 'Activo' ORDER BY apellido_paterno"
    )
    carreras = db.query(
        "SELECT id_carrera,nombre FROM carreras WHERE activa = 1 ORDER BY nombre"
    )
    return tutores, carreras


@bp.route("/franjas", methods=["GET", "POST"])
@rol_requerido(ROL)
def franjas():
    tutores, carreras = _catalogos_franjas()
    fuente = request.form if request.method == "POST" else request.args
    form = {k: fuente.get(k, "") for k in ("docente", "carrera", "materia")}
    docente, carrera, materia = (
        reglas.entero(form[k]) for k in ("docente", "carrera", "materia")
    )
    errores = []
    if request.method == "POST":
        seleccion = request.form.getlist("seleccion")
        if not seleccion and request.form.get("fecha") and request.form.get("bloque"):
            seleccion = [request.form["fecha"] + "|" + request.form["bloque"]]
        cupo = reglas.entero(request.form.get("cupo_maximo", "10"))
        try:
            if (
                not all((docente, carrera, materia, cupo))
                or cupo > 65535
                or not 1 <= len(seleccion) <= 130
            ):
                raise reglas.ReglaNegocio(
                    "Selecciona tutor, carrera, materia, cupo y al menos un bloque del calendario."
                )
            with db.transaction():
                reglas.bloquear_docente(docente)
                for valor in seleccion:
                    fecha, separador, bloque = valor.partition("|")
                    f, b = reglas.fecha(fecha), reglas.entero(bloque)
                    materias, libres, aviso = reglas.opciones_franja(
                        docente, carrera, f
                    )
                    if materia not in {m["id_materia"] for m in materias}:
                        raise reglas.ReglaNegocio(
                            "La materia debe estar autorizada para este tutor y carrera."
                        )
                    if not separador or b not in {h["id_bloque"] for h in libres}:
                        raise reglas.ReglaNegocio(aviso or "Elige un bloque libre.")
                    db.insert(
                        "INSERT INTO franjas_asesoria(id_docente,id_carrera,id_materia,fecha,id_bloque,cupo_maximo) "
                        "VALUES(%s,%s,%s,%s,%s,%s)",
                        (docente, carrera, materia, f, b, cupo),
                    )
        except (reglas.ReglaNegocio, MySQLError) as e:
            errores.append(db.mensaje_error(e) if isinstance(e, MySQLError) else str(e))
        else:
            flash("Franjas publicadas: " + str(len(seleccion)) + ".", "success")
            return redirect(
                url_for(
                    "coordinacion.franjas",
                    semana=int(request.form.get("semana") == "1"),
                    **form,
                )
            )
    materias, _, _ = reglas.opciones_franja(docente, carrera, None)
    filas = db.query(
        "SELECT v.*,b.etiqueta AS horario,m.nombre AS materia,c.nombre AS carrera,"
        "CONCAT_WS(' ',d.nombres,d.apellido_paterno,d.apellido_materno) AS docente FROM v_franjas_cupo v "
        "JOIN bloques_horarios b USING(id_bloque) JOIN materias m USING(id_materia) JOIN carreras c USING(id_carrera) "
        "JOIN docentes d USING(id_docente) WHERE v.fecha BETWEEN %s AND %s "
        "ORDER BY v.fecha,b.hora_inicio,docente",
        (reglas.semanas()[0][0], reglas.semanas()[1][-1]),
    )
    return render_template(
        "coordinacion/franjas.html",
        form=form,
        errores=errores,
        tutores=tutores,
        carreras=carreras,
        materias=materias,
        filas=filas,
        agenda=reglas.calendario_docente(docente),
    )


@bp.get("/franjas/opciones")
@rol_requerido(ROL)
def franjas_opciones():
    d, c = (reglas.entero(request.args.get(k)) for k in ("docente", "carrera"))
    materias, bloques, mensaje = reglas.opciones_franja(
        d, c, reglas.fecha(request.args.get("fecha"))
    )
    return jsonify(
        materias=materias,
        bloques=[
            {"id_bloque": b["id_bloque"], "etiqueta": b["etiqueta"]} for b in bloques
        ],
        agenda=reglas.calendario_docente(d),
        mensaje=mensaje,
    )


@bp.post("/franjas/<int:id_franja>/cupo")
@rol_requerido(ROL)
def cupo(id_franja):
    f = reglas.datos_franja(id_franja)
    if not f:
        abort(404)
    nuevo = reglas.entero(request.form.get("cupo_maximo"))
    try:
        with db.transaction():
            reglas.bloquear_docente(f["id_docente"])
            f = reglas.datos_franja(id_franja, bloquear=True)
            if f["estado"] != "Publicada":
                raise reglas.ReglaNegocio("El cupo se ajusta en una franja publicada.")
            if not nuevo or nuevo > 65535 or nuevo < reglas.reservas_activas(id_franja):
                raise reglas.ReglaNegocio(
                    "El cupo debe ser positivo y cubrir todos los lugares apartados."
                )
            db.execute(
                "UPDATE franjas_asesoria SET cupo_maximo=%s WHERE id_franja=%s",
                (nuevo, id_franja),
            )
        flash("Cupo actualizado.", "success")
    except (reglas.ReglaNegocio, MySQLError) as e:
        flash(db.mensaje_error(e) if isinstance(e, MySQLError) else str(e), "warning")
    return redirect(
        url_for(
            "coordinacion.franjas",
            docente=f["id_docente"],
            carrera=f["id_carrera"],
            materia=f["id_materia"],
            semana=int(f["fecha"] >= reglas.semanas()[1][0]),
        )
    )


@bp.get("/historial")
@rol_requerido(ROL)
def historial():
    q = request.args.get("q", "").strip().upper()
    estudiante = (
        db.query(
            "SELECT e.*,c.nombre AS carrera,CONCAT_WS(' ',e.nombres,e.apellido_paterno,e.apellido_materno) AS nombre FROM estudiantes e JOIN carreras c USING(id_carrera) WHERE matricula = %s",
            (q,),
            one=True,
        )
        if q
        else None
    )
    filas = (
        reglas.citas("r.id_estudiante = %s", (estudiante["id_estudiante"],))
        if estudiante
        else []
    )
    return render_template(
        "coordinacion/historial.html",
        q=q,
        estudiante=estudiante,
        filas=filas,
        grupos=reglas.recorridos(filas),
    )


@bp.get("/reportes")
@rol_requerido(ROL)
def reportes():
    errores = []
    filas = []
    carreras = db.query("SELECT id_carrera,nombre FROM carreras ORDER BY nombre")
    tutores = db.query(
        "SELECT id_docente,CONCAT_WS(' ',nombres,apellido_paterno,apellido_materno) AS nombre FROM docentes ORDER BY apellido_paterno"
    )
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    carrera = request.args.get("carrera", "")
    tutor = request.args.get("tutor", "")
    try:
        desde, hasta = reglas.rango_reporte(request.args)
        condiciones = ["f.fecha >= %s", "f.fecha <= %s"]
        params = [desde, hasta]
        for campo, valor, permitidos in [
            ("id_carrera", carrera, {c["id_carrera"] for c in carreras}),
            ("id_docente", tutor, {d["id_docente"] for d in tutores}),
        ]:
            if valor:
                id_ = reglas.entero(valor)
                if id_ not in permitidos:
                    raise reglas.ReglaNegocio(
                        "Selecciona una carrera y un tutor válidos para el reporte."
                    )
                condiciones.append("f." + campo + " = %s")
                params.append(id_)
        filas = reglas.citas(" AND ".join(condiciones), tuple(params))
    except reglas.ReglaNegocio as error:
        errores.append(str(error))
    detalles = {}
    alumnos = {
        r["id_estudiante"]
        for r in filas
        if r["estado_acuerdo"] or r["id_reserva_origen"]
    }
    if alumnos:
        parametros = tuple(sorted(alumnos))
        historial = reglas.citas(
            "r.id_estudiante IN (" + ",".join(["%s"] * len(alumnos)) + ")", parametros
        )
        detalles = {
            r["id_reserva"]: [grupo]
            for grupo in reglas.recorridos(historial)
            for r in grupo
        }
    return render_template(
        "coordinacion/reportes.html",
        detalles=detalles,
        errores=errores,
        filas=filas,
        desde=desde,
        hasta=hasta,
        carrera=carrera,
        tutor=tutor,
        carreras=carreras,
        tutores=tutores,
    )
