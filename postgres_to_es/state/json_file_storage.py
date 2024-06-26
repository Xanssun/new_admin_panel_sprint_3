import json

from .base_storage import BaseStorage


class JsonFileStorage(BaseStorage):
    """Реализация хранилища, использующего локальный файл.

    Формат хранения: JSON
    """

    def __init__(self, file_path: str = "storage.json") -> None:
        self.file_path = file_path

    def save_state(self, state: dict) -> None:
        """Сохранить состояние в хранилище."""
        try:
            prev_key, prev_val = self.retrieve_state().popitem()
        except KeyError:
            with open(self.file_path, 'w') as f:
                json.dump(state, f)
        else:
            if prev_val < state[prev_key]:
                with open(self.file_path, 'w') as f:
                    json.dump(state, f)

    def retrieve_state(self) -> dict:
        """Получить состояние из хранилища."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
