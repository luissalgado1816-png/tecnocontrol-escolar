# Modulo 2: Rutas base del Administrador Escolar (P-01)
import re
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from pymysql import MySQLError as ErrorBD
from werkzeug.security import generate_password_hash

import db
import reglas
from auth import MIN_PASSWORD, rol_requerido

bp = Blueprint("admin", __name__, url_prefix="/admin")
ROL = "admin_escolar"

DOMINIO = "@zacatepec.tecnm.mx"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
CICLOS = ["Enero-Junio", "Agosto-Diciembre"]
TIPOS_INGRESO = ["Regular", "Cambio de carrera", "Traslado"]
ESTADOS_ESCOLARES = ["Inscrito", "Baja temporal", "Baja total"]
GRADOS = ["Ing.", "Mtro.", "Dr."]
ESTADOS_LABORALES = ["Activo", "Investigación", "Sabático"]
# Prefijo del número de control según el tipo de ingreso (nota del wireframe)
PREFIJO_INGRESO = {"Regular": "", "Cambio de carrera": "C", "Traslado": "T"}

RE_MATRICULA = re.compile(r"^[CT]?\d{8}$")
RE_CLAVE_DOCENTE = re.compile(r"^[A-Za-z0-9-]{3,20}$")
RE_CORREO_LOCAL = re.compile(r"^[A-Za-z0-9._-]{3,60}$")


# Ayudas generales
def _like(texto):
    """Prepara un texto para LIKE '%texto%' sin que % y _ actúen como comodines."""
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def _campo(nombre):
    """Campo de texto del formulario sin espacios de más."""
    return " ".join(request.form.get(nombre, "").split())


def _entero(texto):
    return reglas.entero(texto)


def _periodo_vigente():
    return db.query("SELECT anio, ciclo FROM periodos_escolares WHERE es_actual = 1", one=True)


def _catalogos():
    materias = db.query(
        "SELECT m.id_materia, m.nombre, m.clave_oficial, m.posicion, m.id_departamento, "
        "GROUP_CONCAT(CONCAT(cm.id_carrera, ':', cm.semestre)) AS planes "
        "FROM materias m JOIN carrera_materia cm ON cm.id_materia = m.id_materia "
        "GROUP BY m.id_materia, m.nombre,m.clave_oficial,m.posicion,m.id_departamento ORDER BY m.nombre"
    )
    for materia in materias:
        materia["planes"] = {int(c):int(s) for c,s in (par.split(":") for par in materia["planes"].split(","))}
        materia["carreras"] = list(materia["planes"])
    return {
        "carreras": db.query("SELECT id_carrera, nombre FROM carreras WHERE activa = 1 ORDER BY nombre"),
        "departamentos": db.query("SELECT id_departamento, nombre FROM departamentos ORDER BY nombre"),
        "bloques": db.query("SELECT id_bloque, etiqueta FROM bloques_horarios ORDER BY hora_inicio"),
        "materias": materias,
        "periodo": _periodo_vigente(),
    }


def _datos_horario(cat, modo, filas):
    """Datos que usa el editor de horario (JavaScript) de la ficha."""
    return {
        "modo": modo,
        "filas": filas,
        "dias": DIAS,
        "materias": [
            {"id": m["id_materia"], "nombre": m["nombre"], "planes": m["planes"], "carreras": m["carreras"], "depto": m["id_departamento"], "pos": m["posicion"], "clave": m["clave_oficial"]}
            for m in cat["materias"]
        ],
        "bloques": [{"id": b["id_bloque"], "etiqueta": b["etiqueta"]} for b in cat["bloques"]],
        "carreras": [{"id": c["id_carrera"], "nombre": c["nombre"]} for c in cat["carreras"]],
        "periodoActual": cat["periodo"],
    }


def _semestre(anio_ingreso, ciclo_ingreso, periodo):
    """Mismo cálculo que la vista v_estudiantes_semestre."""
    indice = {"Enero-Junio": 1, "Agosto-Diciembre": 2}
    return (periodo["anio"] - anio_ingreso) * 2 + indice[periodo["ciclo"]] - indice[ciclo_ingreso] + 1


