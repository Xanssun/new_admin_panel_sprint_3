from typing import Generator

from elasticsearch import Elasticsearch, helpers

from config.choices import Tables
import logging
from config.pg_connection_helpers import pg_cursor
from config.utils import coroutine, preprocess_rows
from settings import NUMBER_OF_FETCHED, STATE_KEY
from state.models import MovieRow, State

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)


class ETLWorker:

    def __init__(self, connection):
        self.connection = connection

    @coroutine
    def producer(self, next_node: Generator):
        """Производит извлечение изменений и отправляет их следующему узлу."""
        while producer_args := (yield):
            last_updated_at, table = producer_args
            self.fetch_and_send_changes(last_updated_at, table, next_node)

    @coroutine
    def enricher(self, next_node: Generator, save_state: Generator):
        """Обогащает изменения данными и отправляет их следующему узлу."""
        while enricher_args := (yield):
            table, rows = enricher_args
            last_updated_at = rows[-1]['updated_at']
            if table == Tables.FILM_WORK.value:
                self.save_and_send_state(table, last_updated_at, save_state)
                next_node.send((rows, last_updated_at))
            else:
                self.enrich_changes(table, rows, last_updated_at,
                                    next_node, save_state)

    @coroutine
    def merger(self, next_node: Generator):
        """Объединяет изменения и отправляет их следующему узлу."""
        while merger_args := (yield):
            rows, last_updated_at = merger_args
            self.merge_changes(rows, last_updated_at, next_node)

    @coroutine
    def transform_movies(self, next_node: Generator):
        """Преобразует фильмы и отправляет их следующему узлу."""
        while transform_args := (yield):
            movie_dicts, last_updated_at = transform_args
            self.transform_and_send_movies(movie_dicts,
                                           last_updated_at, next_node)

    @coroutine
    def load_movies_to_elasticsearch(self, client: Elasticsearch,
                                     save_state_coro: Generator):
        """Загружает фильмы в Elasticsearch и
        отправляет состояние сохранения."""
        while loader_args := (yield):
            movies = loader_args[0]
            self.load_to_elasticsearch(client, movies, save_state_coro)

    @coroutine
    def save_state_coro(self, state: State):
        """Сохраняет состояние и логирует его."""
        while state_saver_args := (yield):
            key_to_save, last_updated_at_to_save = state_saver_args
            send_to_save = (yield)
            if send_to_save:
                self.log_and_save_state(state, last_updated_at_to_save)

    def fetch_and_send_changes(self, last_updated_at: str, table: str, next_node: Generator) -> None:
        """Извлекает изменения из таблицы и отправляет их следующему узлу."""
        logger.info("Extracting changes from a table %s", table)
        sql = f'''
        SELECT id, updated_at
        FROM content.{table}
        WHERE updated_at > %s
        ORDER BY updated_at
        '''
        with pg_cursor(self.connection) as cursor:
            cursor.execute(sql, (last_updated_at,))
            while rows := cursor.fetchmany(NUMBER_OF_FETCHED):
                next_node.send((table, rows))

    def save_and_send_state(self, table: str, last_updated_at: str, save_state: Generator) -> None:
        """Сохраняет состояние и отправляет его следующему узлу."""
        save_state.send((table, last_updated_at))

    def enrich_changes(self, table: str, rows: list, last_updated_at: str,
                       next_node: Generator, save_state: Generator) -> None:
        """Обогащает изменения и отправляет их следующему узлу."""
        logger.info("Enriching changes from the table %s", table)
        sql = f'''
        SELECT fw.id, fw.updated_at
        FROM content.film_work fw
        LEFT JOIN content.{table}_film_work afw ON afw.film_work_id = fw.id
        WHERE afw.{table}_id IN %s
        ORDER BY fw.updated_at
        '''
        rows = preprocess_rows(rows)
        with pg_cursor(self.connection) as cursor:
            cursor.execute(sql, (rows,))
            while rows := cursor.fetchmany(NUMBER_OF_FETCHED):
                save_state.send((table, last_updated_at))
                next_node.send((rows, last_updated_at))

    def merge_changes(self, rows: list, last_updated_at: str, next_node: Generator) -> None:
        """Объединяет изменения и отправляет их следующему узлу."""
        logger.info("Merging changes")
        sql_ = '''
        SELECT
            fw.id,
            fw.rating as imdb_rating,
            fw.title,
            fw.description,
            fw.type,
            COALESCE (
               json_agg(
                   DISTINCT jsonb_build_object(
                       'id', g.id,
                       'name', g.name
                   )
               ) FILTER (WHERE g.id is not null),
               '[]'
            ) as genres,
            COALESCE (
               json_agg(
                   DISTINCT jsonb_build_object(
                       'id', p.id,
                       'name', p.full_name
                   )
               ) FILTER (WHERE p.id is not null AND pfw.role = 'director'),
               '[]'
            ) as directors,
            COALESCE (
               json_agg(
                   DISTINCT jsonb_build_object(
                       'id', p.id,
                       'name', p.full_name
                   )
               ) FILTER (WHERE p.id is not null AND pfw.role = 'actor'),
               '[]'
            ) as actors,
            COALESCE (
               json_agg(
                   DISTINCT jsonb_build_object(
                       'id', p.id,
                       'name', p.full_name
                   )
               ) FILTER (WHERE p.id is not null AND pfw.role = 'writer'),
               '[]'
            ) as writers
        FROM
            content.film_work fw
        LEFT JOIN
            content.person_film_work pfw ON pfw.film_work_id = fw.id
        LEFT JOIN
            content.person p ON p.id = pfw.person_id
        LEFT JOIN
            content.genre_film_work gfw ON gfw.film_work_id = fw.id
        LEFT JOIN
            content.genre g ON g.id = gfw.genre_id
        WHERE
           fw.id IN %s
        GROUP BY
            fw.id;
        '''
        rows = preprocess_rows(rows)
        with pg_cursor(self.connection) as cursor:
            cursor.execute(sql_, (rows,))
            while rows := cursor.fetchmany(NUMBER_OF_FETCHED):
                next_node.send((rows, last_updated_at))

    def transform_and_send_movies(self, movie_dicts: list,
                                  last_updated_at: str, next_node: Generator) -> None:
        """Преобразует фильмы и отправляет их следующему узлу."""
        logger.info("Converting movies from PostgreSQL")
        batch = []
        for movie_dict in movie_dicts:
            movie = MovieRow(**movie_dict)
            movie.transform()
            batch.append(movie)
        next_node.send((batch, last_updated_at))

    def load_to_elasticsearch(self, client: Elasticsearch, movies: list,
                              save_state_coro: Generator) -> None:
        """Загружает фильмы в Elasticsearch и
        отправляет состояние сохранения."""
        logger.info("Uploading %d movies to ElasticSearch", len(movies))
        data = [{
            "_index": "movies",
            "_id": row.id,
            "_source": {
                "id": row.id,
                "imdb_rating": row.imdb_rating,
                "title": row.title,
                "description": row.description,
                "genre": row.genres_names,
                "actors_names": row.actors_names,
                "writers_names": row.writers_names,
                "director": row.directors_names,
                "actors": [dict(actor) for actor in row.actors],
                "writers": [dict(writer) for writer in row.writers],
            }
        } for row in movies]
        _, errors = helpers.bulk(client, actions=data)
        save_state_coro.send(not errors)

    def log_and_save_state(self, state: Generator, last_updated_at_to_save: str) -> None:
        """Логирует и сохраняет состояние."""
        logger.info("The last state: %s: %s",
                    STATE_KEY, state.get_state(STATE_KEY))
        state.set_state(f"{STATE_KEY}", last_updated_at_to_save)
