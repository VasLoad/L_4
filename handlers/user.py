from typing import Optional

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.payload import decode_payload
import binascii

from callbacks.menu import MenuCB, MenuCBActions
from callbacks.settings import SettingsCB, SettingsCBActions
from config import SETTINGS_PARAM_VALUE_TRUE_FALSE_TEXT_DICT
from enums.command_name import CommandName
from enums.payload_command import PayloadCommand
from enums.db_settings_param_name import DBSettingsParamName
from handlers.content import search_track_handler, search_album_handler
from keyboards.main_menu import main_menu_kb, MainMenuButtonName
from keyboards.menu import menu_kb
from keyboards.settings import settings_kb
from services.db import UsersRepository, db_sender, register_user, UserSettingsRepository
from utils.message_text import ContentMessageTextSettings, ContentMessageTextMenu, ContentMessageTextHelp

router = Router()


@router.message(CommandStart(deep_link=True))
async def handle_deep_link(message: Message, command: CommandObject):
    raw_payload = command.args

    if not raw_payload:
        await message.answer("Некорректная ссылка!")

        return

    db_users_repo = UsersRepository(db_sender)

    is_user_registered = db_users_repo.check_user(message.from_user.id)

    if not is_user_registered:
        register_user(db_sender, message.from_user.id)

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
    db_users_repo = UsersRepository(db_sender)

    is_user_registered = db_users_repo.check_user(message.from_user.id)

    if is_user_registered:
        answer_text = "Чтобы получить *информацию о треке*, отправь в чат его *название*!"
    else:
        register_user(db_sender, message.from_user.id)

        answer_text = (
            "Привет!"
            "\nЧтобы получить *информацию о треке*, отправь в чат его *название*!"
            "\nИли воспользуйся командой /menu"
        )

    await message.answer(
        answer_text,
        reply_markup=main_menu_kb()
    )


@router.message(Command(CommandName.MENU))
async def menu_command(message: Message, callback: bool = False):
    text = ContentMessageTextMenu().text

    if callback:
        await message.edit_text(
            text=text,
            reply_markup=menu_kb()
        )
    else:
        await message.answer(
            text=text,
            reply_markup=menu_kb()
        )


@router.message(Command(CommandName.SETTINGS))
async def settings_command(message: Message, user_id: Optional[int] = None, callback: bool = False):
    db_user_settings_repo = UserSettingsRepository(db_sender)

    settings = db_user_settings_repo.get_settings(user_id if user_id else message.from_user.id)

    send_information_image = settings.get(DBSettingsParamName.SEND_INFORMATION_IMAGE)

    send_information_image_text = SETTINGS_PARAM_VALUE_TRUE_FALSE_TEXT_DICT.get(settings.get(DBSettingsParamName.SEND_INFORMATION_IMAGE))

    settings_str = (
        f"🖼️ *Показывать обложку*: {send_information_image_text}",
    )

    text = ContentMessageTextSettings(settings_str).text

    if callback or user_id:
        try:
            await message.edit_text(
                text=text,
                reply_markup=settings_kb(
                    send_information_image_param_new_value=not send_information_image
                )
            )
        except TelegramBadRequest:
            pass
    else:
        await message.answer(
            text=text,
            reply_markup=settings_kb(
                send_information_image_param_new_value=not send_information_image
            )
        )

@router.message(Command(CommandName.HELP))
async def help_command(message: Message):
    commands = (
        f"/{CommandName.TRACK}: Поиск трека"
        f"\n   Использование: /{CommandName.TRACK} <название трека> <другие параметры (опционально)>",
        f"/{CommandName.ALBUM}: Поиск альбома"
        f"\n   Использование: /{CommandName.ALBUM} <название альбома> <другие параметры (опционально)>",
        f"/{CommandName.MENU}: Меню"
        f"\n   Использование: /{CommandName.MENU}",
        f"/{CommandName.SETTINGS}: Настройки"
        f"\n   Использование: /{CommandName.SETTINGS}"
    )

    text = ContentMessageTextHelp(commands).text

    await message.answer(text)


@router.message(F.text == MainMenuButtonName.MENU)
async def main_menu_handler_menu(message: Message):
    await menu_command(message)


@router.message(F.text == MainMenuButtonName.SETTINGS)
async def main_menu_handler_settings(message: Message):
    await settings_command(message)


@router.message(F.text)
async def message_handler(message: Message):
    if message.text[0] == "/":
        text = "Команда не найдена.\nℹ️ Для получения помощи по командам выполните /help"
    elif message.text.startswith("http"):
        text = "\nПохоже вы отправили ссылку...\nЯ не могу её обработать."
    else:
        await search_track_handler(message)

        return

    await message.reply(text)


@router.callback_query(MenuCB.filter())
async def menu_handler(callback: CallbackQuery, callback_data: MenuCB):
    if callback_data.action == MenuCBActions.OPEN_SETTINGS:
        await settings_command(callback.message, user_id=callback.from_user.id, callback=True)

    await callback.answer()


@router.callback_query(SettingsCB.filter())
async def settings_handler(callback: CallbackQuery, callback_data: SettingsCB):
    db_user_settings_repo = UserSettingsRepository(db_sender)

    if callback_data.action == SettingsCBActions.UPDATE_SETTING_PARAM_VALUE:
        if callback_data.param and callback_data.new_param_value:
            db_user_settings_repo.update_param_value(
                user_id=callback.from_user.id,
                param=callback_data.param,
                value=callback_data.new_param_value
            )

            await settings_command(callback.message, user_id=callback.from_user.id, callback=False)
    elif callback_data.action == SettingsCBActions.GO_TO_MENU:
        await menu_command(callback.message, callback=True)
    elif callback_data.action == SettingsCBActions.SET_USER_DEFAULT_SETTINGS:
        db_user_settings_repo.delete_user_settings(callback.from_user.id, set_default=True)

        await settings_command(callback.message, user_id=callback.from_user.id, callback=False)

    await callback.answer()
