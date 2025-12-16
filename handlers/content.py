import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, CallbackQuery

from callbacks.track import SpotifyTrackCB, SpotifyTrackCBActions
from config import DOWNLOADS_DIR_PATH, SPOTIFY_TRACK_URL_REGEX
from enums.command_name import CommandName
from enums.db_settings_param_name import DBSettingsParamName
from errors import DownloadError, DownloadedFilesNotFoundError
from keyboards.album import spotify_album_kb
from keyboards.track import spotify_track_kb
from services.db import UserSettingsRepository, db_sender
from services.spotify import SpotifyTrack, SpotifyAlbum, spotify_client
from utils.downloads import download_track_spotify, DownloadedTrackFile
from utils.message_text import ContentMessageTextTrack, ContentMessageTextAlbum, MessageTextCommandError, MessageCommandAndArgs

router = Router()


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

        db_user_settings_repo = UserSettingsRepository(db_sender)

        send_information_image: bool = db_user_settings_repo.get_settings_param_value(
            message.from_user.id,
            DBSettingsParamName.SEND_INFORMATION_IMAGE
        )

        if send_information_image:
            await message.answer_photo(
                photo=track.image_url,
                caption=text,
                reply_markup=spotify_track_kb(track)
            )
        else:
            await message.answer(
                text=text,
                reply_markup=spotify_track_kb(track)
            )


async def search_album_handler(
        message: Message, query: Optional[str] = None,
        album_id: Optional[str] = None,
        user_id: Optional[int] = None
):
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

        db_settings_repo = UserSettingsRepository(db_sender)

        send_information_image: bool = db_settings_repo.get_settings_param_value(
            user_id if user_id else message.from_user.id,
            DBSettingsParamName.SEND_INFORMATION_IMAGE
        )

        if send_information_image:
            await message.answer_photo(
                photo=album.image_url,
                caption=text,
                reply_markup=spotify_album_kb(album)
            )
        else:
            await message.answer(
                text=text,
                reply_markup=spotify_album_kb(album),
                disable_web_page_preview=True
            )


@router.message(Command(CommandName.TRACK))
async def track_command(message: Message):
    message_data = MessageCommandAndArgs(message.text)

    if not message_data.command_only:
        await search_track_handler(message, query=message_data.args_str)
    else:
        await message.reply(
            MessageTextCommandError(
                f"/{CommandName.TRACK}",
                ("<название трека>", "<другие параметры (опционально)>")
            ).text
        )


@router.message(Command(CommandName.ALBUM))
async def track_command(message: Message):
    message_data = MessageCommandAndArgs(message.text)

    if not message_data.command_only:
        await search_album_handler(message, query=message_data.args_str)
    else:
        await message.reply(
            MessageTextCommandError(
                f"/{CommandName.ALBUM}",
                ("<название альбома>", "<исполнители (опционально)>")
            ).text
        )


@router.callback_query(SpotifyTrackCB.filter())
async def spotify_track_handler(callback: CallbackQuery, callback_data: SpotifyTrackCB):
    spotify_url = f"https://open.spotify.com/track/{callback_data.track_id}"

    match callback_data.action:
        case SpotifyTrackCBActions.ALBUM:
            await search_album_handler(callback.message, user_id=callback.from_user.id, album_id=callback_data.album_id)
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
