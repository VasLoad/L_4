from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from callbacks.menu import MenuCB, MenuCBActions


def menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(
            text=f"Настройки",
            callback_data=(MenuCB(action=MenuCBActions.OPEN_SETTINGS)).pack()
        )
    )

    return kb.as_markup()