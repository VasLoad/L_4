from enum import StrEnum

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


class MainMenuButtonName(StrEnum):
    MENU = "📋 Меню"
    SETTINGS = "⚙️ Настройки"


def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()

    kb.button(
        text=MainMenuButtonName.MENU
    )

    kb.button(
        text=MainMenuButtonName.SETTINGS
    )

    kb.adjust(1)

    return kb.as_markup()
