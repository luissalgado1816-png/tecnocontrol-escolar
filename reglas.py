# Reglas compartidas de validacion y coherencia de datos (Modulos 2, 3, 4 y 5)
from datetime import date, datetime, timedelta
import re
import db

DIAS = ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes')
MOTIVO_SUSPENSION_DOCENTE = "Suspensión del docente"
MOTIVO_SUSPENSION_NO_RESTABLECIDA = "Suspensión del docente · no restablecida"

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
        "SELECT f.fecha, f.id_bloque, f.id_carrera, r.id_materia_inscrita AS id_materia, r.cruce_aceptado FROM reservas_asesoria r "
        "JOIN franjas_asesoria f ON f.id_franja = r.id_franja "
        "WHERE r.id_estudiante = %s AND r.estado_cita = 'Programada' "
        "AND f.estado = 'Publicada' AND f.fecha >= %s FOR UPDATE",
        (actual['id_estudiante'], hoy()),
    )
    materias = {f['materia'] for f in filas}
    ocupados = {(f['dia'], f['bloque']) for f in filas}
    for cita in pendientes:
        if (cita['id_carrera'] != form['id_carrera'] or cita['id_materia'] not in materias
                or (not cita['cruce_aceptado'] and (dia(cita['fecha']), cita['id_bloque']) in ocupados)):
            raise ReglaNegocio('El cambio afecta una asesoría programada. Conserva su carrera, materia y horario compatible antes de guardar.')

# Verifica coherencia de departamento y no traslape con franjas publicadas (RN-09)
def validar_edicion_docente(actual, form, filas):
    if form['estado_laboral'] != 'Activo':
        return
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
def semanas():
    lunes = hoy() - timedelta(days=hoy().weekday())
    return [[lunes + timedelta(days=offset + dia) for dia in range(5)] for offset in (0, 7)]


def dentro_de_oferta(f):
    dias = semanas()
    return f is not None and hoy() <= f <= dias[1][-1] and f.weekday() < 5


def futura(f, hora):
    return f > hoy() or (f == hoy() and hora_texto(hora) > ahora().strftime("%H:%M"))


def nivel(grado):
    return {"Ing.": 1, "Mtro.": 2, "Mtra.": 2, "Dr.": 3, "Dra.": 3}.get(grado, 0)


def opciones_franja(id_docente, id_carrera, dia_fecha, bloquear=False, *, incluir_previas=False):
    materias = db.query(
        "SELECT DISTINCT m.id_materia,m.nombre FROM v_materias_elegibles_tutor e "
        "JOIN tutor_materias tm USING(id_docente,id_materia) JOIN materias m USING(id_materia) "
        "JOIN docentes d USING(id_docente) JOIN carreras c ON c.id_carrera=e.id_carrera "
        "WHERE e.id_docente=%s AND e.id_carrera=%s AND tm.autorizada=1 AND d.habilitado_tutor=1 AND c.activa=1 "
        "AND (%s OR EXISTS (SELECT 1 FROM v_horario_docente_actual h "
        "WHERE h.id_docente=e.id_docente AND h.id_carrera=e.id_carrera AND h.id_materia=e.id_materia)) "
        "ORDER BY m.nombre",
        (id_docente, id_carrera, incluir_previas),
    )
    if not dentro_de_oferta(dia_fecha):
        return materias, [], "Elige un día hábil de la semana actual o la siguiente."
    if db.query(
        "SELECT 1 FROM bloqueos_asesoria WHERE id_docente=%s AND %s BETWEEN desde AND hasta",
        (id_docente, dia_fecha),
        one=True,
    ):
        return materias, [], "El docente suspendió las asesorías en esta fecha."
    ocupados = db.query(
        "SELECT id_bloque FROM v_horario_docente_actual WHERE id_docente=%s AND dia_semana=%s "
        "UNION SELECT id_bloque FROM franjas_asesoria WHERE id_docente=%s AND fecha=%s AND estado='Publicada'",
        (id_docente, dia(dia_fecha), id_docente, dia_fecha),
    )
    ids = {f["id_bloque"] for f in ocupados}
    bloques = [
        b
        for b in bloques_horarios()
        if b["id_bloque"] not in ids and futura(dia_fecha, b["hora_inicio"])
    ]
    return materias, bloques, "El bloque ya está ocupado o dejó de estar disponible."


