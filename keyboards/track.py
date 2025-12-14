import re

from aiogram.types import InlineKeyboardMarkup, CopyTextButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from urllib.parse import quote

from callbacks.track import SpotifyTrackCB, SpotifyTrackCBActions
from config import URL_QUOTE_REGEX
from enums.payload_command import PayloadCommand
from services.spotify import SpotifyTrack


def generate_url(track: SpotifyTrack) -> str:
    artists_str = ""
    track_artists_len = len(track.artists)

    for index, artist in enumerate(track.artists):
        artists_str += artist.name

        if index < track_artists_len - 1:
            artists_str += "-"

    url = f"https://t.me/TrackStarInfo_bot?start={PayloadCommand.TRACK}"

    data = f"_{quote(track.id)}"

    data = re.sub(URL_QUOTE_REGEX, "", data)

    url += data

    return url


def spotify_track_kb(track: SpotifyTrack) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    track_id = track.url.rstrip("/").split("/")[-1]

    kb.row(
        InlineKeyboardButton(
            text="Альбом",
            callback_data=SpotifyTrackCB(action=SpotifyTrackCBActions.ALBUM, album_id=track.album.id).pack()
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="Открыть в Spotify",
            url=track.url
        ),
        InlineKeyboardButton(
            text="Поделиться",
            copy_text=CopyTextButton(
                text=generate_url(track)
            )
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="Скачать",
            callback_data=SpotifyTrackCB(action=SpotifyTrackCBActions.DOWNLOAD, track_id=track_id).pack()
        )
    )

    return kb.as_markup()