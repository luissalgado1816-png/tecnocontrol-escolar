# Modulo 1: Inicio de sesion, cierre de sesion y restablecimiento de clave (WF-00 y WF-00B)
import re
import time
from functools import wraps

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db

bp = Blueprint("auth", __name__)

# Ruta inicial segun el codigo_rol en la tabla roles
HOME_POR_ROL = {
    "admin_escolar": "admin.estudiantes",
    "coordinador_tutorias": "coordinacion.tutores",
    "consulta_seguimiento": "tutor.franjas",
    "consulta_seguimiento_est": "estudiante.reservar",
}

MIN_PASSWORD = 8
MINUTOS_RESTABLECER = 10
AVISO_ALTA = "Si aún no tienes acceso, verifica el alta de tu cuenta con Servicios Escolares."
AVISO_CREDENCIALES = "Verifica tu usuario y contraseña."
PATRON_CORREO = re.compile(r"[^@\s]+@zacatepec\.tecnm\.mx", re.IGNORECASE)


# Devuelve la URL de inicio del rol o lanza error 403 si no existe
def home_url(codigo_rol):
    destino = HOME_POR_ROL.get(codigo_rol)
    if destino is None:
        abort(403)
    return url_for(destino)


# Decorador para restringir rutas segun el rol del usuario activo
def rol_requerido(*roles):
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))
            if g.user["codigo_rol"] not in roles:
                abort(403)
            return vista(*args, **kwargs)

        return envoltura

    return decorador


# Redireccion desde la raiz del sitio
@bp.route("/")
def index():
    if g.user:
        return redirect(home_url(g.user["codigo_rol"]))
    return redirect(url_for("auth.login"))


# Validacion de credenciales y apertura de sesion (WF-00)
@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(home_url(g.user["codigo_rol"]))

    errores = {}
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username:
            errores["username"] = "Escribe tu usuario o número de control."
        elif len(username) > 50:
            errores["username"] = "El usuario debe tener como máximo 50 caracteres."
        if not password:
            errores["password"] = "Escribe tu contraseña."
        if errores:
            flash("Completa correctamente los campos señalados.", "danger")
            return render_template("login.html", errores=errores)

        usuario = db.query(
            "SELECT u.id_usuario, u.password_hash, u.activo, r.codigo_rol "
            "FROM usuarios u JOIN roles r ON r.id_rol = u.id_rol "
            "WHERE u.username = %s",
            (username,),
            one=True,
        )
        if usuario is None or not usuario["activo"]:
            flash(AVISO_ALTA, "warning")
        elif not check_password_hash(usuario["password_hash"], password):
            flash(AVISO_CREDENCIALES, "danger")
        else:
            session.clear()
            session["user_id"] = usuario["id_usuario"]
            session.permanent = True
            return redirect(home_url(usuario["codigo_rol"]))

    return render_template("login.html", errores=errores)


# Cierre de sesion por peticion POST
@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


# Verifica si sigue vigente el tiempo de 10 minutos para restablecer clave
def _reset_vigente():
    datos = session.get("reset")
    if (isinstance(datos, dict)
            and isinstance(datos.get("expira"), (int, float))
            and datos["expira"] > time.time()):
        return datos
    session.pop("reset", None)
    return None


# Flujo en dos pasos para restablecer contraseña institucional (RF-13 / WF-00B)
@bp.route("/restablecer", methods=["GET", "POST"])
def restablecer():
    actualizado = False
    errores = {}

    if request.method == "POST":
        paso = request.form.get("paso")

        if paso == "verificar":
            session.pop("reset", None)
            numero = request.form.get("numero", "").strip()
            correo = request.form.get("correo", "").strip()
            if not numero:
                errores["numero"] = "Escribe tu usuario o número de control."
            elif len(numero) > 50:
                errores["numero"] = "El usuario debe tener como máximo 50 caracteres."
            if not correo:
                errores["correo"] = "Escribe tu correo institucional."
            elif len(correo) > 120 or PATRON_CORREO.fullmatch(correo) is None:
                errores["correo"] = "Usa tu correo completo con el dominio @zacatepec.tecnm.mx."
            if errores:
                flash("Completa correctamente los campos señalados.", "danger")
                return render_template("restablecer.html", reset=None, actualizado=False, errores=errores)

            usuario = db.query(
                "SELECT id_usuario FROM usuarios "
                "WHERE username = %s AND correo_institucional = %s AND activo = 1",
                (numero, correo),
                one=True,
            )
            if usuario:
                session["reset"] = {
                    "uid": usuario["id_usuario"],
                    "numero": numero,
                    "correo": correo,
                    "expira": time.time() + MINUTOS_RESTABLECER * 60,
                }
            else:
                session.pop("reset", None)
                flash("Los datos no coinciden. Verifica tu usuario o número de control y correo.", "danger")

        elif paso == "actualizar":
            datos = _reset_vigente()
            nueva = request.form.get("password", "")
            confirmar = request.form.get("confirmar", "")
            if datos is None:
                flash("La verificación caducó. Vuelve a verificar tus datos.", "warning")
            elif len(nueva) < MIN_PASSWORD:
                errores["password"] = f"Escribe al menos {MIN_PASSWORD} caracteres."
                if not confirmar:
                    errores["confirmar"] = "Confirma tu nueva contraseña."
                flash(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres.", "danger")
            elif nueva != confirmar:
                errores["confirmar"] = "Debe coincidir con la nueva contraseña."
                flash("Las contraseñas no coinciden.", "danger")
            else:
                with db.transaction():
                    afectadas = db.execute(
                        "UPDATE usuarios SET password_hash = %s "
                        "WHERE id_usuario = %s AND username = %s "
                        "AND correo_institucional = %s AND activo = 1",
                        (generate_password_hash(nueva, method="scrypt"), datos["uid"],
                         datos["numero"], datos["correo"]),
                    )
                session.pop("reset", None)
                if afectadas == 1:
                    actualizado = True
                else:
                    flash("Los datos de la cuenta cambiaron. Vuelve a verificarlos.", "warning")
        else:
            abort(400)

    datos = _reset_vigente() if not actualizado else None
    return render_template("restablecer.html", reset=datos, actualizado=actualizado, errores=errores)
