# Modificacion ultimo modulo
from datetime import timedelta

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from pymysql import MySQLError
from auth import rol_requerido
import db
import reglas

bp = Blueprint("tutor", __name__, url_prefix="/tutor")
ROL = "consulta_seguimiento"
# Vista inicial de agenda de franjas y lista de estudiantes


def _tutor():
    docente = db.query(
        "SELECT * FROM docentes WHERE id_usuario = %s",
        (g.user["id_usuario"],),
        one=True,
    )
    if (
        not docente
        or not docente["habilitado_tutor"]
        or docente["estado_laboral"] != "Activo"
    ):
        abort(403)
    return docente


@bp.get("/franjas")
@rol_requerido(ROL)
def franjas():
    tutor = _tutor()
    valor_desde = request.args.get(
        "desde", request.args.get("fecha", reglas.hoy().isoformat())
    )
    valor_hasta = request.args.get("hasta", "")
    desde = reglas.fecha(valor_desde)
    hasta = reglas.fecha(valor_hasta) if valor_hasta else desde
    errores = []
    if not desde or not hasta:
        errores.append("Selecciona fechas válidas.")
    elif desde > hasta:
        errores.append("La fecha Hasta debe ser igual o posterior a la fecha Desde.")

    filas = []
    if not errores and not request.args.get("franja"):
        filas = db.query(
            "SELECT v.*,b.etiqueta AS horario,m.nombre AS materia FROM v_franjas_cupo v "
            "JOIN bloques_horarios b ON b.id_bloque = v.id_bloque JOIN materias m ON m.id_materia = v.id_materia "
            "WHERE v.id_docente = %s AND v.fecha BETWEEN %s AND %s "
            "ORDER BY v.fecha,b.hora_inicio,v.id_franja",
            (tutor["id_docente"], desde, hasta),
        )
    id_franja = reglas.entero(request.args.get("franja"))
    elegida = None
    citas = []
    if request.args.get("franja"):
        elegida = reglas.datos_franja(id_franja)
        if (
            errores
            or not elegida
            or elegida["id_docente"] != tutor["id_docente"]
            or not desde <= elegida["fecha"] <= hasta
        ):
            abort(404)
        citas = reglas.citas(
            "r.id_franja = %s AND f.id_docente = %s", (id_franja, tutor["id_docente"])
        )
    return render_template(
        "tutor/franjas.html",
        filas=filas,
        desde=valor_desde,
        hasta=valor_hasta,
        errores=errores,
        elegida=elegida,
        citas=citas,
    )


def _periodo_de_la_cita(cita):
    fecha = cita["fecha"]
    desde = reglas.fecha(request.args.get("desde"))
    hasta = reglas.fecha(request.args.get("hasta") or desde)
    if desde and hasta and desde <= fecha <= hasta:
        return {"desde": desde.isoformat(), "hasta": request.args.get("hasta") or None}
    return {"desde": fecha.isoformat()}


def _cita(id_reserva, id_docente, bloquear=False):
    consulta = reglas.CONSULTA_CITAS + " WHERE r.id_reserva = %s AND f.id_docente = %s"
    return db.query(
        consulta + (" FOR UPDATE" if bloquear else ""),
        (id_reserva, id_docente),
        one=True,
    )


def _opciones(cita):
    estudiante = db.query(
        "SELECT * FROM estudiantes WHERE id_estudiante=%s",
        (cita["id_estudiante"],),
        one=True,
    )
    franjas = reglas.oferta_estudiante(
        estudiante, cita["id_materia"], cita["id_materia_inscrita"], cita["id_docente"]
    )
    origen = (cita["fecha"], reglas.hora_texto(cita["hora_inicio"]))
    clases = {
        (c["dia"], c["bloque"])
        for c in reglas.calendario_clases("estudiante", cita["id_estudiante"])
    }
    otras = reglas.citas(
        "r.id_estudiante=%s AND r.estado_cita<>'Cancelada' AND f.fecha BETWEEN %s AND %s",
        (cita["id_estudiante"], reglas.hoy(), reglas.semanas()[1][-1]),
    )
    ocupados = {(r["fecha"], r["id_bloque"]) for r in otras}
    opciones = []
    for f in franjas:
        if f["lugares_libres"] <= 0:
            continue
        if (
            (f["fecha"], reglas.hora_texto(f["hora_inicio"])) > origen
            and (f["fecha"], f["id_bloque"]) not in ocupados
            and (reglas.dia(f["fecha"]), f["id_bloque"]) not in clases
        ):
            opciones.append(dict(f, materia=f["materia_asesorada"]))
    return opciones