def bloques_horarios():
    return db.query(
        "SELECT id_bloque,etiqueta,hora_inicio FROM bloques_horarios ORDER BY hora_inicio"
    )


def cancelar_franjas(
    id_docente, motivo, desde=None, hasta=None, materia=None, carrera=None
):
    """El llamador ya tiene el bloqueo del tutor. El acuerdo y su cadena quedan en el historial."""
    filtros = ["f.id_docente=%s", "f.estado='Publicada'"]
    parametros = [id_docente]
    for condicion, valor in [
        ("f.fecha>=%s", desde),
        ("f.fecha<=%s", hasta),
        ("f.id_materia=%s", materia),
        ("f.id_carrera=%s", carrera),
    ]:
        if valor is not None:
            filtros.append(condicion)
            parametros.append(valor)
    donde = " AND ".join(filtros)
    db.execute(
        "UPDATE reservas_asesoria r JOIN franjas_asesoria f USING(id_franja) "
        "SET r.estado_cita='Cancelada', r.motivo_cancelacion=%s WHERE r.estado_cita='Programada' AND "
        + donde,
        (motivo, *parametros),
    )
    # Las franjas históricas ya impartidas conservan su estado.
    db.execute(
        "UPDATE franjas_asesoria f SET estado='Cancelada',motivo_cancelacion=%s WHERE "
        + donde
        + " AND f.fecha>=%s",
        (motivo, *parametros, hoy()),
    )


def restablecer_dia_docente(id_docente, dia_fecha):
    """Quita un día de la suspensión y recupera las citas que aún se pueden atender."""
    rangos = db.query(
        "SELECT id_bloqueo,desde,hasta FROM bloqueos_asesoria "
        "WHERE id_docente=%s AND %s BETWEEN desde AND hasta FOR UPDATE",
        (id_docente, dia_fecha),
    )
    if not rangos:
        raise ReglaNegocio("La fecha ya está disponible.")

    franjas = db.query(
        "SELECT f.*,b.hora_inicio FROM franjas_asesoria f JOIN bloques_horarios b USING(id_bloque) "
        "WHERE f.id_docente=%s AND f.fecha=%s AND f.estado='Cancelada' "
        "AND f.motivo_cancelacion=%s ORDER BY b.hora_inicio,f.id_franja",
        (id_docente, dia_fecha, MOTIVO_SUSPENSION_DOCENTE),
    )
    franjas = [f for f in franjas if futura(dia_fecha, f["hora_inicio"])]
    ids = {f["id_franja"] for f in franjas}
    candidatas = {id_franja: [] for id_franja in ids}
    for r in citas(
        "f.id_docente=%s AND f.fecha=%s AND r.estado_cita='Cancelada' "
        "AND r.motivo_cancelacion=%s",
        (id_docente, dia_fecha, MOTIVO_SUSPENSION_DOCENTE),
    ):
        if r["id_franja"] in ids:
            candidatas[r["id_franja"]].append(r)
    estudiantes = {
        id_estudiante: bloquear_estudiante(id_estudiante)
        for id_estudiante in sorted({
            r["id_estudiante"] for filas in candidatas.values() for r in filas
        })
    }

    for rango in rangos:
        db.execute("DELETE FROM bloqueos_asesoria WHERE id_bloqueo=%s", (rango["id_bloqueo"],))
    for rango in rangos:
        for desde, hasta in (
            (rango["desde"], dia_fecha - timedelta(days=1)),
            (dia_fecha + timedelta(days=1), rango["hasta"]),
        ):
            if desde <= hasta:
                db.execute(
                    "INSERT INTO bloqueos_asesoria(id_docente,desde,hasta) VALUES(%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE id_bloqueo=id_bloqueo",
                    (id_docente, desde, hasta),
                )

    publicadas = recuperadas = omitidas = 0
    for franja in franjas:
        # La franja ya existía, incluso si se publicó con las reglas anteriores.
        materias, bloques, _ = opciones_franja(
            id_docente, franja["id_carrera"], dia_fecha, incluir_previas=True
        )
        disponible = (
            franja["id_materia"] in {m["id_materia"] for m in materias}
            and franja["id_bloque"] in {b["id_bloque"] for b in bloques}
        )
        id_franja = franja["id_franja"]
        if disponible:
            db.execute(
                "UPDATE franjas_asesoria SET estado='Publicada',motivo_cancelacion=NULL WHERE id_franja=%s",
                (id_franja,),
            )
            franja["estado"] = "Publicada"
            publicadas += 1
        else:
            db.execute(
                "UPDATE franjas_asesoria SET motivo_cancelacion=%s WHERE id_franja=%s",
                (MOTIVO_SUSPENSION_NO_RESTABLECIDA, id_franja),
            )

        for r in candidatas[id_franja]:
            try:
                if not disponible:
                    raise ReglaNegocio("La franja ya no se puede publicar.")
                origen = None
                if r["tipo_cita"] == "Seguimiento":
                    anteriores = citas("r.id_reserva=%s AND r.estado_cita='Realizada'", (r["id_reserva_origen"],))
                    if not anteriores:
                        raise ReglaNegocio("El seguimiento ya no tiene una atención de origen.")
                    origen = anteriores[0]
                validar_reserva(
                    estudiantes[r["id_estudiante"]],
                    franja,
                    r["id_materia_inscrita"] or franja["id_materia"],
                    aceptar_cruce=bool(r["cruce_aceptado"]),
                    origen=origen,
                    asesorada=r["id_materia"],
                )
            except ReglaNegocio:
                db.execute(
                    "UPDATE reservas_asesoria SET motivo_cancelacion=%s WHERE id_reserva=%s",
                    (MOTIVO_SUSPENSION_NO_RESTABLECIDA, r["id_reserva"]),
                )
                omitidas += 1
            else:
                db.execute(
                    "UPDATE reservas_asesoria SET estado_cita='Programada',motivo_cancelacion=NULL WHERE id_reserva=%s",
                    (r["id_reserva"],),
                )
                recuperadas += 1
    return publicadas, len(franjas) - publicadas, recuperadas, omitidas


