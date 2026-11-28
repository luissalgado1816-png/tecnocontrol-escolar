from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from pymysql import MySQLError
from auth import rol_requerido
import db
import reglas

bp = Blueprint("estudiante", __name__, url_prefix="/estudiante")
ROL = "consulta_seguimiento_est"
MOTIVOS_CANCELACION_DOCENTE = (
    reglas.MOTIVO_SUSPENSION_DOCENTE,
    reglas.MOTIVO_SUSPENSION_NO_RESTABLECIDA,
    "Cancelada por el docente",
)


def _estudiante():
    estudiante = db.query(
        "SELECT * FROM estudiantes WHERE id_usuario = %s",
        (g.user["id_usuario"],),
        one=True,
    )
    if not estudiante:
        abort(403)
    return estudiante


def _avisar_franja_cancelada(franja):
    session["franja_cancelada"] = {
        "fecha": franja["fecha"].isoformat(),
        "bloque": franja["id_bloque"],
    }


@bp.get("/reservar")
@rol_requerido(ROL)
def reservar():
    estudiante = _estudiante()
    id_est = estudiante["id_estudiante"]
    opciones = db.query(
        "SELECT v.id_materia_inscrita,v.id_materia,m.nombre FROM v_materias_asesoria_estudiante v "
        "JOIN materias m USING(id_materia) WHERE v.id_estudiante=%s ORDER BY m.nombre",
        (id_est,),
    )
    materias = [m for m in opciones if m["id_materia"] == m["id_materia_inscrita"]]
    seleccion = reglas.entero(request.args.get("materia"))
    if seleccion not in {m["id_materia"] for m in materias}:
        seleccion = None
    alternativas = [m for m in opciones if m["id_materia_inscrita"] == seleccion]
    asesorada = reglas.entero(request.args.get("asesoria"))
    if asesorada not in {m["id_materia"] for m in alternativas}:
        asesorada = seleccion
    publicadas = reglas.oferta_estudiante(
        estudiante,
        asesorada,
        seleccion,
        incluir_pasadas=True,
        incluir_suspendidas=estudiante["estado"] == "Inscrito",
    )
    semana_actual, semana_siguiente = reglas.semanas()
    fechas = (semana_actual[0], semana_siguiente[-1])
    agenda = reglas.calendario_base()
    agenda["semana"] = int(request.args.get("semana") == "1")
    agenda["franja_cancelada"] = session.pop("franja_cancelada", None)
    agenda["clases"] = reglas.calendario_clases("estudiante", id_est)
    agenda["oferta"] = [
        {
            "id": f["id_franja"],
            "fecha": f["fecha"].isoformat(),
            "bloque": f["id_bloque"],
            "materia": f["materia_asesorada"],
            "docente": f["docente"],
            "cupo": f["cupo_maximo"],
            "libres": int(f["lugares_libres"]),
            "pasada": not reglas.futura(f["fecha"], f["hora_inicio"]),
            "suspendida": f["estado"] == "Cancelada",
            "horario": f["horario"],
            "url": url_for(
                "estudiante.confirmar",
                id_franja=f["id_franja"],
                inscrita=seleccion,
                asesoria=asesorada if asesorada != f["id_materia"] else None,
            ),
        }
        for f in publicadas
    ]
    citas = reglas.citas(
        "r.id_estudiante=%s AND f.fecha BETWEEN %s AND %s",
        (id_est, *fechas),
    )
    agenda["citas"] = [
        {
            "id": r["id_reserva"],
            "id_franja": r["id_franja"],
            "fecha": r["fecha"].isoformat(),
            "bloque": r["id_bloque"],
            "materia": r["materia"],
            "estado": r["estado_cita"],
            "futura": reglas.futura(r["fecha"], r["hora_inicio"]),
            "cancelada_por_docente": r["estado_cita"] == "Cancelada"
            and r["motivo_cancelacion"] in MOTIVOS_CANCELACION_DOCENTE,
            "tipo": r["tipo_cita"],
            "confirmada": bool(r["confirmada"]),
        }
        for r in citas
    ]
    return render_template(
        "estudiante/reservar.html",
        estudiante=estudiante,
        materias=materias,
        seleccion=seleccion,
        asesorada=asesorada,
        alternativas=alternativas,
        agenda=agenda,
        citas=citas,
        abierta=bool(asesorada and reglas.cita_abierta(id_est, asesorada)),
        futura=reglas.futura,
    )


