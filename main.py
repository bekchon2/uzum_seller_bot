import asyncio, logging, os
from aiohttp import web
import aiohttp
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
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")  # Render avtomatik beradi


async def ping(request):
    return web.Response(text="OK", headers={"Cache-Control": "no-cache"})

async def health(request):
    return web.json_response({"status": "ok", "bot": "uzum-seller-bot"})


async def start_web_server():
    app = web.Application()
    app.router.add_get("/",       ping)
    app.router.add_get("/ping",   ping)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    logger.info(f"Web server started on port {PORT}")
    return runner


async def self_ping():
    """
    O'zini-o'zi har 10 daqiqada ping qiladi.
    Render free tier da uxlab qolmaslik uchun.
    """
    if not RENDER_URL:
        logger.info("RENDER_EXTERNAL_URL yo'q — self-ping o'chirildi (local mode)")
        return

    url = f"{RENDER_URL}/ping"
    logger.info(f"Self-ping boshlandi: {url}")

    while True:
        await asyncio.sleep(10 * 60)  # 10 daqiqa
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    logger.info(f"Self-ping: {resp.status}")
        except Exception as e:
            logger.warning(f"Self-ping xato: {e}")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in .env")

    await init_db()
    logger.info("Database initialized")

    bot = Bot(token=BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(analytics.router)
    dp.include_router(start.router)
    dp.include_router(main_menu.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    runner = await start_web_server()

    # Self-ping — background task
    asyncio.create_task(self_ping())

    logger.info("Bot polling started...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await runner.cleanup()
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
