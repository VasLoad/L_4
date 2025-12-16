from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

class MenuCBActions(StrEnum):
    OPEN_SETTINGS = "open_settings"


class MenuCB(CallbackData, prefix="menu"):
    action: MenuCBActions