def _leer_filas(form, con_carrera):
    """Lee las filas del horario que arma el editor (campos h_materia, h_dia, h_bloque, h_carrera)."""
    materias = form.getlist("h_materia")
    dias = form.getlist("h_dia")
    bloques = form.getlist("h_bloque")
    carreras = form.getlist("h_carrera")
    cantidades = [len(materias), len(dias), len(bloques)]
    if con_carrera:
        cantidades.append(len(carreras))
    if len(set(cantidades)) != 1:
        raise reglas.ReglaNegocio('El horario está incompleto. Cada fila debe tener materia, día, bloque y, para el docente, carrera.')
    filas = []
    for i, (materia, dia, bloque) in enumerate(zip(materias, dias, bloques)):
        fila = {"materia": _entero(materia), "dia": dia, "bloque": _entero(bloque)}
        if con_carrera:
            fila["carrera"] = _entero(carreras[i]) if i < len(carreras) else None
        filas.append(fila)
    return filas


def _validar_filas(filas, cat, errores, carrera_estudiante=None, con_carrera=False, depto_docente=None, semestre=None, grado=None):
    """Revisa el horario: materia válida para la carrera (y departamento), sin dos clases a la misma hora."""
    materias = {m["id_materia"]: m for m in cat["materias"]}
    bloques = {b["id_bloque"]: b["etiqueta"] for b in cat["bloques"]}
    vistos = set()
    for fila in filas:
        materia = materias.get(fila["materia"])
        if materia is None or fila["dia"] not in DIAS or fila["bloque"] not in bloques:
            errores.append("Hay un bloque de clase con datos no válidos.")
            return
        carrera = fila["carrera"] if con_carrera else carrera_estudiante
        if carrera not in materia["carreras"]:
            errores.append(f"«{materia['nombre']}» no pertenece a la carrera seleccionada.")
            return
        if depto_docente is not None and materia["id_departamento"] != depto_docente:
            errores.append(f"«{materia['nombre']}» no es del departamento del docente.")
            return
        if semestre is not None and materia["planes"][carrera] != semestre:
            errores.append(f"«{materia['nombre']}» corresponde a otro semestre de esta carrera.")
            return
        if grado and materia["posicion"] > reglas.nivel(grado):
            errores.append("El grado académico no permite asignar esa posición de la cadena.")
            return
        clave = (fila["dia"], fila["bloque"])
        if clave in vistos:
            errores.append(f"Hay dos clases el {fila['dia']} de {bloques[fila['bloque']]}.")
            return
        vistos.add(clave)


def _ordenar(filas):
    return sorted(filas, key=lambda f: (DIAS.index(f["dia"]), f["bloque"]))


