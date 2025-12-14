import asyncio

from bot import bot, dp

from handlers import user_router


async def main():
    dp.include_routers(
        user_router
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
