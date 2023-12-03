from datetime import datetime
from time import sleep

import backoff
import elastic_transport
import psycopg2
from elasticsearch import Elasticsearch

from config.choices import Tables
import logging
from config.pg_connection_helpers import pg_connector
from config.utils import create_index_if_not_exists
from config.worker import ETLWorker
from settings import (ELASTIC_CLIENT, INDEX_NAME, INDEX_PATH, PG_CONF,
                      REFRESH_INTERVAL, STATE_KEY, STATE_PATH)
from state.json_file_storage import JsonFileStorage
from state.models import State

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)


@backoff.on_exception(backoff.constant,
                      (psycopg2.OperationalError,
                       elastic_transport.ConnectionError), max_tries=1000)
def start_etl_process(etl_worker, producer, state):
    """Запускает процесс ETL, извлекая, обогащая,
    объединяя, преобразуя и загружая данные."""
    while True:
        for table in Tables:
            logger.info('Starting the ETL process for the table %s', table.value)
            producer.send((state.get_state(STATE_KEY)
                           or str(datetime.min), table.value))

        sleep(REFRESH_INTERVAL)


def main():
    """Основная функция, инициализирующая и запускающая ETL-процесс."""
    logger.info("Initializing the state")
    state = State(JsonFileStorage(STATE_PATH))

    sleep(10)
    es_client = Elasticsearch(ELASTIC_CLIENT['host'])

    logger.info("Creating an ES index if there is none")
    create_index_if_not_exists(es_client,
                               index_path=INDEX_PATH,
                               index_name=INDEX_NAME)

    logger.info("Connecting to PostgreSQL")
    with pg_connector(PG_CONF) as conn:
        etl_worker = ETLWorker(conn)
        logger.info("Initialization")

        state_saver_ = etl_worker.save_state_coro(state)
        loader_ = etl_worker.load_movies_to_elasticsearch(es_client,
                                                          state_saver_)
        transformer_ = etl_worker.transform_movies(next_node=loader_)
        merger_ = etl_worker.merger(next_node=transformer_)
        enricher_ = etl_worker.enricher(next_node=merger_,
                                        save_state=state_saver_)
        producer_ = etl_worker.producer(next_node=enricher_)

        start_etl_process(etl_worker, producer_, state)


if __name__ == '__main__':
    main()