def _validar_acceso(form, nuevo, errores, id_usuario=None):
    """Correo y contraseña (la contraseña es obligatoria solo en el alta)."""
    if not RE_CORREO_LOCAL.match(form["correo_local"]):
        errores.append("El correo institucional solo puede llevar letras, números, punto, guion y guion bajo (mínimo 3).")
    else:
        existe = db.query(
            "SELECT id_usuario FROM usuarios WHERE correo_institucional = %s AND id_usuario <> %s",
            (form["correo_local"] + DOMINIO, id_usuario or 0),
            one=True,
        )
        if existe:
            errores.append("Ese correo institucional ya está registrado.")

    password, confirmar = form["password"], form["confirmar"]
    if nuevo or password or confirmar:
        if len(password) < MIN_PASSWORD:
            errores.append(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres.")
        elif password != confirmar:
            errores.append("Las contraseñas no coinciden.")


def _mensaje(error):
    if error.args and error.args[0] == 4025 and "ck_doc_tutor_activo" in str(error):
        return "Un docente habilitado como tutor debe estar Activo. Coordinación debe quitar primero su habilitación."
    return db.mensaje_error(error)


# ESTUDIANTES
@bp.route("/estudiantes")
@rol_requerido(ROL)
def estudiantes():
    q = request.args.get("q", "").strip()
    filtros = {k: request.args.get(k, '').strip() for k in ('paterno', 'materno', 'nombres')}
    filas = db.query(
        "SELECT id_estudiante, matricula, CONCAT_WS(' ', nombres, apellido_paterno, apellido_materno) AS nombre, "
        "carrera, semestre_actual, tipo_ingreso, estado "
        "FROM v_estudiantes_semestre WHERE matricula LIKE %s AND apellido_paterno LIKE %s "
        "AND COALESCE(apellido_materno, '') LIKE %s AND nombres LIKE %s ORDER BY matricula",
        (_like(q), *(_like(filtros[k]) for k in ('paterno', 'materno', 'nombres'))),
    )
    return render_template("admin/estudiantes.html", q=q, filtros=filtros, buscado=bool(q or any(filtros.values())), filas=filas, periodo=_periodo_vigente())


@bp.route("/estudiantes/nuevo", methods=["GET", "POST"])
@rol_requerido(ROL)
def estudiantes_nuevo():
    return _ficha_estudiante(None)


@bp.route("/estudiantes/<int:id_estudiante>", methods=["GET", "POST"])
@rol_requerido(ROL)
def estudiantes_ficha(id_estudiante):
    return _ficha_estudiante(id_estudiante)


def _leer_form_estudiante(actual):
    id_carrera = _entero(request.form.get("id_carrera"))
    numero = actual['matricula'] if actual else request.form.get('matricula', '').strip().upper()
    base = numero[1:] if numero.startswith(('C', 'T')) else numero
    tipo = request.form.get('tipo_ingreso', '')
    # RN-01: el sistema forma el identificador completo tanto al dar de alta como al editar.
    numero = PREFIJO_INGRESO.get(tipo, '') + base
    return {
        "matricula": numero,
        "ap_paterno": _campo("ap_paterno"),
        "ap_materno": _campo("ap_materno"),
        "nombres": _campo("nombres"),
        "id_carrera": id_carrera,
        "ciclo": request.form.get("ciclo", ""),
        "anio": request.form.get("anio", "").strip(),
        "tipo_ingreso": request.form.get("tipo_ingreso", ""),
        "estado": request.form.get("estado", ""),
        "correo_local": request.form.get("correo_local", "").strip(),
        "password": request.form.get("password", ""),
        "confirmar": request.form.get("confirmar", ""),
    }


def _validar_estudiante(form, filas, cat, actual, errores):
    if not re.fullmatch(r'[CT]?[0-9]{8}', form['matricula']):
        errores.append('El número de control debe tener 8 dígitos, con C para cambio de carrera o T para traslado.')
    else:
        prefijo = form['matricula'][0] if form['matricula'][0] in 'CT' else ''
        if prefijo != PREFIJO_INGRESO.get(form['tipo_ingreso']):
            errores.append('El número de control no corresponde al tipo de ingreso.')
        if (db.query('SELECT id_usuario FROM usuarios WHERE username = %s AND id_usuario <> %s',
                     (form['matricula'], actual['id_usuario'] if actual else 0), one=True)
                or db.query('SELECT id_estudiante FROM estudiantes WHERE matricula = %s AND id_estudiante <> %s',
                            (form['matricula'], actual['id_estudiante'] if actual else 0), one=True)):
            errores.append('Ya existe un estudiante con ese número de control.')

    if not form["ap_paterno"] or not form["nombres"]:
        errores.append("Captura el apellido paterno y los nombres.")
    if len(form["ap_paterno"]) > 60 or len(form["ap_materno"]) > 60 or len(form["nombres"]) > 80:
        errores.append("Algún nombre o apellido es demasiado largo.")

    carreras = {c["id_carrera"] for c in cat["carreras"]}
    if form["id_carrera"] not in carreras:
        errores.append("Selecciona una carrera.")
    if form["tipo_ingreso"] not in TIPOS_INGRESO:
        errores.append("Selecciona el tipo de ingreso.")
    if form["estado"] not in ESTADOS_ESCOLARES:
        errores.append("Selecciona el estado escolar.")

    anio = _entero(form["anio"])
    if form["ciclo"] not in CICLOS or anio is None or not 2000 <= anio <= 2100:
        errores.append("Captura un periodo y año de ingreso válidos.")
    elif cat["periodo"] is None:
        errores.append("No hay un periodo escolar vigente; no se puede calcular el semestre.")
    elif _semestre(anio, form["ciclo"], cat["periodo"]) < 1:
        errores.append("El periodo de ingreso no puede ser posterior al periodo vigente.")

    _validar_acceso(form, actual is None, errores, actual["id_usuario"] if actual else None)
    semestre = _semestre(anio, form["ciclo"], cat["periodo"]) if anio and form["ciclo"] in CICLOS and cat["periodo"] else None
    _validar_filas(filas, cat, errores, carrera_estudiante=form["id_carrera"], semestre=semestre)


def _id_periodo(anio, ciclo):
    """Devuelve el id del periodo; si todavía no existe lo crea (como periodo no vigente)."""
    fila = db.query('SELECT id_periodo FROM periodos_escolares WHERE anio = %s AND ciclo = %s FOR UPDATE', (anio, ciclo), one=True)
    if fila:
        return fila['id_periodo']
    db.execute("INSERT INTO periodos_escolares (anio, ciclo, es_actual) VALUES (%s, %s, 0)", (anio, ciclo))
    return db.query("SELECT id_periodo FROM periodos_escolares WHERE anio = %s AND ciclo = %s", (anio, ciclo), one=True)["id_periodo"]


def _guardar_estudiante(form, filas, actual):
    correo = form["correo_local"] + DOMINIO
    clave = generate_password_hash(form["password"], method='scrypt') if form["password"] else None
    materno = form["ap_materno"] or None
    with db.transaction():
        if actual:
            actual = reglas.bloquear_estudiante(actual['id_estudiante'])
            reglas.validar_edicion_estudiante(actual, form, filas)
        id_periodo = _id_periodo(int(form["anio"]), form["ciclo"])
        if actual is None:
            id_usuario = db.insert(
                "INSERT INTO usuarios (username, password_hash, id_rol, correo_institucional, activo) "
                "SELECT %s, %s, id_rol, %s, 1 FROM roles WHERE codigo_rol = 'consulta_seguimiento_est'",
                (form["matricula"], clave, correo),
            )
            id_estudiante = db.insert(
                "INSERT INTO estudiantes (id_usuario, matricula, apellido_paterno, apellido_materno, nombres, "
                "id_carrera, id_periodo_ingreso, tipo_ingreso, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (id_usuario, form["matricula"], form["ap_paterno"], materno, form["nombres"],
                 form["id_carrera"], id_periodo, form["tipo_ingreso"], form["estado"]),
            )
        else:
            id_estudiante = actual["id_estudiante"]
            db.execute(
                "UPDATE estudiantes SET matricula = %s, apellido_paterno = %s, apellido_materno = %s, nombres = %s, id_carrera = %s, "
                "id_periodo_ingreso = %s, tipo_ingreso = %s, estado = %s WHERE id_estudiante = %s",
                (form['matricula'], form["ap_paterno"], materno, form["nombres"], form["id_carrera"], id_periodo,
                 form["tipo_ingreso"], form["estado"], id_estudiante),
            )
            db.execute("UPDATE usuarios SET username = %s, correo_institucional = %s WHERE id_usuario = %s", (form['matricula'], correo, actual["id_usuario"]))
            if clave:
                db.execute("UPDATE usuarios SET password_hash = %s WHERE id_usuario = %s", (clave, actual["id_usuario"]))
            db.execute("DELETE FROM horario_estudiante WHERE id_estudiante = %s AND id_periodo=(SELECT id_periodo FROM periodos_escolares WHERE es_actual=1)", (id_estudiante,))
        for fila in _ordenar(filas):
            db.execute(
                "INSERT INTO horario_estudiante (id_estudiante, id_materia, dia_semana, id_bloque) VALUES (%s, %s, %s, %s)",
                (id_estudiante, fila["materia"], fila["dia"], fila["bloque"]),
            )