# Obtiene el rango del reporte y valida que Desde no sea posterior a Hasta
def rango_reporte(args):
    # Si no se eligieron fechas, usa el primer y ultimo dia del mes actual.
    inicio_mes = hoy().replace(day=1)
    siguiente = (inicio_mes.replace(day=28) + timedelta(days=4)).replace(day=1)
    desde = fecha(args.get("desde", inicio_mes.isoformat()))
    hasta = fecha(args.get("hasta", (siguiente - timedelta(days=1)).isoformat()))
    if not desde or not hasta or desde > hasta:
        raise ReglaNegocio(
            "Selecciona un rango de fechas válido: Desde no puede ser posterior a Hasta."
        )
    return desde, hasta


# Consulta compartida del historial, acuerdos y cita de seguimiento vinculada
# Modulo 5: incluye el estado del seguimiento para mostrar su situacion actual.
CONSULTA_CITAS = """
 SELECT r.id_reserva, r.id_franja, r.id_estudiante, r.tipo_cita, r.id_reserva_origen, r.estado_cita,
 r.confirmada,r.cruce_aceptado,r.id_materia_inscrita,r.motivo_cancelacion,r.resultado_atencion,
 e.matricula, CONCAT_WS(' ', e.nombres, e.apellido_paterno, e.apellido_materno) AS estudiante,
 f.fecha, f.id_docente, f.id_carrera, m.id_materia, f.id_bloque, b.etiqueta AS horario, b.hora_inicio,
 c.nombre AS carrera, m.nombre AS materia,
 CONCAT_WS(' ', d.nombres, d.apellido_paterno, d.apellido_materno) AS docente,
 a.id_acuerdo, COALESCE(a.descripcion_acuerdo,r.anotaciones) AS descripcion_acuerdo,
 COALESCE(a.estado_acuerdo,r.resultado_atencion) AS estado_acuerdo,
 s.id_reserva AS siguiente_id, s.estado_cita AS siguiente_estado,s.confirmada AS siguiente_confirmada,
 sf.fecha AS siguiente_fecha, sb.etiqueta AS siguiente_horario
 FROM reservas_asesoria r
 JOIN estudiantes e ON e.id_estudiante = r.id_estudiante
 JOIN franjas_asesoria f ON f.id_franja = r.id_franja
 JOIN bloques_horarios b ON b.id_bloque = f.id_bloque
 JOIN carreras c ON c.id_carrera = f.id_carrera
 JOIN materias m ON m.id_materia = COALESCE(r.id_materia_asesorada, f.id_materia)
 JOIN docentes d ON d.id_docente = f.id_docente
 LEFT JOIN acuerdos a ON a.id_reserva = r.id_reserva
 LEFT JOIN reservas_asesoria s ON s.id_reserva_origen = r.id_reserva
 LEFT JOIN franjas_asesoria sf ON sf.id_franja = s.id_franja
 LEFT JOIN bloques_horarios sb ON sb.id_bloque = sf.id_bloque
"""


