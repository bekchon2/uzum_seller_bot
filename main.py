import asyncio, logging, os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database import init_db
from handlers import start, main_menu, analytics
from services.scheduler import setup_scheduler

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "8080"))


async def ping(request):
    return web.Response(text="OK")


async def start_ping_server():
    app = web.Application()
    app.router.add_get("/ping", ping)
    app.router.add_get("/", ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    logger.info(f"Ping server started on port {PORT}")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in .env")

    await init_db()
    logger.info("Database initialized")

    bot = Bot(token=BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Handlerlar — tartib muhim: analytics oldin (FSM uchun)
    dp.include_router(analytics.router)
    dp.include_router(start.router)
    dp.include_router(main_menu.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    await start_ping_server()

    logger.info("Bot is starting...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