def _ficha_estudiante(id_estudiante):
    cat = _catalogos()
    actual = None
    if id_estudiante is not None:
        actual = db.query(
            "SELECT e.*, p.anio AS anio_ingreso, p.ciclo AS ciclo_ingreso, u.correo_institucional "
            "FROM estudiantes e JOIN usuarios u ON u.id_usuario = e.id_usuario "
            "JOIN periodos_escolares p ON p.id_periodo = e.id_periodo_ingreso WHERE e.id_estudiante = %s",
            (id_estudiante,),
            one=True,
        )
        if actual is None:
            abort(404)

    errores = []
    if request.method == "POST":
        form = _leer_form_estudiante(actual)
        try:
            filas = _leer_filas(request.form, con_carrera=False)
        except reglas.ReglaNegocio as error:
            filas = []
            errores.append(str(error))
        _validar_estudiante(form, filas, cat, actual, errores)
        if not errores:
            try:
                _guardar_estudiante(form, filas, actual)
            except ErrorBD as error:
                errores.append(_mensaje(error))
            except reglas.ReglaNegocio as error:
                errores.append(str(error))
            else:
                flash("Estudiante guardado. Su cuenta quedó activa." if actual is None else "Cambios guardados.", "success")
                return redirect(url_for("admin.estudiantes", q=form["matricula"]))
    elif actual:
        form = {
            "matricula": actual["matricula"], "ap_paterno": actual["apellido_paterno"],
            "ap_materno": actual["apellido_materno"] or "", "nombres": actual["nombres"],
            "id_carrera": actual["id_carrera"], "ciclo": actual["ciclo_ingreso"], "anio": str(actual["anio_ingreso"]),
            "tipo_ingreso": actual["tipo_ingreso"], "estado": actual["estado"],
            "correo_local": actual["correo_institucional"].removesuffix(DOMINIO), "password": "", "confirmar": "",
        }
        filas = [
            {"materia": h["id_materia"], "dia": h["dia_semana"], "bloque": h["id_bloque"]}
            for h in db.query("SELECT id_materia, dia_semana, id_bloque FROM v_horario_estudiante_actual WHERE id_estudiante = %s", (id_estudiante,))
        ]
    else:
        form = {
            "matricula": request.args.get("matricula", "").strip().upper(),
            "ap_paterno": request.args.get("paterno", "").strip(), "ap_materno": request.args.get("materno", "").strip(),
            "nombres": request.args.get("nombres", "").strip(), "id_carrera": None,
            "ciclo": cat["periodo"]["ciclo"] if cat["periodo"] else "", "anio": str(cat["periodo"]["anio"]) if cat["periodo"] else "",
            "tipo_ingreso": "Regular", "estado": "Inscrito", "correo_local": "", "password": "", "confirmar": "",
        }
        filas = []

    return render_template(
        "admin/estudiante_ficha.html", form=form, errores=errores, actual=actual, cat=cat,
        tipos=TIPOS_INGRESO, estados=ESTADOS_ESCOLARES, ciclos=CICLOS, periodo=cat["periodo"],
        datos_horario=_datos_horario(cat, "estudiante", filas),
    )