# Consulta historiales y reportes con condiciones internas y valores parametrizados
def citas(where, params):
    return db.query(
        CONSULTA_CITAS
        + " WHERE "
        + where
        + " ORDER BY f.fecha, b.hora_inicio, e.matricula",
        params,
    )


# Reservas y oferta de asesorias del estudiante (Modulo 4)
# La oferta informa; la confirmacion vuelve a comprobar los datos antes de guardar.
# Texto SQL compartido para consultar franja, tutor, materia, carrera y horario.
CONSULTA_FRANJA = """
 SELECT f.*, {cupo} b.etiqueta AS horario, b.hora_inicio, c.nombre AS carrera, c.activa AS carrera_activa,
 m.nombre AS materia, m.id_departamento AS departamento_materia,
 d.id_departamento AS departamento_docente, d.habilitado_tutor, d.estado_laboral,
 CONCAT_WS(' ',d.nombres,d.apellido_paterno,d.apellido_materno) AS docente
 FROM franjas_asesoria f JOIN bloques_horarios b ON b.id_bloque = f.id_bloque
 JOIN carreras c ON c.id_carrera = f.id_carrera JOIN materias m ON m.id_materia = f.id_materia
 JOIN docentes d ON d.id_docente = f.id_docente
"""


# Obtiene los datos de una franja y permite bloquearla durante la confirmacion
def datos_franja(id_franja, bloquear=False):
    return db.query(
        CONSULTA_FRANJA.format(cupo="")
        + " WHERE f.id_franja = %s"
        + (" FOR UPDATE" if bloquear else ""),
        (id_franja,),
        one=True,
    )


# Cuenta las reservas que ocupan un lugar en la franja
def reservas_activas(id_franja, bloquear=False):
    # Al confirmar, FOR UPDATE permite leer y bloquear las reservas actuales.
    return len(
        db.query(
            "SELECT id_reserva FROM reservas_asesoria WHERE id_franja = %s "
            "AND estado_cita <> 'Cancelada'" + (" FOR UPDATE" if bloquear else ""),
            (id_franja,),
        )
    )


# Valida elegibilidad, carrera, carga, horarios, duplicados y cupo de una reserva
def oferta_estudiante(
    estudiante, id_materia, inscrita, id_docente=None, *,
    incluir_pasadas=False, incluir_suspendidas=False
):
    if not id_materia or not inscrita:
        return []
    semana_actual, semana_siguiente = semanas()
    sql = (
        CONSULTA_FRANJA.format(cupo="cupo.lugares_libres, asesorada.nombre AS materia_asesorada,")
        + """
      JOIN v_materias_asesorables_franja alcance ON alcance.id_franja=f.id_franja
      JOIN v_materias_asesoria_estudiante elegida ON elegida.id_estudiante=%s
        AND elegida.id_materia=alcance.id_materia AND elegida.id_materia_inscrita=%s
      JOIN materias asesorada ON asesorada.id_materia=elegida.id_materia
      JOIN v_franjas_cupo cupo ON cupo.id_franja=f.id_franja
      WHERE f.id_carrera=%s AND alcance.id_materia=%s AND c.activa=1
        AND f.fecha BETWEEN %s AND %s
        AND (
          (f.estado='Publicada' AND NOT EXISTS (
            SELECT 1 FROM bloqueos_asesoria bl
            WHERE bl.id_docente=f.id_docente AND f.fecha BETWEEN bl.desde AND bl.hasta
          ))
          OR (%s AND f.estado='Cancelada' AND f.motivo_cancelacion=%s)
        )
    """
    )
    params = [
        estudiante["id_estudiante"],
        inscrita,
        estudiante["id_carrera"],
        id_materia,
        semana_actual[0] if incluir_pasadas else hoy(),
        semana_siguiente[-1],
        incluir_suspendidas,
        MOTIVO_SUSPENSION_DOCENTE,
    ]
    if id_docente is not None:
        sql += " AND f.id_docente=%s"
        params.append(id_docente)
    return [
        f
        for f in db.query(
            sql + " ORDER BY f.fecha,b.hora_inicio,docente", tuple(params)
        )
        if incluir_pasadas or futura(f["fecha"], f["hora_inicio"])
    ]


