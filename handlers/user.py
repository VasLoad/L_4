import json

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.payload import decode_payload

from enums.payload_command import PayloadCommand
from services.spotify import SpotifyClient
from utils.time import convert_time_from_milliseconds

router = Router()


@router.message(CommandStart(deep_link=True))  # Ловит только /start с payload
async def handle_deep_link(message: Message, command: CommandObject):
    raw_payload = command.args

    if not raw_payload:
        await message.answer("Нет payload")
        return

    try:
        payload = decode_payload(raw_payload)
    except UnicodeDecodeError:
        payload = raw_payload

    if payload == PayloadCommand.SHARE:
        await message.reply("Готово!")
    else:
        await message.reply("Некорректная ссылка!")


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🎵 *Добро пожаловать!*\n\n"
        "Просто отправь мне название песни, и я найду информацию о ней."
    )


@router.message(F.text)
async def song_search_handler(message: Message):
    track: dict = SpotifyClient().search(message.text)

    if not track:
        await message.answer("❌ Песня не найдена")
        return

    with open("response.json", "w", encoding="utf-8") as file:
        json.dump(track, file, ensure_ascii=False, indent=4)

        file.close()

    name = track["name"]
    artist = track["artists"][0]["name"]
    album = track["album"]["name"]
    release = track["album"]["release_date"]
    duration = convert_time_from_milliseconds(track["duration_ms"])
    url = track["external_urls"]["spotify"]
    cover = track["album"]["images"][0]["url"]

    text = (
        f"🎵 *{name}*\n"
        f"👤 Исполнитель: *{artist}*\n"
        f"💿 Альбом: *{album}*\n"
        f"📅 Релиз: {release}\n"
        f"⏱ Длительность: {duration}\n\n"
        f"🔗 [Открыть в Spotify]({url})"
    )

    await message.answer_photo(
        photo=cover,
        caption=text
    )
