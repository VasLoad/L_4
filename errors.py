from pathlib import Path
from typing import Union, Optional

import requests


class DownloadsError(Exception):
    """Базовые исключения, связанные со скачиванием."""

    pass


class DownloadError(DownloadsError):
    """Ошибка скачивания."""

    def __init__(self, url: str):
        super().__init__(f"Ошибка при скачивании с ресурса: {url}.")


class DownloadedFilesNotFoundError(DownloadsError):
    """Скачанные файлы не найдены."""

    def __init__(self, file_paths: list[Union[str, Path]]):
        file_paths_str = ""

        file_paths_len = len(file_paths)

        for index, file_path in enumerate(file_paths):
            file_paths_str += file_path

            if index < file_paths_len - 1:
                file_paths_str += ", "

        super().__init__(f"Скачанные файлы не найдены: {file_paths_str}.")


class RemoteError(Exception):
    """Базовые исключения, связанные с удалёнными запросами."""

    pass


class RemoteTimeoutError(RemoteError):
    def __init__(self):
        super().__init__("Превышено время ожидания ответа.")


class RemoteConnectionError(RemoteError):
    def __init__(self):
        super().__init__("Ошибка подключения.")


class RemoteHTTPError(RemoteError):
    def __init__(self, exception: requests.exceptions.HTTPError):
        super().__init__(f"Ошибка HTTP-запроса.\nКод ошибки: {getattr(exception.response, "status_code")}.\nТекст ошибки: {str(exception)}")


class RemoteRequestException(RemoteError):
    def __init__(self, exception_text: str):
        super().__init__(f"Ошибка запроса.\nТекст ошибки: {exception_text}")


class RemoteResponseDataError(RemoteError):
    def __init__(self, exception_text: str, response: Optional[str] = None):
        super().__init__(f"Сервер вернул некорректные данные.\nТекст ошибки: {exception_text}.{f'\nПолученные данные: {response}.' if response else ''}")