def clase_estudiante(id_estudiante, franja):
    return db.query(
        "SELECT h.id_horario_est, m.nombre AS materia FROM v_horario_estudiante_actual h "
        "JOIN materias m USING(id_materia) "
        "WHERE id_estudiante=%s AND dia_semana=%s AND id_bloque=%s",
        (id_estudiante, dia(franja["fecha"]), franja["id_bloque"]),
        one=True,
    )


def cita_abierta(id_estudiante, id_materia, excepto=None):
    return db.query(
        "SELECT r.id_reserva FROM reservas_asesoria r JOIN franjas_asesoria f USING(id_franja) "
        "WHERE r.id_estudiante=%s AND COALESCE(r.id_materia_asesorada,f.id_materia)=%s "
        "AND r.estado_cita='Programada' "
        "AND r.id_reserva<>%s LIMIT 1",
        (id_estudiante, id_materia, excepto or 0),
        one=True,
    )


def validar_reserva(estudiante, franja, inscrita, aceptar_cruce=False, origen=None, *, asesorada=None):
    if not franja or franja["estado"] != "Publicada":
        raise ReglaNegocio("Esta asesoría fue cancelada. Selecciona otra franja.")
    if estudiante["estado"] != "Inscrito":
        raise ReglaNegocio("Solo un estudiante inscrito puede reservar.")
    if not dentro_de_oferta(franja["fecha"]) or not futura(
        franja["fecha"], franja["hora_inicio"]
    ):
        raise ReglaNegocio("Elige una franja futura de esta semana o la siguiente.")
    asesorada = asesorada or franja["id_materia"]
    if not any(
        f["id_franja"] == franja["id_franja"]
        for f in oferta_estudiante(
            estudiante, asesorada, inscrita, franja["id_docente"]
        )
    ):
        raise ReglaNegocio(
            "La materia o la franja ya no están disponibles. Selecciona otra."
        )
    libres = franja["cupo_maximo"] - reservas_activas(franja["id_franja"])
    if libres <= 0:
        raise ReglaNegocio("Esta franja ya no tiene cupo.")
    if origen and (
        franja["id_docente"] != origen["id_docente"]
        or asesorada != origen["id_materia"]
        or (franja["fecha"], hora_texto(franja["hora_inicio"]))
        <= (origen["fecha"], hora_texto(origen["hora_inicio"]))
    ):
        raise ReglaNegocio("Selecciona una franja posterior del mismo tutor y materia.")
    if db.query(
        "SELECT r.id_reserva FROM reservas_asesoria r JOIN franjas_asesoria f USING(id_franja) "
        "WHERE r.id_estudiante=%s AND f.fecha=%s AND f.id_bloque=%s AND r.estado_cita<>'Cancelada' LIMIT 1",
        (estudiante["id_estudiante"], franja["fecha"], franja["id_bloque"]),
        one=True,
    ):
        raise ReglaNegocio("Ya tienes una asesoría en ese horario.")
    if cita_abierta(
        estudiante["id_estudiante"],
        asesorada,
        origen["id_reserva"] if origen else None,
    ):
        raise ReglaNegocio(
            "Ya tienes una asesoría abierta o en seguimiento de esta materia."
        )
    if clase_estudiante(estudiante["id_estudiante"], franja) and (
        origen or not aceptar_cruce
    ):
        raise ReglaNegocio(
            "La asesoría coincide con una clase. Para reservarla debes aceptar el cruce bajo tu responsabilidad."
        )
    return libres


