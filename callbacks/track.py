from enum import StrEnum
from typing import Optional

from aiogram.filters.callback_data import CallbackData

class SpotifyTrackCBActions(StrEnum):
    ALBUM = "album"
    DOWNLOAD = "download"


class SpotifyTrackCB(CallbackData, prefix="spotify_track"):
    action: SpotifyTrackCBActions
    track_id: Optional[str] = None
    album_id: Optional[str] = None
