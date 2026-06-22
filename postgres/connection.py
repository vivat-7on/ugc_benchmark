from contextlib import contextmanager

import psycopg2
from psycopg2.extras import register_uuid


@contextmanager
def get_postgres_connection():
    connection = psycopg2.connect(
        database="postgres",
        user="postgres",
        password="password",
        host="localhost",
        port="5432",
        )

    register_uuid(conn_or_curs=connection)
    try:
        yield connection
    finally:
        connection.close()
