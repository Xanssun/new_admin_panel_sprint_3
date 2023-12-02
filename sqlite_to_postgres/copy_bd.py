import sqlite3
from contextlib import contextmanager
from data_clases import Filmwork, Genre, GenreFilmWork, Person, PersonFilmWork


class SQLiteLoader:
    def __init__(self, db_path, batch_size):
        self.db_path = db_path
        self.batch_size = batch_size

    @contextmanager
    def conn_context(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        curs = conn.cursor()
        yield conn, curs
        conn.close()

    def load_table(self, table_name, data_class):
        with self.conn_context() as (conn, curs):
            curs.execute(f"SELECT * FROM {table_name};")
            while (rows := curs.fetchmany(self.batch_size)):
                for row in rows:
                    item = data_class(**dict(row))
                    yield item

    def load_movies(self):
        return self.load_table("film_work", Filmwork)

    def load_genres(self):
        return self.load_table("genre", Genre)

    def load_persons(self):
        return self.load_table("person", Person)

    def load_genre_film_work(self):
        return self.load_table("genre_film_work", GenreFilmWork)

    def load_person_film_work(self):
        return self.load_table("person_film_work", PersonFilmWork)

    def load_data(self):
        movies = list(self.load_movies())
        genres = list(self.load_genres())
        persons = list(self.load_persons())
        genre_film_works = list(self.load_genre_film_work())
        person_film_works = list(self.load_person_film_work())
        return movies, genres, persons, genre_film_works, person_film_works
