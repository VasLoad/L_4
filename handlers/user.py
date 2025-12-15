from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from aiogram.utils.payload import decode_payload
import binascii

from enums.payload_command import PayloadCommand
from handlers.content import search_track_handler, search_album_handler

router = Router()


@router.message(CommandStart(deep_link=True))
async def handle_deep_link(message: Message, command: CommandObject):
    raw_payload = command.args

    if not raw_payload:
        await message.answer("Некорректная ссылка!")

        return

    try:
        payload = decode_payload(raw_payload)
    except (UnicodeDecodeError, binascii.Error):
        payload = raw_payload

    payload_data = payload.split("_")

    payload_data_len = len(payload_data)

    if payload_data_len > 0:
        payload_command = payload_data.pop(0)

        payload_data_len = len(payload_data)

        if payload_data_len > 0:
            if payload_command == PayloadCommand.TRACK:
                await search_track_handler(message, track_id=payload_data[0])

                return
            elif payload_command == PayloadCommand.ALBUM:
                await search_album_handler(message, album_id=payload_data[0])

                return

    await message_handler(message)


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привет!"
        "\nЧтобы получить *информацию о треке*, отправь в чат его *название*!"
        "\nИли воспользуйся командой /menu"
    )


@router.message(F.text)
async def message_handler(message: Message):
    if message.text[0] == "/":
        await message.reply("Команда не найдена.")
    else:
        await search_track_handler(message)
