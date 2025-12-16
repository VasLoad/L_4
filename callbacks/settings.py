from enum import StrEnum
from typing import Any, Optional

from aiogram.filters.callback_data import CallbackData

from enums.db_settings_param_name import DBSettingsParamName


class SettingsCBActions(StrEnum):
    UPDATE_SETTING_PARAM_VALUE = "update_setting_param_value"

    GO_TO_MENU = "go_to_menu"

    SET_USER_DEFAULT_SETTINGS = "set_user_default_settings"


class SettingsCB(CallbackData, prefix="settings"):
    action: SettingsCBActions
    param: Optional[DBSettingsParamName] = None
    new_param_value: Optional[Any] = None
