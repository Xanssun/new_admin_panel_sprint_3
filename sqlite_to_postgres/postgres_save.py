from psycopg2.extensions import connection as _connection


class PostgresSaver:
    def __init__(self, pg_conn: _connection, batch_size):
        self.pg_conn = pg_conn
        self.batch_size = batch_size

    def save_movies(self, movies):
        movie_chunks = [movies[i:i + self.batch_size] for i in (
            range(0, len(movies), self.batch_size))]

        with self.pg_conn.cursor() as pg_cursor:
            for movie_chunk in movie_chunks:
                pg_cursor.executemany(
                    """
                    INSERT INTO content.film_work (id, title, description,
                    creation_date, rating, type, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    [
                        (str(movie.id), movie.title, movie.description,
                         movie.creation_date, movie.rating, movie.type,
                         movie.created_at, movie.updated_at)
                        for movie in movie_chunk
                    ]
                )
        self.pg_conn.commit()

    def save_genres(self, genres):
        genre_chunks = [genres[i:i + self.batch_size] for i in (
            range(0, len(genres), self.batch_size))]

        with self.pg_conn.cursor() as pg_cursor:
            for genre_chunk in genre_chunks:
                pg_cursor.executemany(
                    """
                    INSERT INTO content.genre (id, name, description,
                    created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    [
                        (str(genre.id), genre.name, genre.description,
                         genre.created_at, genre.updated_at)
                        for genre in genre_chunk
                    ]
                )
        self.pg_conn.commit()

    def save_persons(self, persons):
        person_chunks = [persons[i:i + self.batch_size] for i in (
            range(0, len(persons), self.batch_size))]

        with self.pg_conn.cursor() as pg_cursor:
            for person_chunk in person_chunks:
                pg_cursor.executemany(
                    """
                    INSERT INTO content.person (id, full_name,
                    created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    [
                        (str(person.id), person.full_name, person.created_at,
                         person.updated_at)
                        for person in person_chunk
                    ]
                )
        self.pg_conn.commit()

    def save_genre_film_work(self, genre_film_works):
        genre_film_work_chunks = (
            [genre_film_works[i:i + self.batch_size] for i in (
                range(0, len(genre_film_works), self.batch_size))]
        )

        with self.pg_conn.cursor() as pg_cursor:
            for genre_film_work_chunk in genre_film_work_chunks:
                pg_cursor.executemany(
                    """
                    INSERT INTO content.genre_film_work (id, genre_id,
                    film_work_id, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    [
                        (str(genre_film_work.id),
                         str(genre_film_work.genre_id),
                         str(genre_film_work.film_work_id),
                         genre_film_work.created_at)
                        for genre_film_work in genre_film_work_chunk
                    ]
                )
        self.pg_conn.commit()

    def save_person_film_work(self, person_film_works):
        person_film_work_chunks = (
            [person_film_works[i:i + self.batch_size] for i in (
                range(0, len(person_film_works), self.batch_size))]
        )

        with self.pg_conn.cursor() as pg_cursor:
            for person_film_work_chunk in person_film_work_chunks:
                pg_cursor.executemany(
                    """
                    INSERT INTO content.person_film_work (id, person_id,
                    film_work_id, role, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    [
                        (str(person_film_work.id),
                         str(person_film_work.person_id),
                         str(person_film_work.film_work_id),
                         person_film_work.role,
                         person_film_work.created_at)
                        for person_film_work in person_film_work_chunk
                    ]
                )
        self.pg_conn.commit()

    def save_data(self, movies, genres, persons,
                  genre_film_works, person_film_works):
        self.save_movies(movies)
        self.save_genres(genres)
        self.save_persons(persons)
        self.save_genre_film_work(genre_film_works)
        self.save_person_film_work(person_film_works)
