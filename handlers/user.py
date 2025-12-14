import binascii
from typing import Callable, Optional

from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, ErrorEvent, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.payload import decode_payload
import logging
import shutil
import subprocess
from pathlib import Path

from callbacks.track import SpotifyTrackCB, SpotifyTrackCBActions
from config import DOWNLOADS_DIR_PATH, SPOTIFY_TRACK_URL_REGEX
from enums.payload_command import PayloadCommand
from errors import DownloadError, DownloadedFilesNotFound
from keyboards.track import spotify_track_kb
from services.spotify import SpotifyClient, SpotifyTrack, SpotifyAlbum
from utils.download import download_track_spotify, DownloadedTrackFile

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

        if payload_command == PayloadCommand.TRACK:
            if payload_data_len > 0:
                await search_track_handler(message, payload_data[0])
    else:
        await message.reply("Команда не найдена!")


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🎵 *Добро пожаловать!*\n\n"
        "Просто отправь мне название песни, и я найду информацию о ней."
    )


async def process_spotify_track(
        spotify_url: str,
        send_audio: Callable,
        send_text: Callable
    ):
    await send_text(
        "🔍 Начинаю обработку ссылки Spotify...\n"
        "⏳ Скачивание трека (это может занять 30–60 секунд)"
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
    except subprocess.TimeoutExpired:
        await send_text("❌ Скачивание заняло слишком много времени")
    except DownloadError:
        raise
    except DownloadedFilesNotFound:
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

@router.message(F.text)
async def search_track_handler(message: Message, track_id: Optional[str] = None):
    spotify_client = SpotifyClient()

    if track_id:
        tracks: list[SpotifyTrack] = [spotify_client.search_track_by_id(track_id)]
    else:
        tracks: list[SpotifyTrack] = spotify_client.search_track(message.text, limit=1)

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

        text = (
            f"🎶 *{track.name}* 🎶\n\n"

            f"✨ ━━━━━━━━━━━━━━━━━ ✨\n\n"

            f"🎤 *{'Исполнители' if artists_len > 1 else 'Исполнитель'}:*\n"
            f"{artists_str}\n\n"

            f"💿 *Альбом:* {track.album.name}\n"
            f"📅 *Дата релиза:* {track.release_date}\n"
            f"⏳ *Длительность:* {track.duration}\n\n"

            f"✨ ━━━━━━━━━━━━━━━━━ ✨"
        )

        await message.answer_photo(
            photo=track.image_url,
            caption=text,
            reply_markup=spotify_track_kb(track)
        )


# @router.message(F.text)
async def search_album_handler(message: Message, album_id: Optional[str] = None):
    spotify_client = SpotifyClient()

    if album_id:
        albums: list[SpotifyAlbum] = [spotify_client.search_album_by_id(album_id)]
    else:
        albums: list[SpotifyAlbum] = spotify_client.search_album(message.text, limit=1)

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

        text = (
            f"🎶 *{album.name}* 🎶\n\n"

            f"✨ ━━━━━━━━━━━━━━━━━ ✨\n\n"

            f"🎤 *{'Исполнители' if artists_len > 1 else 'Исполнитель'}:*\n"
            f"{artists_str}\n\n"

            f"💿 *Альбом:* {album.name}\n"
            f"📅 *Дата релиза:* {album.release_date}\n"
            f"⏳ *Треков:* {album.total_tracks}\n\n"

            f"✨ ━━━━━━━━━━━━━━━━━ ✨"
        )

        await message.answer_photo(
            photo=album.image_url,
            caption=text
        )


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

    await callback.answer()


@router.errors()
async def global_error_handler(event: ErrorEvent):
    if event.update.message:
        try:
            await event.update.message.answer("Произошла ошибка, попробуйте позже...")
        except Exception:
            pass

    logger.exception("Ошибка в обработчике:", exc_info=event.exception)
