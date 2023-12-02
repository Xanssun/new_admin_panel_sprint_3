import sqlite3
import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
from copy_bd import SQLiteLoader
from postgres_save import PostgresSaver
from variables import batch_size, db_path
import os
from dotenv import load_dotenv, find_dotenv
from contextlib import closing

load_dotenv(find_dotenv())


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    sqlite_loader = SQLiteLoader(db_path, batch_size)
    postgres_saver = PostgresSaver(pg_conn, batch_size)
    (movies, genres, persons, genre_film_works,
     person_film_works) = sqlite_loader.load_data()
    postgres_saver.save_data(movies, genres, persons,
                             genre_film_works, person_film_works)


if __name__ == '__main__':
    dsl = {
        'dbname': os.getenv("PG_NAME"),
        'user': os.getenv("PG_USER"),
        'password': os.getenv("PG_PASSWORD"),
        'host': os.getenv("PG_HOST"),
        'port': os.getenv("PG_PORT")
    }
    with closing(sqlite3.connect('db.sqlite')) as sqlite_conn, (
            closing(psycopg2.connect(**dsl,
                                     cursor_factory=DictCursor))) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
