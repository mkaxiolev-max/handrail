import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ns:ns_secure_pwd@localhost:5433/ns"
)

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def get_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)
