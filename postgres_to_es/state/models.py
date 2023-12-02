import uuid
from typing import Any

from pydantic import BaseModel

from .base_storage import BaseStorage


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage
        self.value = {}

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа."""
        state = {key: str(value)}
        self.storage.save_state(state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""
        states = self.storage.retrieve_state()
        return states.get(key)


class UUIDMixIn(BaseModel):
    id: uuid.UUID


class Person(UUIDMixIn):
    name: str


class Genre(UUIDMixIn):
    name: str


class MovieRow(UUIDMixIn):
    imdb_rating: float | None
    title: str
    description: str | None
    type: str | None
    genres_names: list[str] | None
    genres: list[Genre]
    directors_names: list[str] | None
    directors: list[Person]
    actors_names: list[str] | None
    actors: list[Person]
    writers_names: list[str] | None
    writers: list[Person]

    def _get_names(self, names: list[Person | Genre]):
        return [i.name for i in names]

    def transform(self):
        self.genres_names = self._get_names(self.genres)
        self.directors_names = self._get_names(self.directors)
        self.actors_names = self._get_names(self.actors)
        self.writers_names = self._get_names(self.writers)
