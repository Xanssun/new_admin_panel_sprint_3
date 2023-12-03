import json
from functools import wraps

from elasticsearch import Elasticsearch


def coroutine(func):
    @wraps(func)
    def inner(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn

    return inner


def preprocess_rows(rows):
    return tuple([row['id'] for row in rows], )


def create_index_if_not_exists(client: Elasticsearch,
                               index_path: str, index_name: str):
    if not client.indices.exists(index="movies"):
        with open(index_path, "r") as fp:
            client.indices.create(
                index=index_name,
                body=json.load(fp)
            ) 