# DOCENTES
@bp.route("/docentes")
@rol_requerido(ROL)
def docentes():
    q = request.args.get("q", "").strip()
    filtros = {k: request.args.get(k, '').strip() for k in ('paterno', 'materno', 'nombres')}
    filas = db.query(
        "SELECT d.id_docente, d.clave_docente, CONCAT_WS(' ', d.nombres, d.apellido_paterno, d.apellido_materno) AS nombre, "
        "d.grado_academico, d.estado_laboral, dep.nombre AS departamento, "
        "(SELECT GROUP_CONCAT(DISTINCT m.nombre) FROM v_horario_docente_actual h "
        "   JOIN materias m ON m.id_materia = h.id_materia WHERE h.id_docente = d.id_docente) AS materias, "
        "(SELECT GROUP_CONCAT(DISTINCT c.nombre) FROM v_horario_docente_actual h "
        "   JOIN carreras c ON c.id_carrera = h.id_carrera WHERE h.id_docente = d.id_docente) AS carreras "
        "FROM docentes d JOIN departamentos dep ON dep.id_departamento = d.id_departamento "
        "WHERE d.clave_docente LIKE %s AND d.apellido_paterno LIKE %s "
        "AND COALESCE(d.apellido_materno, '') LIKE %s AND d.nombres LIKE %s ORDER BY d.clave_docente",
        (_like(q), *(_like(filtros[k]) for k in ('paterno', 'materno', 'nombres'))),
    )
    return render_template("admin/docentes.html", q=q, filtros=filtros, buscado=bool(q or any(filtros.values())), filas=filas)


@bp.route("/docentes/nuevo", methods=["GET", "POST"])
@rol_requerido(ROL)
def docentes_nuevo():
    return _ficha_docente(None)


@bp.route("/docentes/<int:id_docente>", methods=["GET", "POST"])
@rol_requerido(ROL)
def docentes_ficha(id_docente):
    return _ficha_docente(id_docente)


def _siguiente_usuario_docente():
    """Siguiente usuario de acceso libre: maestro0001, maestro0002..."""
    fila = db.query(
        "SELECT COALESCE(MAX(CAST(SUBSTRING(username, 8) AS UNSIGNED)), 0) + 1 AS n "
        "FROM usuarios WHERE username REGEXP '^maestro[0-9]+$'",
        one=True,
    )
    return f"maestro{int(fila['n']):04d}"


