"""run.py — to'liq log bilan ishga tushirish"""
import sys, os

# Bufferni o'chiramiz
os.environ["PYTHONUNBUFFERED"] = "1"
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("=== Bot ishga tushmoqda ===", flush=True)

try:
    import asyncio
    print("✅ asyncio OK", flush=True)
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ dotenv OK", flush=True)
    import os
    token = os.getenv("BOT_TOKEN")
    print(f"✅ TOKEN: {token[:20]}..." if token else "❌ TOKEN YOQ!", flush=True)

    from database import init_db
    print("✅ database import OK", flush=True)

    from handlers import start, main_menu, analytics
    print("✅ handlers import OK", flush=True)

    from services.scheduler import setup_scheduler
    print("✅ scheduler import OK", flush=True)

    print("\n=== Asosiy bot ishga tushmoqda ===", flush=True)

    import main as bot_main
    asyncio.run(bot_main.main())

except Exception as e:
    import traceback
    print(f"\n❌ XATO: {e}", flush=True)
    traceback.print_exc()
    input("\nEnter bosing...")
