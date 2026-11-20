# Motor principal de TecnoControl Escolar (Flask)
import hmac
import secrets

import pymysql
from flask import Flask, abort, g, render_template, request, session

import db
import reglas
from auth import bp as auth_bp
from config import Config
from modulos.admin import bp as admin_bp
from modulos.coordinacion import bp as coordinacion_bp
from modulos.estudiante import bp as estudiante_bp
from modulos.tutor import bp as tutor_bp

# Pestanas de navegacion por rol (barra superior segun wireframes)
MENU = {
    "admin_escolar": [
        ("Estudiantes", "admin.estudiantes"),
        ("Docentes", "admin.docentes"),
    ],
    "coordinador_tutorias": [
        ("Tutores", "coordinacion.tutores"),
        ("Franjas", "coordinacion.franjas"),
        ("Historial", "coordinacion.historial"),
        ("Reportes", "coordinacion.reportes"),
    ],
    "consulta_seguimiento_est": [
        ("Reservar asesoría", "estudiante.reservar"),
        ("Mi historial", "estudiante.historial"),
    ],
    "consulta_seguimiento": [
        ("Mis franjas", "tutor.franjas"),
        ("Reportes", "tutor.reportes"),
    ],
}


# Fabrica de la aplicacion Flask
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    reglas.registrar_filtros(app)

    # Cierra conexion a BD al terminar cada peticion y registra blueprints
    app.teardown_appcontext(db.close_db)
    for blueprint in (auth_bp, admin_bp, coordinacion_bp, estudiante_bp, tutor_bp):
        app.register_blueprint(blueprint)

    # Carga los datos del usuario activo antes de cada vista
    @app.before_request
    def cargar_usuario():
        g.user = None
        if request.endpoint == "static":
            return
        user_id = session.get("user_id")
        if user_id:
            usuario = db.query(
                "SELECT u.id_usuario, u.username, u.activo, r.codigo_rol "
                "FROM usuarios u JOIN roles r ON r.id_rol = u.id_rol "
                "WHERE u.id_usuario = %s",
                (user_id,),
                one=True,
            )
            if usuario and usuario["activo"]:
                g.user = usuario
            else:
                session.clear()

    # Valida el token CSRF en todos los envios de formularios POST
    @app.before_request
    def verificar_csrf():
        if request.method == "POST":
            enviado = request.form.get("_csrf", "")
            esperado = session.get("_csrf", "")
            if not isinstance(enviado, str) or not isinstance(esperado, str) or not esperado:
                abort(400)
            if not hmac.compare_digest(enviado.encode("utf-8"), esperado.encode("utf-8")):
                abort(400)

    # Inyecta token CSRF y pestanas activas en todas las plantillas HTML
    @app.context_processor
    def datos_de_plantilla():
        def csrf_token():
            if "_csrf" not in session:
                session["_csrf"] = secrets.token_hex(16)
            return session["_csrf"]

        pestanas = []
        if g.get("user"):
            actual = request.endpoint or ""
            for etiqueta, endpoint in MENU.get(g.user["codigo_rol"], []):
                # Modulo 4: mantiene activa Reservar asesoria al confirmar la reserva.
                activa = (actual.startswith(endpoint)
                          or (actual == 'coordinacion.perfil' and endpoint == 'coordinacion.tutores')
                          or (actual == 'estudiante.confirmar' and endpoint == 'estudiante.reservar'))
                pestanas.append((etiqueta, endpoint, activa))
        return {"csrf_token": csrf_token, "pestanas": pestanas}

    # Manejadores personalizados de errores HTTP y de MariaDB
    @app.errorhandler(400)
    def error_400(_e):
        return render_template("error.html", codigo=400,
                               mensaje="El formulario expiró o no es válido. Recarga la página e inténtalo de nuevo."), 400

    @app.errorhandler(403)
    def error_403(_e):
        return render_template("error.html", codigo=403,
                               mensaje="No tienes permiso para ver esta página."), 403

    @app.errorhandler(404)
    def error_404(_e):
        return render_template("error.html", codigo=404, mensaje="La página no existe."), 404

    @app.errorhandler(pymysql.MySQLError)
    def error_bd(error):
        app.logger.exception("Error de base de datos")
        return render_template("error.html", codigo=500, mensaje=db.mensaje_error(error)), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
