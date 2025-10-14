import psycopg2
from psycopg2 import OperationalError

def test_connection():
    try:
        # Reemplaza estos valores con los de tu configuración
        conn = psycopg2.connect(
            dbname="oficios",  # Nombre de la base de datos (por defecto es 'postgres')
            user="postgres",    # Usuario (por defecto es 'postgres')
            password="tuxx6393",  # La contraseña que configuraste
            host="localhost",   # Servidor (local por defecto)
            port="5433"         # Puerto por defecto de PostgreSQL
        )
        
        print("¡Conexión exitosa a PostgreSQL!")
        print(f"Versión del servidor: {conn.server_version}")
        
        # Cerrar la conexión
        conn.close()
        return True
        
    except OperationalError as e:
        print(f"Error al conectarse a la base de datos: {e}")
        return False

if __name__ == "__main__":
    test_connection()