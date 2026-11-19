# Modulo 3: Rutas base del Coordinador de Tutorias (P-02)
from flask import Blueprint, render_template
from auth import rol_requerido

bp = Blueprint("coordinacion", __name__, url_prefix="/coordinacion")
ROL = "coordinador_tutorias"

# Vista inicial de habilitacion de tutores y materias autorizadas
@bp.route("/tutores")
@rol_requerido(ROL)
def tutores():
    return render_template("en_construccion.html", titulo="Tutores")

# Vista inicial de monitoreo de franjas de asesoria
@bp.route("/franjas")
@rol_requerido(ROL)
def franjas():
    return render_template("en_construccion.html", titulo="Franjas de asesoría")

# Vista inicial de consulta de historial por estudiante
@bp.route("/historial")
@rol_requerido(ROL)
def historial():
    return render_template("en_construccion.html", titulo="Historial de estudiante")

# Vista inicial de reporte general de tutorias
@bp.route("/reportes")
@rol_requerido(ROL)
def reportes():
    return render_template("en_construccion.html", titulo="Reporte general")