def _leer_form_docente(actual):
    return {
        "clave_docente": actual["clave_docente"] if actual else request.form.get("clave_docente", "").strip().upper(),
        "ap_paterno": _campo("ap_paterno"),
        "ap_materno": _campo("ap_materno"),
        "nombres": _campo("nombres"),
        "grado": request.form.get("grado", ""),
        "estado_laboral": request.form.get("estado_laboral", ""),
        "id_departamento": _entero(request.form.get("id_departamento")),
        "correo_local": request.form.get("correo_local", "").strip(),
        "password": request.form.get("password", ""),
        "confirmar": request.form.get("confirmar", ""),
    }


def _validar_docente(form, filas, cat, actual, errores):
    if actual is None:
        if not RE_CLAVE_DOCENTE.match(form["clave_docente"]):
            errores.append("La clave docente debe tener de 3 a 20 caracteres (letras, números y guion), por ejemplo DOC-104.")
        elif db.query("SELECT 1 AS x FROM docentes WHERE clave_docente = %s", (form["clave_docente"],), one=True):
            errores.append("Ya existe un docente con esa clave.")

    if not form["ap_paterno"] or not form["nombres"]:
        errores.append("Captura el apellido paterno y los nombres.")
    if len(form["ap_paterno"]) > 60 or len(form["ap_materno"]) > 60 or len(form["nombres"]) > 80:
        errores.append("Algún nombre o apellido es demasiado largo.")
    if form["grado"] not in GRADOS and form["grado"] != (actual or {}).get("grado_academico"):
        errores.append("Selecciona el grado académico.")
    if form["estado_laboral"] not in ESTADOS_LABORALES:
        errores.append("Selecciona el estado laboral.")
    departamentos = {d["id_departamento"] for d in cat["departamentos"]}
    if form["id_departamento"] not in departamentos:
        errores.append("Selecciona el departamento.")

    _validar_acceso(form, actual is None, errores, actual["id_usuario"] if actual else None)
    if actual and (form["password"] or form["confirmar"]):
        errores.append("Utiliza Restablecer contraseña para cambiar el acceso de un docente registrado.")
    if form["estado_laboral"] != "Activo" and filas:
        errores.append("El horario debe quedar vacío en Investigación o Sabático.")
    _validar_filas(filas, cat, errores, con_carrera=True, depto_docente=form["id_departamento"],grado=form["grado"])


def _guardar_docente(form, filas, actual):
    correo = form["correo_local"] + DOMINIO
    clave = generate_password_hash(form["password"], method='scrypt') if form["password"] else None
    materno = form["ap_materno"] or None
    with db.transaction():
        if actual:
            actual = reglas.bloquear_docente(actual['id_docente'])
            reglas.validar_edicion_docente(actual, form, filas)
        if actual is None:
            id_usuario = db.insert(
                "INSERT INTO usuarios (username, password_hash, id_rol, correo_institucional, activo) "
                "SELECT %s, %s, id_rol, %s, 0 FROM roles WHERE codigo_rol = 'consulta_seguimiento'",
                (_siguiente_usuario_docente(), clave, correo),
            )
            # El trigger deja la cuenta inactiva hasta que Coordinación habilite al tutor
            id_docente = db.insert(
                "INSERT INTO docentes (id_usuario, clave_docente, apellido_paterno, apellido_materno, nombres, "
                "grado_academico, estado_laboral, id_departamento, habilitado_tutor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)",
                (id_usuario, form["clave_docente"], form["ap_paterno"], materno, form["nombres"],
                 form["grado"], form["estado_laboral"], form["id_departamento"]),
            )
        else:
            id_docente = actual["id_docente"]
            if form["estado_laboral"] != "Activo":
                reglas.cancelar_franjas(id_docente,"Cambio de estado laboral del docente")
                db.execute("UPDATE docentes SET habilitado_tutor=0 WHERE id_docente=%s",(id_docente,))
            db.execute(
                "UPDATE docentes SET apellido_paterno = %s, apellido_materno = %s, nombres = %s, grado_academico = %s, "
                "estado_laboral = %s, id_departamento = %s WHERE id_docente = %s",
                (form["ap_paterno"], materno, form["nombres"], form["grado"], form["estado_laboral"],
                 form["id_departamento"], id_docente),
            )
            db.execute("UPDATE usuarios SET correo_institucional = %s WHERE id_usuario = %s", (correo, actual["id_usuario"]))
            if clave:
                db.execute("UPDATE usuarios SET password_hash = %s WHERE id_usuario = %s", (clave, actual["id_usuario"]))
            db.execute("DELETE FROM horario_docente WHERE id_docente = %s AND id_periodo=(SELECT id_periodo FROM periodos_escolares WHERE es_actual=1)", (id_docente,))
        for fila in _ordenar(filas):
            db.execute(
                "INSERT INTO horario_docente (id_docente, id_carrera, id_materia, dia_semana, id_bloque) VALUES (%s, %s, %s, %s, %s)",
                (id_docente, fila["carrera"], fila["materia"], fila["dia"], fila["bloque"]),
            )

        if actual:
            reglas.sincronizar_perfil(id_docente)


