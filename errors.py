from pathlib import Path
from typing import Union


class Downloads(Exception):
    """Базовые исключения, связанные со скачиванием."""

    pass


class DownloadError(Downloads):
    """Ошибка скачивания."""

    def __init__(self, url: str):
        super().__init__(f"Ошибка при скачивании с ресурса: {url}.")


class DownloadedFilesNotFound(Downloads):
    """Скачанные файлы не найдены."""

    def __init__(self, file_paths: list[Union[str, Path]]):
        file_paths_str = ""

        file_paths_len = len(file_paths)

        for index, file_path in enumerate(file_paths):
            file_paths_str += file_path

            if index < file_paths_len - 1:
                file_paths_str += ", "

        super().__init__(f"Скачанные файлы не найдены: {file_paths_str}.")