@bp.route("/acuerdo/<int:id_reserva>", methods=["GET", "POST"])
@rol_requerido(ROL)
def acuerdo(id_reserva):
    tutor = _tutor()
    cita = _cita(id_reserva, tutor["id_docente"])
    if not cita:
        abort(404)
    periodo = _periodo_de_la_cita(cita)
    errores = []
    form = {
        k: request.form.get(k, "").strip()
        for k in ("asistencia", "decision", "descripcion", "franja")
    }
    if request.method == "POST":
        try:
            with db.transaction():
                d = reglas.bloquear_docente(tutor["id_docente"])
                est = reglas.bloquear_estudiante(cita["id_estudiante"])
                actual = _cita(id_reserva, d["id_docente"], bloquear=True)
                if not d["habilitado_tutor"] or d["estado_laboral"] != "Activo":
                    raise reglas.ReglaNegocio("El docente ya no está habilitado.")
                if actual["estado_cita"] != "Programada" or actual["id_acuerdo"]:
                    raise reglas.ReglaNegocio(
                        "La atención guardada es de solo lectura."
                    )
                if form["asistencia"] == "ausente":
                    db.execute(
                        "UPDATE reservas_asesoria SET estado_cita='No asistio' WHERE id_reserva=%s",
                        (id_reserva,),
                    )
                elif form["asistencia"] == "asistio":
                    decision = form["decision"]
                    if decision not in ("cerrar", "seguir"):
                        raise reglas.ReglaNegocio(
                            "Selecciona Cerrado o Agendar seguimiento."
                        )
                    if len(form["descripcion"]) > 10000 or (
                        decision == "seguir" and not form["descripcion"]
                    ):
                        raise reglas.ReglaNegocio(
                            "Para agendar seguimiento escribe el acuerdo. El máximo es de 10000 caracteres."
                        )
                    nueva = None
                    if decision == "seguir":
                        nueva = reglas.datos_franja(
                            reglas.entero(form["franja"]), bloquear=True
                        )
                        reglas.validar_reserva(
                            est, nueva, actual["id_materia_inscrita"],
                            origen=actual, asesorada=actual["id_materia"],
                        )
                    resultado = "En seguimiento" if nueva else "Cerrado"
                    db.execute(
                        "UPDATE reservas_asesoria SET estado_cita='Realizada',resultado_atencion=%s,anotaciones=%s "
                        "WHERE id_reserva=%s",
                        (
                            resultado,
                            None if nueva else (form["descripcion"] or None),
                            id_reserva,
                        ),
                    )
                    if nueva:
                        db.insert(
                            "INSERT INTO acuerdos(id_reserva,descripcion_acuerdo,estado_acuerdo) VALUES(%s,%s,'En seguimiento')",
                            (id_reserva, form["descripcion"]),
                        )
                        db.insert(
                            "INSERT INTO reservas_asesoria(id_franja,id_estudiante,tipo_cita,id_reserva_origen,id_materia_inscrita,id_materia_asesorada) "
                            "VALUES(%s,%s,'Seguimiento',%s,%s,%s)",
                            (
                                nueva["id_franja"],
                                est["id_estudiante"],
                                id_reserva,
                                actual["id_materia_inscrita"],
                                actual["id_materia"],
                            ),
                        )
                else:
                    raise reglas.ReglaNegocio("Selecciona Asistió o No asistió.")
            flash("Atención guardada.", "success")
            return redirect(url_for("tutor.acuerdo", id_reserva=id_reserva, **periodo))
        except (reglas.ReglaNegocio, MySQLError) as e:
            errores.append(db.mensaje_error(e) if isinstance(e, MySQLError) else str(e))
            cita = _cita(id_reserva, tutor["id_docente"])
    opciones = _opciones(cita) if cita["estado_cita"] == "Programada" else []
    regreso = url_for(
        "tutor.franjas", franja=cita["id_franja"], **periodo
    )
    reporte = request.args.get("de") == "reportes"
    if reporte:
        regreso = url_for(
            "tutor.reportes",
            desde=request.args.get("desde"),
            hasta=request.args.get("hasta"),
        )
    return render_template(
        "tutor/acuerdo.html",
        cita=cita,
        form=form,
        opciones=opciones,
        errores=errores,
        regreso=regreso,
        reporte=reporte,
    )


