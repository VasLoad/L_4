from aiogram.types import InlineKeyboardMarkup, CopyTextButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from enums.payload_command import PayloadCommand
# from callbacks.track import SpotifyTrackCB, SpotifyTrackCBActions
from services.spotify import SpotifyAlbum
from utils.urls import generate_content_share_url


def spotify_album_kb(album: SpotifyAlbum) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # album_id = album.url.rstrip("/").split("/")[-1]

    kb.row(
        InlineKeyboardButton(
            text="Открыть в Spotify",
            url=album.url
        ),
        InlineKeyboardButton(
            text="Поделиться",
            copy_text=CopyTextButton(
                text=generate_content_share_url(PayloadCommand.ALBUM, album.id)
            )
        )
    )

    # kb.row(
    #     InlineKeyboardButton(
    #         text="Скачать",
    #         callback_data=SpotifyTrackCB(action=SpotifyTrackCBActions.DOWNLOAD, track_id=album_id).pack()
    #     )
    # )

    return kb.as_markup()