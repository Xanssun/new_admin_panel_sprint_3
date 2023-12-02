from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor


@contextmanager
def pg_connector(pg_conf: dict):
    conn = psycopg2.connect(**pg_conf, cursor_factory=DictCursor)
    yield conn
    conn.close()


@contextmanager
def pg_cursor(conn: psycopg2.connect):
    cursor = conn.cursor()
    yield cursor
    cursor.close()
