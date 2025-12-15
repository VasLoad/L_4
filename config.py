import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Настройки проекта."""

    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")

    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET")


config = Config()

SPOTIFY_TRACK_URL_REGEX = r"https?://open\.spotify\.com/track/"
URL_QUOTE_REGEX = r"%[0-9A-Fa-f]{2}"

EMPTY_CONTENT_TEXT = "Неизвестно"

HANDLER_ERROR_MESSAGE_TEXT = "Произошла ошибка, попробуйте позже..."
HANDLER_ERROR_LOGGER_TEXT = "Ошибка в обработчике:"

STORAGE_DIR_PATH = "./storage/"

DATA_DIR_PATH = STORAGE_DIR_PATH + "data/"

TEMP_DIR_PATH = STORAGE_DIR_PATH + "temp/"

DOWNLOADS_DIR_PATH = TEMP_DIR_PATH + "downloads/"

LOGS_DIR_PATH = DATA_DIR_PATH + "logs/"

LOGS_FILE_PATH = LOGS_DIR_PATH + "logs.log"
