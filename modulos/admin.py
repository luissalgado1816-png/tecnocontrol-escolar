# Modulo 2: Rutas base del Administrador Escolar (P-01)
from flask import Blueprint, render_template
from auth import rol_requerido

bp = Blueprint("admin", __name__, url_prefix="/admin")
ROL = "admin_escolar"

# Vista inicial de gestion de estudiantes
@bp.route("/estudiantes")
@rol_requerido(ROL)
def estudiantes():
    return render_template("en_construccion.html", titulo="Estudiantes")

# Vista inicial de gestion de docentes
@bp.route("/docentes")
@rol_requerido(ROL)
def docentes():
    return render_template("en_construccion.html", titulo="Docentes")
