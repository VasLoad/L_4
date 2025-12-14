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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpotifyAlbum":
        images = data.get("images")

        if len(images) > 0:
            image_data = images[0]
        else:
            image_data = None

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
    name: str = EMPTY_CONTENT_TEXT
    artists: list[SpotifyArtist] = field(default_factory=list)
    album: SpotifyAlbum = field(default_factory=SpotifyAlbum)
    release: str = EMPTY_CONTENT_TEXT
    duration: Union[int, str] = 0
    url: str = EMPTY_CONTENT_TEXT

    @property
    def duration_decorated(self) -> Optional[str]:
        if self.duration:
            return convert_time_from_milliseconds(self.duration)

        return None

    @property
    def release_date(self) -> Optional[str]:
        if self.album:
            return self.album.release_date

        return None

    @property
    def image_url(self) -> Optional[str]:
        if self.album:
            if self.album.images:
                if len(self.album.images) > 0:
                    return self.album.images[0].url

        return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpotifyTrack":
        return cls(
            name=data.get("name"),
            artists=[SpotifyArtist.from_dict(artist) for artist in data.get("artists", [])],
            album=SpotifyAlbum.from_dict(data.get("album")),
            duration=data.get("duration"),
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
    def headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Basic {self.auth_data}"
        }

        return headers

    @cached_property
    def data(self) -> dict[str, str]:
        data = {
            "grant_type": "client_credentials"
        }

        return data

    @property
    def __access_token(self):
        response = requests.post(
            self.auth_url,
            data=self.data,
            headers=self.headers
        )

        return response.json()["access_token"]

    def search_track(self, name: str, limit: Optional[int] = None) -> Optional[dict[str, Any]]:
        self.search(name, type=ContentType.TRACK, limit=limit if limit else 0)

    def search_album(self, name: str, limit: Optional[int] = None) -> Optional[dict[str, Any]]:
        self.search(name, type=ContentType.ALBUM, limit=limit if limit else 0)

    def search(self, track_name: str, type: ContentType = ContentType.TRACK, limit: int = 1) -> Optional[dict[str, Any]]:
        token = self.__access_token

        headers = {
            "Authorization": f"Bearer {token}"
        }

        params = {
            "q": track_name,
            "type": type,
            "limit": limit if limit > 0 else 1
        }

        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params
        )

        items = response.json()["tracks"]["items"]

        return items if items else None

if __name__ == "__main__":
    with open("response.json", "r", encoding="utf-8") as file:
        track = SpotifyTrack.from_dict(json.loads(file.read()))

        file.close()

    print(track.image_url)
