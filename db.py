# Conexion y operaciones hacia MariaDB
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor
from flask import current_app, g


# Abre o reutiliza la conexion de la peticion actual
def get_db():
    if "db" not in g:
        cfg = current_app.config
        params = dict(
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
            database=cfg["DB_NAME"],
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            cursorclass=DictCursor,
            autocommit=False,
            init_command="SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED",
            connect_timeout=5,
        )
        if cfg.get("DB_SOCKET"):
            params["unix_socket"] = cfg["DB_SOCKET"]
        g.db = pymysql.connect(**params)
    return g.db


# Cierra la conexion al terminar la peticion HTTP
def close_db(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None and conexion.open:
        conexion.close()


# Consultas SELECT parametrizadas
def query(sql, params=(), one=False):
    cursor = get_db().cursor()
    try:
        cursor.execute(sql, params)
        filas = cursor.fetchall()
    finally:
        cursor.close()
    if one:
        return filas[0] if filas else None
    return filas


# Actualizaciones y eliminaciones (UPDATE / DELETE)
def execute(sql, params=()):
    cursor = get_db().cursor()
    try:
        cursor.execute(sql, params)
        return cursor.rowcount
    finally:
        cursor.close()


# Inserciones (INSERT) devolviendo el ID generado
def insert(sql, params=()):
    cursor = get_db().cursor()
    try:
        cursor.execute(sql, params)
        return cursor.lastrowid
    finally:
        cursor.close()


# Control de transacciones con commit y rollback automatico
@contextmanager
def transaction():
    if g.get("_transaccion_activa"):
        raise RuntimeError("Agrupa las escrituras relacionadas en una sola transacción.")
    conexion = get_db()
    g._transaccion_activa = True
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        g.pop("_transaccion_activa", None)


# Traduce codigos de error de MariaDB (triggers y restricciones) a mensajes claros
def mensaje_error(error):
    codigo = error.args[0] if error.args else None
    if codigo == 1644:
        return str(error.args[1]) if len(error.args) > 1 else "La operación no cumple una regla de negocio."
    if codigo == 1062:
        return "Ya existe un registro con esos datos."
    if codigo in (1451, 1452):
        return "La operación no es válida por los datos relacionados."
    if codigo == 4025:
        return "Un dato no cumple una regla de la base de datos."
    return "Ocurrió un error en la base de datos."
