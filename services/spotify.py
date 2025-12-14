import json
from dataclasses import dataclass, field
from typing import Any, Optional, Union
import base64
import requests
import os
from dotenv import load_dotenv
from propcache import cached_property

from config import EMPTY_CONTENT_TEXT
from enums.content_type import ContentType
from utils.time import convert_time_from_milliseconds

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

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
            album=SpotifyAlbum.from_dict(data.get("album")),
            duration_ms=data.get("duration_ms"),
            url=data.get("external_urls", {}).get("spotify")
        )

class SpotifyClient:
    """Клиент Spotify."""

    def __init__(
            self,
            client_id: str = os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret = os.getenv("SPOTIFY_CLIENT_SECRET"),
            auth_url: str = "https://accounts.spotify.com/api/token",
            search_url: str = "https://api.spotify.com/v1/search"
        ):
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__auth_url = auth_url
        self.__search_url = search_url

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

    @property
    def auth_data(self) -> str:
        auth = f"{self.__client_id}:{self.__client_secret}"

        b64_auth = base64.b64encode(auth.encode()).decode()

        return b64_auth

    @cached_property
    def __auth_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Basic {self.auth_data}"
        }

        return headers

    @cached_property
    def __auth_data(self) -> dict[str, str]:
        data = {
            "grant_type": "client_credentials"
        }

        return data

    @property
    def __access_token(self):
        response = requests.post(
            self.auth_url,
            data=self.__auth_data,
            headers=self.__auth_headers
        )

        return response.json()["access_token"]

    @property
    def __search_headers(self) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.__access_token}"
        }

        return headers

    def search_by_id(self, id: str, type: ContentType) -> Union[SpotifyTrack, SpotifyAlbum]:
        search_type_str = "tracks" if type is ContentType.TRACK else "albums"

        response = requests.get(
            f"https://api.spotify.com/v1/{search_type_str}/{id}",
            headers=self.__search_headers
        )

        if type is ContentType.TRACK:
            return SpotifyTrack.from_dict(response.json())
        else:
            return SpotifyAlbum.from_dict(response.json())

    def search_track(self, name: str, limit: Optional[int] = None) -> list[SpotifyTrack]:
        return self.search(name, type=ContentType.TRACK, limit=limit)

    def search_track_by_id(self, track_id: str) -> SpotifyTrack:
        return self.search_by_id(track_id, type=ContentType.TRACK)

    def search_album(self, name: str, limit: Optional[int] = None) -> list[SpotifyAlbum]:
        return self.search(name, type=ContentType.ALBUM, limit=limit)

    def search_album_by_id(self, album_id: str) -> SpotifyAlbum:
        return self.search_by_id(album_id, type=ContentType.ALBUM)

    def search(self, track_name: str, type: ContentType = ContentType.TRACK, limit: Optional[int] = None) -> list[Union[SpotifyTrack, SpotifyAlbum]]:
        params = {
            "q": track_name,
            "type": type
        }

        if limit and isinstance(limit, int) and limit > 0:
            params["limit"] = str(limit)

        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=self.__search_headers,
            params=params
        )

        items = response.json()["tracks"]["items"]

        artists = []

        if items:
            for item in items:
                if type is ContentType.TRACK:
                    artists.append(SpotifyTrack.from_dict(item))
                elif type is ContentType.ALBUM:
                    artists.append(SpotifyAlbum.from_dict(item))

        return artists

if __name__ == "__main__":
    with open("response.json", "r", encoding="utf-8") as file:
        track = SpotifyTrack.from_dict(json.loads(file.read()))

        file.close()
