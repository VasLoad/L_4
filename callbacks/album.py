from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

class SpotifyTrackCBActions(StrEnum):
    DOWNLOAD = "download"


class SpotifyTrackCB(CallbackData, prefix="spotify_album"):
    action: SpotifyTrackCBActions
