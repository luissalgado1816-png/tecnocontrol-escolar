# Archivo de confiracion.
import os
import secrets
from datetime import timedelta


class Config:
    # Seguridad y modo de ejecución
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    
    # Parametros de conexion hacia MariaDB
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "tecnocontrol_escolar")
    DB_SOCKET = os.environ.get("DB_SOCKET")  # opcional (conexión por socket en Linux/macOS)

    # Configuracion de cookies y duracion de sesion
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)