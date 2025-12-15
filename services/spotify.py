import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Union
import base64
from propcache import cached_property

from config import EMPTY_CONTENT_TEXT, config
from enums.content_type import ContentType
from enums.request_type import RequestType
from errors import RemoteResponseDataError
from utils.send_requests import send_request
from utils.time import convert_time_from_milliseconds

@dataclass
class SpotifyImage:
    height: Union[int, str] = 0
    width: Union[int, str] = 0
    url: str = EMPTY_CONTENT_TEXT

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpotifyImage":
        return cls(
            height=data.get("height"),
            width=data.get("width"),
            url=data.get("url")
        )


@dataclass
class SpotifyArtist:
    url: str = EMPTY_CONTENT_TEXT
    id: str = EMPTY_CONTENT_TEXT
    name: str = EMPTY_CONTENT_TEXT

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpotifyArtist":
        return cls(
            url=data.get("url"),
            id=data.get("id"),
            name=data.get("name")
        )


@dataclass
class SpotifyAlbum:
    album_type: str = EMPTY_CONTENT_TEXT
    artists: list[SpotifyArtist] = field(default_factory=list)
    url: str = EMPTY_CONTENT_TEXT
    id: str = EMPTY_CONTENT_TEXT
    images: list[SpotifyImage] = field(default_factory=list)
    is_playable: bool = field(default_factory=bool)
    name: str = EMPTY_CONTENT_TEXT
    release_date: str = EMPTY_CONTENT_TEXT
    total_tracks: Union[int, str] = 0

    @property
    def image_url(self) -> Optional[str]:
        if self.images:
            return self.images[0].url

        return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpotifyAlbum":
        return cls(
            album_type=data.get("album_type"),
            artists=[SpotifyArtist.from_dict(artist) for artist in data.get("artists", [])],
            url=data.get("external_urls", {}).get("spotify"),
            id=data.get("id"),
            images=[SpotifyImage.from_dict(image) for image in data.get("images", [])],
            is_playable=data.get("is_playable"),
            name=data.get("name"),
            release_date=data.get("release_date"),
            total_tracks=data.get("total_tracks")
        )


@dataclass
class SpotifyTrack:
    id: str = ""
    name: str = EMPTY_CONTENT_TEXT
    artists: list[SpotifyArtist] = field(default_factory=list)
    album: SpotifyAlbum = field(default_factory=SpotifyAlbum)
    duration_ms: Union[int, str] = 0
    url: str = EMPTY_CONTENT_TEXT

    @property
    def duration(self) -> str:
        if self.duration_ms:
            return convert_time_from_milliseconds(self.duration_ms)

        return EMPTY_CONTENT_TEXT

    @property
    def release_date(self) -> str:
        if self.album:
            return self.album.release_date

        return EMPTY_CONTENT_TEXT

    @property
    def image_url(self) -> Optional[str]:
        if self.album:
            return self.album.image_url

        return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpotifyTrack":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            artists=[SpotifyArtist.from_dict(artist) for artist in data.get("artists", [])],
            album=SpotifyAlbum.from_dict(data.get("album", {})),
            duration_ms=data.get("duration_ms"),
            url=data.get("external_urls", {}).get("spotify")
        )

class SpotifyClient:
    """Клиент Spotify."""

    def __init__(
            self,
            client_id: str = "",
            client_secret: str = "",
            auth_url: Optional[str] = "https://accounts.spotify.com/api/token",
            search_url: Optional[str] = "https://api.spotify.com/v1/search"
        ):
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__auth_url = auth_url
        self.__search_url = search_url

        self.__access_token: Optional[str] = None
        self.__access_token_expires_at: float = 0.0

    @property
    def client_id(self) -> str:
        return self.__client_id

    @property
    def client_secret(self) -> str:
        return self.__client_secret

    @property
    def auth_url(self) -> str:
        return self.__auth_url

    @property
    def search_url(self) -> str:
        return self.__search_url

    @cached_property
    def auth_token(self) -> str:
        auth = f"{self.__client_id}:{self.__client_secret}"

        b64_auth = base64.b64encode(auth.encode()).decode()

        return b64_auth

    def search_by_id(self, content_id: str, content_type: ContentType) -> Union[SpotifyTrack, SpotifyAlbum]:
        search_type_str = f"{content_type.value}s"

        response = send_request(
            RequestType.GET,
            f"https://api.spotify.com/v1/{search_type_str}/{content_id}",
            headers=self.__search_headers
        )

        if content_type is ContentType.TRACK:
            return SpotifyTrack.from_dict(response.json())
        else:
            return SpotifyAlbum.from_dict(response.json())

    def search_track(self, name: str, limit: Optional[int] = None) -> list[SpotifyTrack]:
        return self.search(name, content_type=ContentType.TRACK, limit=limit)

    def search_track_by_id(self, track_id: str) -> SpotifyTrack:
        return self.search_by_id(track_id, content_type=ContentType.TRACK)

    def search_album(self, name: str, limit: Optional[int] = None) -> list[SpotifyAlbum]:
        return self.search(name, content_type=ContentType.ALBUM, limit=limit)

    def search_album_by_id(self, album_id: str) -> SpotifyAlbum:
        return self.search_by_id(album_id, content_type=ContentType.ALBUM)

    def get_tracks_by_album_id(self, album_id: str) -> list[SpotifyTrack]:
        response = send_request(
            RequestType.GET,
            f"https://api.spotify.com/v1/albums/{album_id}/tracks",
            headers=self.__search_headers
        )

        try:
            data = response.json()["items"]
        except Exception as ex:
            raise RemoteResponseDataError(str(ex), response.json())

        tracks = [SpotifyTrack.from_dict(track) for track in data]

        return tracks

    def search(self, track_name: str, content_type: ContentType = Union[SpotifyTrack, SpotifyAlbum], limit: Optional[int] = None) -> list[Union[SpotifyTrack, SpotifyAlbum]]:
        params = {
            "q": track_name,
            "type": content_type.value
        }

        if limit and isinstance(limit, int) and limit > 0:
            params["limit"] = str(limit)

        response = send_request(
            RequestType.GET,
            "https://api.spotify.com/v1/search",
            headers=self.__search_headers,
            params=params
        )

        items = []

        try:
            if content_type is ContentType.TRACK:
                items = response.json()["tracks"]["items"]
            elif content_type is ContentType.ALBUM:
                items = response.json()["albums"]["items"]
        except Exception as ex:
            raise RemoteResponseDataError(str(ex), response.json())

        artists = []

        if items:
            for item in items:
                if content_type is ContentType.TRACK:
                    artists.append(SpotifyTrack.from_dict(item))
                elif content_type is ContentType.ALBUM:
                    artists.append(SpotifyAlbum.from_dict(item))

        return artists

    @cached_property
    def __auth_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Basic {self.auth_token}"
        }

        return headers

    @property
    def __auth_data(self) -> dict[str, str]:
        data = {
            "grant_type": "client_credentials"
        }

        return data

    def __get_access_token(self):
        if self.__access_token and time.time() < self.__access_token_expires_at:
            return self.__access_token

        response = send_request(
            RequestType.POST,
            self.auth_url,
            headers=self.__auth_headers,
            data=self.__auth_data
        )

        try:
            self.__access_token = response.json()["access_token"]
            self.__access_token_expires_at = time.time() + response.json()["expires_in"] - 10

            return self.__access_token
        except Exception as ex:
            raise RemoteResponseDataError(str(ex), response.json())

    @property
    def __search_headers(self) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.__get_access_token()}"
        }

        return headers


spotify_client = SpotifyClient(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET
)
