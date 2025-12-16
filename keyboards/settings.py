from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from callbacks.settings import SettingsCB, SettingsCBActions
from enums.db_settings_param_name import DBSettingsParamName


def settings_kb(
        send_information_image_param_new_value: Optional[bool] = None
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(
            text=f"Показывать обложку",
            callback_data=SettingsCB(
                action=SettingsCBActions.UPDATE_SETTING_PARAM_VALUE,
                param=DBSettingsParamName.SEND_INFORMATION_IMAGE,
                new_param_value=send_information_image_param_new_value
            ).pack()
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="🔁 По умолчанию 🔁",
            callback_data=SettingsCB(action=SettingsCBActions.SET_USER_DEFAULT_SETTINGS).pack()
        )
    )

    kb.row(
        InlineKeyboardButton(
            text=f"📋 В меню 📋",
            callback_data=SettingsCB(action=SettingsCBActions.GO_TO_MENU).pack()
        )
    )

    return kb.as_markup()
