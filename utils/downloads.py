import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from config import EMPTY_CONTENT_TEXT
from errors import DownloadError, DownloadedFilesNotFoundError


@dataclass
class DownloadedTrackFile:
    path: Path = field(default_factory=Path)
    filename: str = EMPTY_CONTENT_TEXT
    title: str = EMPTY_CONTENT_TEXT
    file_bytes: bytes = field(default_factory=lambda: bytes)


def download_track_spotify(url: str, output_dir: str) -> DownloadedTrackFile:
    """
    Скачивает трек по ссылке в указанную директорию.

    Args:
        url: Ссылка на трек
        output_dir: Директория для скачивания

    Returns:
        Экземпляр типа DownloadedTrackFile с информацией о скачанном файле трека

    Raises:
        DownloadError: Ошибка при скачивании
        DownloadedTrackFile: Скачанные файлы не найдены
    """

    download_dir = Path(output_dir)

    download_dir.mkdir(parents=True, exist_ok=True)

    for item in download_dir.iterdir():
        if item.is_file():
            item.unlink()
        else:
            shutil.rmtree(item)

    result = subprocess.run(
        ["spotdl", "download", url, "--output", str(download_dir)],
        capture_output=True,
        text=True,
        timeout=250
    )

    if result.returncode != 0:
        raise DownloadError(url)

    mp3_files = list(download_dir.glob("*.mp3"))

    if not mp3_files:
        DownloadedFilesNotFoundError(mp3_files)

    # Обработка бага библиотеки
    for file in mp3_files:
        if file.name == "Faceless 1-7 - Download My Conscious.mp3":
            file.unlink()

            mp3_files.remove(file)

            break

    file_path = Path(mp3_files[-1])

    filename = file_path.name

    title = filename[0:filename.rfind(".")]

    file_bytes = file_path.read_bytes()

    return DownloadedTrackFile(
        path=file_path,
        filename=filename,
        title=title,
        file_bytes=file_bytes
    )