def _ficha_docente(id_docente):
    cat = _catalogos()
    actual = None
    if id_docente is not None:
        actual = db.query(
            "SELECT d.*, u.username, u.correo_institucional FROM docentes d "
            "JOIN usuarios u ON u.id_usuario = d.id_usuario WHERE d.id_docente = %s",
            (id_docente,),
            one=True,
        )
        if actual is None:
            abort(404)

    errores = []
    if request.method == "POST":
        form = _leer_form_docente(actual)
        try:
            filas = _leer_filas(request.form, con_carrera=True)
        except reglas.ReglaNegocio as error:
            filas = []
            errores.append(str(error))
        _validar_docente(form, filas, cat, actual, errores)
        if not errores:
            try:
                _guardar_docente(form, filas, actual)
            except ErrorBD as error:
                errores.append(_mensaje(error))
            except reglas.ReglaNegocio as error:
                errores.append(str(error))
            else:
                flash(
                    "Docente guardado. Coordinación activa su acceso de tutor al habilitar su perfil."
                    if actual is None else "Cambios guardados.",
                    "success",
                )
                return redirect(url_for("admin.docentes", q=form["clave_docente"]))
    elif actual:
        form = {
            "clave_docente": actual["clave_docente"], "ap_paterno": actual["apellido_paterno"],
            "ap_materno": actual["apellido_materno"] or "", "nombres": actual["nombres"],
            "grado": actual["grado_academico"], "estado_laboral": actual["estado_laboral"],
            "id_departamento": actual["id_departamento"],
            "correo_local": actual["correo_institucional"].removesuffix(DOMINIO), "password": "", "confirmar": "",
        }
        filas = [
            {"materia": h["id_materia"], "carrera": h["id_carrera"], "dia": h["dia_semana"], "bloque": h["id_bloque"]}
            for h in db.query("SELECT id_materia, id_carrera, dia_semana, id_bloque FROM v_horario_docente_actual WHERE id_docente = %s", (id_docente,))
        ]
    else:
        form = {
            "clave_docente": request.args.get("clave", "").strip().upper(),
            "ap_paterno": request.args.get("paterno", "").strip(), "ap_materno": request.args.get("materno", "").strip(),
            "nombres": request.args.get("nombres", "").strip(), "grado": "", "estado_laboral": "Activo",
            "id_departamento": None, "correo_local": "", "password": "", "confirmar": "",
        }
        filas = []

    usuario_acceso = actual["username"] if actual else _siguiente_usuario_docente()
    return render_template(
        "admin/docente_ficha.html", form=form, errores=errores, actual=actual, cat=cat,
        grados=GRADOS + ([actual["grado_academico"]] if actual and actual["grado_academico"] not in GRADOS else []), estados=ESTADOS_LABORALES, usuario_acceso=usuario_acceso,
        datos_horario=_datos_horario(cat, "docente", filas),
    )


@bp.post('/docentes/<int:id_docente>/restablecer')
@rol_requerido(ROL)
def restablecer_docente(id_docente):
    nueva = request.form.get('nueva','')
    if len(nueva) < MIN_PASSWORD or nueva != request.form.get('repetir'):
        flash('Las contraseñas deben coincidir y tener al menos ocho caracteres.', 'warning')
    else:
        with db.transaction():
            docente = reglas.bloquear_docente(id_docente)
            db.execute('UPDATE usuarios SET password_hash=%s WHERE id_usuario=%s',
                       (generate_password_hash(nueva,method='scrypt'),docente['id_usuario']))
        flash('Contraseña restablecida.', 'success')
    return redirect(url_for('admin.docentes_ficha',id_docente=id_docente))
