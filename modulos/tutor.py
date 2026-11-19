# Modulo 4: Rutas base del Tutor (P-03)
from flask import Blueprint, render_template
from auth import rol_requerido

bp = Blueprint("tutor", __name__, url_prefix="/tutor")
ROL = "consulta_seguimiento"

# Vista inicial de agenda de franjas y lista de estudiantes
@bp.route("/franjas")
@rol_requerido(ROL)
def franjas():
    return render_template("en_construccion.html", titulo="Mis franjas")

# Vista inicial de reporte de asesorias impartidas
@bp.route("/reportes")
@rol_requerido(ROL)
def reportes():
    return render_template("en_construccion.html", titulo="Reporte de mis asesorías")
