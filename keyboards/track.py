from aiogram.types import InlineKeyboardMarkup, CopyTextButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from callbacks.track import SpotifyTrackCB, SpotifyTrackCBActions
from enums.payload_command import PayloadCommand
from services.spotify import SpotifyTrack
from utils.urls import generate_content_share_url


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
                text=generate_content_share_url(PayloadCommand.TRACK, track.id)
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