# Modulo 5: Rutas base del Estudiante (P-04)
from flask import Blueprint, render_template
from auth import rol_requerido

bp = Blueprint("estudiante", __name__, url_prefix="/estudiante")
ROL = "consulta_seguimiento_est"

# Vista inicial de consulta de franjas y reserva de asesoria
@bp.route("/reservar")
@rol_requerido(ROL)
def reservar():
    return render_template("en_construccion.html", titulo="Reservar asesoría")

# Vista inicial de citas programadas e historial de acuerdos
@bp.route("/historial")
@rol_requerido(ROL)
def historial():
    return render_template("en_construccion.html", titulo="Mi historial")
