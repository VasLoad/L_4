from aiogram import Router
from aiogram.types import ErrorEvent
import logging

from config import HANDLER_ERROR_MESSAGE_TEXT, HANDLER_ERROR_LOGGER_TEXT

router = Router()

logger = logging.getLogger(__name__)

@router.errors()
async def errors_handler_user(event: ErrorEvent):
    if event.update.message:
        try:
            await event.update.message.answer(HANDLER_ERROR_MESSAGE_TEXT)
        except Exception:
            pass

    logger.exception(HANDLER_ERROR_LOGGER_TEXT, exc_info=event.exception)