@bp.post("/citas/<int:id_reserva>/cancelar")
@rol_requerido(ROL)
def cancelar(id_reserva):
    tutor = _tutor()
    with db.transaction():
        reglas.bloquear_docente(tutor["id_docente"])
        cita = _cita(id_reserva, tutor["id_docente"], bloquear=True)
        if not cita:
            abort(404)
        if cita["estado_cita"] == "Programada":
            db.execute(
                "UPDATE reservas_asesoria SET estado_cita='Cancelada',motivo_cancelacion='Cancelada por el docente' WHERE id_reserva=%s",
                (id_reserva,),
            )
            ocupados = reglas.reservas_activas(cita["id_franja"])
            cupo = reglas.datos_franja(cita["id_franja"])["cupo_maximo"]
            flash(
                f"Asesoría cancelada. La franja tiene {ocupados} de {cupo} reservas y {cupo - ocupados} lugares libres.",
                "success",
            )
        else:
            flash("La cita ya tiene un resultado registrado.", "warning")
    return redirect(
        url_for(
            "tutor.franjas", franja=cita["id_franja"], **_periodo_de_la_cita(cita)
        )
    )


@bp.route("/disponibilidad", methods=["GET", "POST"])
@rol_requerido(ROL)
def disponibilidad():
    tutor = _tutor()
    docente = tutor["id_docente"]
    desde = reglas.fecha(request.values.get("desde", reglas.hoy().isoformat()))
    hasta = reglas.fecha(request.values.get("hasta") or desde)
    inicio = reglas.hoy()
    fin = reglas.semanas()[1][-1] + timedelta(days=2)
    afectados = []
    franjas = []
    errores = []
    previsualizar = False
    if request.method == "POST":
        try:
            if not desde or not hasta or not inicio <= desde <= hasta <= fin:
                raise reglas.ReglaNegocio(
                    "Elige un día o un rango de la semana actual o la siguiente."
                )
            with db.transaction():
                reglas.bloquear_docente(docente)
                franjas = db.query(
                    "SELECT f.id_franja,f.fecha,m.nombre AS materia,b.etiqueta FROM franjas_asesoria f "
                    "JOIN materias m USING(id_materia) JOIN bloques_horarios b USING(id_bloque) WHERE f.id_docente=%s AND f.fecha BETWEEN %s AND %s "
                    "AND f.estado='Publicada' ORDER BY f.fecha,b.hora_inicio",
                    (docente, desde, hasta),
                )
                afectados = reglas.citas(
                    "f.id_docente=%s AND f.fecha BETWEEN %s AND %s AND r.estado_cita='Programada'",
                    (docente, desde, hasta),
                )
                ids = (
                    ",".join(str(f["id_franja"]) for f in franjas)
                    + "/"
                    + ",".join(str(r["id_reserva"]) for r in afectados)
                )
                if (
                    request.form.get("accion") == "confirmar"
                    and request.form.get("vista") == ids
                ):
                    db.execute(
                        "INSERT INTO bloqueos_asesoria(id_docente,desde,hasta) VALUES(%s,%s,%s) ON DUPLICATE KEY UPDATE hasta=VALUES(hasta)",
                        (docente, desde, hasta),
                    )
                    reglas.cancelar_franjas(
                        docente, reglas.MOTIVO_SUSPENSION_DOCENTE, desde, hasta
                    )
                else:
                    previsualizar = True
                    if request.form.get("accion") == "confirmar":
                        errores.append(
                            "Las reservas cambiaron. Revisa el listado actualizado antes de confirmar."
                        )
            if not previsualizar:
                texto = (
                    reglas.fecha_texto(desde)
                    if desde == hasta
                    else "del "
                    + reglas.fecha_texto(desde)
                    + " al "
                    + reglas.fecha_texto(hasta)
                )
                flash(
                    "Asesorías suspendidas "
                    + texto
                    + ". Citas canceladas: "
                    + str(len(afectados))
                    + ".",
                    "success",
                )
                return redirect(
                    url_for(
                        "tutor.disponibilidad",
                        desde=desde.isoformat(),
                        hasta=hasta.isoformat(),
                    )
                )
        except (reglas.ReglaNegocio, MySQLError) as e:
            errores.append(db.mensaje_error(e) if isinstance(e, MySQLError) else str(e))
    agenda = reglas.calendario_docente(docente)
    dias_suspendidos = set()
    for rango in db.query(
        "SELECT desde,hasta FROM bloqueos_asesoria WHERE id_docente=%s AND desde<=%s AND hasta>=%s",
        (docente, fin, inicio),
    ):
        primero = max(inicio, rango["desde"])
        ultimo = min(fin, rango["hasta"])
        dias_suspendidos.update(
            primero + timedelta(days=i) for i in range((ultimo - primero).days + 1)
        )
    dias_periodo = []
    if desde and hasta and inicio <= desde <= hasta <= fin:
        consulta_franjas = db.query(
            "SELECT f.id_franja,f.fecha,f.estado,f.motivo_cancelacion,m.nombre AS materia,b.etiqueta FROM franjas_asesoria f "
            "JOIN materias m USING(id_materia) JOIN bloques_horarios b USING(id_bloque) "
            "WHERE f.id_docente=%s AND f.fecha BETWEEN %s AND %s AND (f.estado='Publicada' OR f.motivo_cancelacion IN (%s,%s)) "
            "ORDER BY f.fecha,b.hora_inicio,f.id_franja",
            (docente, desde, hasta, reglas.MOTIVO_SUSPENSION_DOCENTE, reglas.MOTIVO_SUSPENSION_NO_RESTABLECIDA),
        )
        reservas = reglas.citas(
            "f.id_docente=%s AND f.fecha BETWEEN %s AND %s AND "
            "(r.estado_cita='Programada' OR (r.estado_cita='Cancelada' AND r.motivo_cancelacion IN (%s,%s)))",
            (docente, desde, hasta, reglas.MOTIVO_SUSPENSION_DOCENTE, reglas.MOTIVO_SUSPENSION_NO_RESTABLECIDA),
        )
        if previsualizar:
            consulta_franjas, reservas = franjas, afectados
        for indice in range((hasta - desde).days + 1):
            dia = desde + timedelta(days=indice)
            bloques = []
            for f in consulta_franjas:
                if f["fecha"] == dia:
                    bloques.append(
                        dict(
                            f,
                            restablecible=(
                                dia in dias_suspendidos
                                and f.get("motivo_cancelacion") == reglas.MOTIVO_SUSPENSION_DOCENTE
                            ),
                            alumnos=[
                                a for a in reservas if a["id_franja"] == f["id_franja"]
                            ],
                        )
                    )
            dias_periodo.append({"fecha": dia, "bloques": bloques})
    return render_template(
        "tutor/disponibilidad.html",
        agenda=agenda,
        desde=desde,
        hasta=hasta,
        fin=fin,
        inicio=inicio,
        franjas=franjas,
        afectados=afectados,
        dias_periodo=dias_periodo,
        dias_suspendidos=sorted(dias_suspendidos),
        suspension_no_restablecida=reglas.MOTIVO_SUSPENSION_NO_RESTABLECIDA,
        total_estudiantes=len({r["id_estudiante"] for r in afectados}),
        errores=errores,
        preview=previsualizar,
        vista=ids if previsualizar else "",
    )