def recorridos(filas):
    """Agrupa cada cita inicial con sus seguimientos, incluso cuando un resultado está cancelado."""
    por_id = {r["id_reserva"]: r for r in filas}
    grupos = {}
    for r in filas:
        raiz = r
        while raiz["id_reserva_origen"] in por_id:
            raiz = por_id[raiz["id_reserva_origen"]]
        grupos.setdefault(raiz["id_reserva"], []).append(r)
    return list(grupos.values())


def sincronizar_perfil(id_docente):
    permitidas = {
        (r["id_carrera"], r["id_materia"])
        for r in db.query(
            "SELECT id_carrera,id_materia FROM v_materias_elegibles_tutor WHERE id_docente=%s",
            (id_docente,),
        )
    }
    materias = {m for _, m in permitidas}
    for fila in db.query(
        "SELECT id_materia FROM tutor_materias WHERE id_docente=%s AND autorizada=1",
        (id_docente,),
    ):
        if fila["id_materia"] not in materias:
            db.execute(
                "UPDATE tutor_materias SET autorizada=0 WHERE id_docente=%s AND id_materia=%s",
                (id_docente, fila["id_materia"]),
            )
    for f in db.query(
        "SELECT DISTINCT id_carrera,id_materia FROM franjas_asesoria WHERE id_docente=%s AND estado='Publicada'",
        (id_docente,),
    ):
        if (f["id_carrera"], f["id_materia"]) not in permitidas:
            cancelar_franjas(
                id_docente,
                "Cambio de carga académica",
                materia=f["id_materia"],
                carrera=f["id_carrera"],
            )
    if not db.query(
        "SELECT 1 FROM tutor_materias WHERE id_docente=%s AND autorizada=1 LIMIT 1",
        (id_docente,),
        one=True,
    ):
        db.execute(
            "UPDATE docentes SET habilitado_tutor=0 WHERE id_docente=%s", (id_docente,)
        )


def calendario_base():
    return {
        "semanas": [
            [
                {
                    "nombre": dia(f),
                    "fecha": f.isoformat(),
                    "corta": f.strftime("%d/%m"),
                    "etiqueta": dia(f) + " " + f.strftime("%d/%m"),
                }
                for f in semana
            ]
            for semana in semanas()
        ],
        "bloques": [
            {
                "id": b["id_bloque"],
                "etiqueta": b["etiqueta"],
                "hora": hora_texto(b["hora_inicio"]),
            }
            for b in bloques_horarios()
        ],
        "hoy": hoy().isoformat(),
        "hora": ahora().strftime("%H:%M"),
    }


def calendario_clases(persona, id_persona):
    tablas = {
        "docente": ("v_horario_docente_actual", "id_docente"),
        "estudiante": ("v_horario_estudiante_actual", "id_estudiante"),
    }
    tabla, campo = tablas[persona]
    return db.query(
        "SELECT h.dia_semana AS dia,h.id_bloque AS bloque,m.nombre AS materia FROM "
        + tabla
        + " h JOIN materias m USING(id_materia) WHERE h."
        + campo
        + "=%s",
        (id_persona,),
    )


def calendario_docente(id_docente):
    datos = calendario_base()
    desde, hasta = semanas()[0][0], semanas()[1][-1]
    datos["clases"] = calendario_clases("docente", id_docente)
    datos["franjas"] = db.query(
        """SELECT v.id_franja AS id,DATE_FORMAT(v.fecha,'%%Y-%%m-%%d') AS fecha,v.id_bloque AS bloque,
        v.cupo_maximo AS cupo,v.reservas_activas AS reservados,v.estado_visible AS estado,m.nombre AS materia
        FROM v_franjas_cupo v JOIN materias m USING(id_materia)
        WHERE v.id_docente=%s AND v.fecha BETWEEN %s AND %s ORDER BY v.id_franja DESC""",
        (id_docente, desde, hasta),
    )
    datos["bloqueos"] = [
        {"desde": b["desde"].isoformat(), "hasta": b["hasta"].isoformat()}
        for b in db.query(
            "SELECT desde,hasta FROM bloqueos_asesoria WHERE id_docente=%s AND desde<=%s AND hasta>=%s ORDER BY desde",
            (id_docente, hasta, desde),
        )
    ]
    return datos
