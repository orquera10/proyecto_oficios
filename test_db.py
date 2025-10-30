import os
from urllib.parse import urlparse

import psycopg2
from psycopg2 import OperationalError


def _config_from_env():
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        url = urlparse(dsn)
        return {
            "dbname": (url.path[1:] or os.getenv("DB_NAME", "postgres")),
            "user": (url.username or os.getenv("DB_USER", "postgres")),
            "password": (url.password or os.getenv("DB_PASSWORD", "")),
            "host": (url.hostname or os.getenv("DB_HOST", "localhost")),
            "port": (str(url.port) if url.port else os.getenv("DB_PORT", "5432")),
        }

    return {
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
    }


def test_connection():
    cfg = _config_from_env()
    try:
        conn = psycopg2.connect(
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            host=cfg["host"],
            port=cfg["port"],
            connect_timeout=5,
        )

        print("Conexión exitosa a PostgreSQL!")
        print("Host:", cfg["host"], "Puerto:", cfg["port"], "DB:", cfg["dbname"])
        print("Versión del servidor:", conn.server_version)
        conn.close()
        return True
    except OperationalError as e:
        print("Error al conectarse a la base de datos:", e)
        return False


if __name__ == "__main__":
    test_connection()