@bp.route("/reservar/<int:id_franja>", methods=["GET", "POST"])
@rol_requerido(ROL)
def confirmar(id_franja):
    estudiante = _estudiante()
    f = reglas.datos_franja(id_franja)
    if not f:
        abort(404)
    inscrita = reglas.entero(request.values.get("inscrita")) or f["id_materia"]
    asesorada = reglas.entero(request.values.get("asesoria", f["id_materia"]))
    if asesorada is None:
        abort(400)
    regreso = url_for(
        "estudiante.reservar",
        materia=inscrita,
        asesoria=asesorada,
        semana=int(f["fecha"] >= reglas.semanas()[1][0]),
    )
    try:
        if request.method == "POST":
            with db.transaction():
                reglas.bloquear_docente(f["id_docente"])
                estudiante = reglas.bloquear_estudiante(estudiante["id_estudiante"])
                f = reglas.datos_franja(id_franja, bloquear=True)
                acepta = request.form.get("aceptar_cruce") == "1"
                reglas.validar_reserva(
                    estudiante, f, inscrita, aceptar_cruce=acepta, asesorada=asesorada
                )
                cruce = bool(reglas.clase_estudiante(estudiante["id_estudiante"], f))
                db.insert(
                    "INSERT INTO reservas_asesoria(id_franja,id_estudiante,id_materia_inscrita,id_materia_asesorada,cruce_aceptado,tipo_cita,estado_cita) "
                    "VALUES(%s,%s,%s,%s,%s,'Inicial','Programada')",
                    (
                        id_franja,
                        estudiante["id_estudiante"],
                        inscrita,
                        asesorada,
                        int(cruce and acepta),
                    ),
                )
            flash("Asesoría programada. Tu lugar quedó apartado.", "success")
            return redirect(regreso)
        libres = reglas.validar_reserva(
            estudiante, f, inscrita, aceptar_cruce=True, asesorada=asesorada
        )
    except (reglas.ReglaNegocio, MySQLError) as e:
        if isinstance(e, reglas.ReglaNegocio) and f and f["estado"] == "Cancelada":
            _avisar_franja_cancelada(f)
        else:
            flash(db.mensaje_error(e) if isinstance(e, MySQLError) else str(e), "warning")
        return redirect(regreso)
    return render_template(
        "estudiante/confirmar.html",
        franja=f,
        libres=libres,
        inscrita=inscrita,
        asesorada=asesorada,
        materia_asesorada=db.query(
            "SELECT nombre FROM materias WHERE id_materia=%s", (asesorada,), one=True
        )["nombre"],
        cruce=reglas.clase_estudiante(estudiante["id_estudiante"], f),
        regreso=regreso,
    )


@bp.post("/citas/<int:id_reserva>")
@rol_requerido(ROL)
def cita_estado(id_reserva):
    estudiante = _estudiante()
    condicion = "r.id_reserva=%s AND r.id_estudiante=%s"
    params = (id_reserva, estudiante["id_estudiante"])
    fila = db.query(reglas.CONSULTA_CITAS + " WHERE " + condicion, params, one=True)
    if not fila:
        abort(404)
    accion = request.form.get("accion")
    actual = None
    try:
        with db.transaction():
            reglas.bloquear_docente(fila["id_docente"])
            reglas.bloquear_estudiante(estudiante["id_estudiante"])
            actual = db.query(
                reglas.CONSULTA_CITAS + " WHERE " + condicion + " FOR UPDATE",
                params,
                one=True,
            )
            if actual["estado_cita"] != "Programada" or not reglas.futura(
                actual["fecha"], actual["hora_inicio"]
            ):
                raise reglas.ReglaNegocio(
                    "Solo puedes confirmar o cancelar una cita programada antes de su hora de inicio."
                )
            if accion == "confirmar":
                db.execute(
                    "UPDATE reservas_asesoria SET confirmada=1 WHERE id_reserva=%s",
                    (id_reserva,),
                )
            elif accion == "cancelar":
                db.execute(
                    "UPDATE reservas_asesoria SET estado_cita='Cancelada',motivo_cancelacion='Cancelada por el estudiante' WHERE id_reserva=%s",
                    (id_reserva,),
                )
            else:
                abort(400)
        flash(
            "Asistencia confirmada."
            if accion == "confirmar"
            else "Asesoría cancelada. El lugar quedó disponible.",
            "success",
        )
    except (reglas.ReglaNegocio, MySQLError) as e:
        if (
            actual
            and actual["estado_cita"] == "Cancelada"
            and actual["motivo_cancelacion"] in MOTIVOS_CANCELACION_DOCENTE
        ):
            _avisar_franja_cancelada(actual)
        else:
            flash(db.mensaje_error(e) if isinstance(e, MySQLError) else str(e), "warning")
    return redirect(
        url_for(
            "estudiante.reservar",
            materia=fila["id_materia_inscrita"],
            asesoria=fila["id_materia"],
            semana=int(fila["fecha"] >= reglas.semanas()[1][0]),
        )
    )


@bp.get("/historial")
@rol_requerido(ROL)
def historial():
    estudiante = _estudiante()
    filas = reglas.citas("r.id_estudiante=%s", (estudiante["id_estudiante"],))
    grupo_por_cita = {
        cita["id_reserva"]: grupo
        for grupo in reglas.recorridos(filas)
        for cita in grupo
    }
    return render_template(
        "estudiante/historial.html", filas=filas, grupo_por_cita=grupo_por_cita
    )
