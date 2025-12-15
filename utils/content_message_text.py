from abc import ABC, abstractmethod
from typing import Optional

from enums.payload_command import PayloadCommand
from services.spotify import SpotifyArtist, SpotifyTrack, SpotifyAlbum, spotify_client
from utils.urls import generate_content_share_url


class ContentMessageText(ABC):
    def __init__(
            self,
            container_border_symbol: Optional[str] = "━",
            container_border_len: Optional[int] = 12
    ):
        self.__container_border_symbol = container_border_symbol
        self.__container_border_len = container_border_len

    @property
    @abstractmethod
    def text(self) -> str:
        pass

    @staticmethod
    def artists_text(artists: list[SpotifyArtist]) -> str:
        artists_len = len(artists)

        text = "🎤"

        if artists_len == 0:
            text += "Исполнитель отсутствует."

            return text

        text += f"*Исполнител{'и' if artists_len > 1 else 'ь'}*:"

        if artists_len > 1:
            for index, artist in enumerate(artists):
                text += f"\n   {index + 1}. - {artist.name}"
        else:
            text += f" {artists[0].name}"

        return text

    @staticmethod
    def tracks_text(tracks: list[SpotifyTrack]) -> str:
        tracks_len = len(tracks)

        text = "🎶"

        if tracks_len == 0:
            text += "Треки отсутствуют."

            return text

        text += f"*Трек{'и' if tracks_len > 1 else ''}*:"

        if tracks_len > 1:
            for index, track in enumerate(tracks):
                text += f"\n   {index + 1}. - [{track.name}]({generate_content_share_url(PayloadCommand.TRACK, track.id)})"
        else:
            text += f" [{tracks[0].name}]({generate_content_share_url(PayloadCommand.TRACK, tracks[0].id)})"

        return text

    def _container(
            self,
            name: str,
            artists: list[SpotifyArtist],
            release_date: str,
            data: tuple
    ) -> str:
        text = f"*{name}*\n"

        text += "\n" + f"✨{self.__border}✨\n"

        text += "\n" + self.artists_text(artists)

        text += "\n" + "📅 *Дата выхода*: " + release_date

        for item in data:
            text += "\n" + item

        text += "\n" + f"\n✨{self.__border}✨"

        # text = (
        #     name,
        #     self.__border,
        #     self.artists_text(artists),
        #     data,
        #     release_date,
        #     self.__border
        # )

        return text

    @property
    def __border(self) -> str:
        try:
            border = self.__container_border_symbol * self.__container_border_len
        except TypeError:
            border = ""

        return border


class ContentMessageTextTrack(ContentMessageText):
    def __init__(
            self,
            track: SpotifyTrack
    ):
        super().__init__()

        self.__track = track

    @property
    def text(self) -> str:
        data = (
            f"💿 *Альбом*: {self.__track.album.name}",
            f"⏳ *Длительность*: {self.__track.duration}"
        )

        text = self._container(
            name=self.__track.name,
            artists=self.__track.artists,
            release_date=self.__track.release_date,
            data=data
        )

        return text


class ContentMessageTextAlbum(ContentMessageText):
    def __init__(self, album: SpotifyAlbum):
        super().__init__()

        self.__album = album

    @property
    def text(self) -> str:
        tracks = spotify_client.get_tracks_by_album_id(self.__album.id)

        data = (
            f"🎵 *Треков*: {self.__album.total_tracks}",
            self.tracks_text(tracks)
        )

        text = self._container(
            name=self.__album.name,
            artists=self.__album.artists,
            release_date=self.__album.release_date,
            data=data
        )

        return text


class ContentMessageTextCommandError(ContentMessageText):
    def __init__(self, command: str, params: tuple):
        super().__init__()

        self.__command = command
        self.__params = params

    @property
    def text(self) -> str:
        text = (
            "Правильное использование команды:"
            f"\n{self.__command}"
        )

        for param in self.__params:
            text += f" {param}"

        return text