@bp.post("/disponibilidad/restablecer")
@rol_requerido(ROL)
def restablecer_disponibilidad():
    docente = _tutor()["id_docente"]
    fecha = reglas.fecha(request.form.get("fecha"))
    fin = reglas.semanas()[1][-1] + timedelta(days=2)
    if not fecha or not reglas.hoy() <= fecha <= fin:
        flash("Elige una fecha vigente para restablecer.", "warning")
        return redirect(url_for("tutor.disponibilidad"))

    try:
        with db.transaction():
            tutor = reglas.bloquear_docente(docente)
            if not tutor["habilitado_tutor"] or tutor["estado_laboral"] != "Activo":
                abort(403)
            franjas, sin_publicar, citas, sin_restaurar = reglas.restablecer_dia_docente(docente, fecha)
    except (reglas.ReglaNegocio, MySQLError) as error:
        flash(db.mensaje_error(error) if isinstance(error, MySQLError) else str(error), "warning")
    else:
        resumen = f"Disponibilidad restablecida para el {reglas.fecha_texto(fecha)}. Franjas: {franjas}. Citas: {citas}."
        if sin_publicar or sin_restaurar:
            resumen += f" Quedaron canceladas por disponibilidad o por conflicto: {sin_publicar} franjas y {sin_restaurar} citas."
        flash(resumen, "warning" if sin_publicar or sin_restaurar else "success")
    return redirect(url_for("tutor.disponibilidad", desde=fecha.isoformat()))


# Vista inicial de reporte de asesorias impartidas
@bp.get("/reportes")
@rol_requerido(ROL)
def reportes():
    tutor = _tutor()
    errores = []
    filas = []
    try:
        desde, hasta = reglas.rango_reporte(request.args)
        filas = reglas.citas(
            "f.id_docente = %s AND f.fecha >= %s AND f.fecha <= %s",
            (tutor["id_docente"], desde, hasta),
        )
        desde, hasta = desde.isoformat(), hasta.isoformat()
    except reglas.ReglaNegocio as error:
        errores.append(str(error))
        desde = request.args.get("desde", "")
        hasta = request.args.get("hasta", "")
    return render_template(
        "tutor/reportes.html", filas=filas, desde=desde, hasta=hasta, errores=errores
    )
