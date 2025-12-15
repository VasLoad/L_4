import binascii
from typing import Callable, Optional

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, BufferedInputFile, ErrorEvent, CallbackQuery
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.utils.payload import decode_payload
import logging
import shutil
import subprocess
from pathlib import Path

from callbacks.track import SpotifyTrackCB, SpotifyTrackCBActions
from config import DOWNLOADS_DIR_PATH, SPOTIFY_TRACK_URL_REGEX, config
from enums.payload_command import PayloadCommand
from errors import DownloadError, DownloadedFilesNotFoundError
from keyboards.album import spotify_album_kb
from keyboards.track import spotify_track_kb
from services.spotify import SpotifyTrack, SpotifyAlbum, spotify_client
from utils.content_message_text import ContentMessageTextTrack, ContentMessageTextAlbum, ContentMessageTextCommandError
from utils.downloads import download_track_spotify, DownloadedTrackFile


class MessageCommandAndArgs:
    def __init__(self, text: str):
        self.__text = text

        self.__command: Optional[str] = None
        self.__args: list[str] = []

        self.__command_only: Optional[bool] = None

        self.__parse()

    @property
    def text(self) -> str:
        return self.__text

    @property
    def command(self) -> Optional[str]:
        return self.__command

    @property
    def args(self) -> list[str]:
        return self.__args

    @property
    def args_str(self) -> str:
        return " ".join(self.__args)

    @property
    def command_only(self) -> Optional[bool]:
        return self.__command_only

    def __parse(self):
        parsed = self.__text.split(" ")

        parsed_len = len(parsed)

        if parsed_len > 0:
            self.__command = parsed.pop(0)

            parsed_len -=1

        self.__args = parsed

        self.__command_only = bool(parsed_len <= 0)


router = Router()

logger = logging.getLogger(__name__)


@router.message(CommandStart(deep_link=True))
async def handle_deep_link(message: Message, command: CommandObject):
    raw_payload = command.args

    if not raw_payload:
        await message.answer("Некорректная ссылка!")
        return

    try:
        payload = decode_payload(raw_payload)
    except (UnicodeDecodeError, binascii.Error):
        payload = raw_payload

    payload_data = payload.split("_")

    payload_data_len = len(payload_data)

    if payload_data_len > 0:
        payload_command = payload_data.pop(0)

        payload_data_len = len(payload_data)

        if payload_data_len > 0:
            if payload_command == PayloadCommand.TRACK:
                await search_track_handler(message, payload_data[0])

                return
            elif payload_command == PayloadCommand.ALBUM:
                await search_album_handler(message, payload_data[0])

                return

    await message.reply("Команда не найдена!")


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привет!"
        "\nЧтобы получить *информацию о треке*, отправь в чат его *название*!"
        "\nИли воспользуйся командой /menu"
    )


async def process_spotify_track(
        spotify_url: str,
        send_audio: Callable,
        send_text: Callable
    ):

    temp_message: Message = await send_text(
        "⏳ Скачивание трека"
        "\nЭто может занять некоторое время..."
    )

    download_dir = Path(DOWNLOADS_DIR_PATH)
    download_dir.mkdir(parents=True, exist_ok=True)

    try:
        track: DownloadedTrackFile = download_track_spotify(
            spotify_url,
            str(download_dir)
        )

        await send_audio(
            audio=BufferedInputFile(track.file_bytes, filename=track.filename),
            title=track.title,
            performer="Spotify"
        )

        await temp_message.delete()
    except subprocess.TimeoutExpired:
        await send_text("❌ Скачивание заняло слишком много времени")
    except DownloadError:
        raise
    except DownloadedFilesNotFoundError:
        raise
    finally:
        for item in download_dir.iterdir():
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)


@router.message(F.text.regexp(SPOTIFY_TRACK_URL_REGEX))
async def handler_download_track_spotify(message: Message):
    spotify_url = message.text.strip()

    await process_spotify_track(
        spotify_url=spotify_url,
        send_text=message.answer,
        send_audio=message.answer_audio
    )


async def search_track_handler(message: Message, query: Optional[str] = None, track_id: Optional[str] = None):
    if track_id:
        tracks: list[SpotifyTrack] = [spotify_client.search_track_by_id(track_id)]
    else:
        if not query:
            query = message.text

        tracks: list[SpotifyTrack] = spotify_client.search_track(query, limit=1)

    for track in tracks:
        if not track:
            await message.answer("❌ Песня не найдена")

            continue

        artists_len = len(track.artists)

        artists_str = ""

        for index, artist in enumerate(track.artists):
            artists_str += f"   {artist.name}"

            if index < artists_len - 1:
                artists_str += "\n"

        text = ContentMessageTextTrack(track).text

        await message.answer_photo(
            photo=track.image_url,
            caption=text,
            reply_markup=spotify_track_kb(track)
        )


async def search_album_handler(message: Message, query: Optional[str] = None, album_id: Optional[str] = None):
    if album_id:
        albums: list[SpotifyAlbum] = [spotify_client.search_album_by_id(album_id)]
    else:
        if not query:
            query = message.text

        albums: list[SpotifyAlbum] = spotify_client.search_album(query, limit=1)

    for album in albums:
        if not album:
            await message.answer("❌ Альбомы не найдены")

            continue

        artists_len = len(album.artists)

        artists_str = ""

        for index, artist in enumerate(album.artists):
            artists_str += f"   {artist.name}"

            if index < artists_len - 1:
                artists_str += "\n"

        text = ContentMessageTextAlbum(album).text

        # await message.edit_caption(
        #     caption=text,
        #     reply_markup=spotify_album_kb(album)
        # )

        await message.answer_photo(
            photo=album.image_url,
            caption=text,
            reply_markup=spotify_album_kb(album)
        )


@router.message(Command("track"))
async def track_command(message: Message):
    message_data = MessageCommandAndArgs(message.text)

    if not message_data.command_only:
        await search_track_handler(message, query=message_data.args_str)
    else:
        await message.reply(
            ContentMessageTextCommandError(
                "/track",
                ("<название трека>", "<исполнитель (опционально)>")
            ).text
        )


@router.message(Command("album"))
async def track_command(message: Message):
    message_data = MessageCommandAndArgs(message.text)

    if not message_data.command_only:
        await search_album_handler(message, query=message_data.args_str)
    else:
        await message.reply(
            ContentMessageTextCommandError(
                "/album",
                ("<название альбома>", "<исполнители (опционально)>")
            ).text
        )


@router.message(F.text)
async def message_handler(message: Message):
    if message.text[0] == "/":
        await message.reply("Команда не найдена.")
    else:
        await search_track_handler(message)


@router.callback_query(SpotifyTrackCB.filter())
async def spotify_track_handler(callback: CallbackQuery, callback_data: SpotifyTrackCB):
    spotify_url = f"https://open.spotify.com/track/{callback_data.track_id}"

    match callback_data.action:
        case SpotifyTrackCBActions.ALBUM:
            await search_album_handler(callback.message, album_id=callback_data.album_id)
        case SpotifyTrackCBActions.DOWNLOAD:
            await process_spotify_track(
                spotify_url=spotify_url,
                send_text=callback.message.answer,
                send_audio=callback.message.answer_audio
            )

    try:
        await callback.answer()
    except TelegramBadRequest:
        pass


@router.errors()
async def global_error_handler(event: ErrorEvent):
    if event.update.message:
        try:
            await event.update.message.answer("Произошла ошибка, попробуйте позже...")
        except Exception:
            pass

    logger.exception("Ошибка в обработчике:", exc_info=event.exception)
