import asyncio
import logging
from pathlib import Path

from bot import bot, dp
from config import LOGS_DIR_PATH, LOGS_FILE_PATH

from handlers import (
    errors_router,
    content_router,
    user_router
)


async def main():
    dp.include_routers(
        errors_router,
        content_router,
        user_router
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    logs_dir_path = Path(LOGS_DIR_PATH)

    logs_dir_path.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGS_FILE_PATH, encoding="utf-8")
        ]
    )

    asyncio.run(main())
