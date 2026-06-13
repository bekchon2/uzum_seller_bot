"""
Scheduler:
- 08:00 Toshkent: ertalabki hisobot
- Har 4 soat: ombor ogohlantirish
- Har 10 daqiqa: yetkazilgan buyurtmalar tekshirish
"""
import datetime
import asyncio
import logging
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import get_all_users, log_notification, was_notified_today
from locales.i18n import t
from utils.helpers import yesterday_timestamps, storage_status, format_money
from services.uzum_api import (
    get_products, get_finance_orders, get_fbs_orders,
    extract_products, extract_finance_orders, extract_fbs_orders,
    parse_product, parse_finance_order, parse_fbs_order,
    UzumAPIError, UzumRateLimitError
)
from services.storage_tracker import get_storage_days_map

logger = logging.getLogger(__name__)

# Delivered buyurtmalar — oxirgi ko'rilgan IDlar (xotirada saqlanadi)
_seen_delivered: dict[int, set] = {}


async def send_morning_report(bot: Bot, user_id: int, lang: str,
                               api_key: str, shop_id: int):
    """Kecha savdosi + ombor holati"""
    try:
        d_from, d_to = yesterday_timestamps()
        fin_raw = await get_finance_orders(api_key, shop_id, d_from, d_to)
        orders = [parse_finance_order(o) for o in extract_finance_orders(fin_raw)]
        total_rev = sum(o["revenue"] for o in orders)

        await asyncio.sleep(0.5)
        prods_raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(prods_raw)]

        await asyncio.sleep(0.3)
        storage_info = await get_storage_days_map(api_key, shop_id)
        storage_days = storage_info["days"]

        total_qty = sum(p["qty"] for p in products)
        zero_count = sum(1 for p in products if p["qty"] == 0)
        low_count  = sum(1 for p in products if 0 < p["qty"] <= 5)
        left = max(0, 60 - storage_days)
        s_status = storage_status(storage_days)

        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d.%m.%Y")
        today_str = datetime.date.today().strftime("%d.%m.%Y")

        text = f"🌅 <b>Ertalabki hisobot — {today_str}</b>\n\n"
        text += f"📅 <i>Kecha ({yesterday_str}) natijalari:</i>\n"
        text += f"🛒 Buyurtmalar: <b>{len(orders)}</b>\n"
        text += f"💰 Tushum: <b>{format_money(total_rev)} so'm</b>\n\n"
        text += f"📦 <b>Ombor holati:</b>\n"
        text += f"   Jami tovarlar: {len(products)} ta\n"
        text += f"   Umumiy qoldiq: {total_qty} dona\n"

        if zero_count:
            text += f"   🚫 Tugagan: {zero_count} ta\n"
        if low_count:
            text += f"   ⚠️ Kam qolgan (≤5): {low_count} ta\n"

        # Ombor muddati
        if storage_info["date_accepted"]:
            date_str = storage_info["date_accepted"].strftime("%d.%m.%Y")
            text += f"\n🏭 Omborxona: {storage_days}/60 kun ({date_str} dan)\n"
            if s_status == "paid":
                text += f"💸 <b>PULLIK SAQLASH! Tezda hal qiling!</b>\n"
            elif s_status == "critical":
                text += f"🚨 <b>Faqat {left} kun qoldi!</b>\n"
            elif s_status == "warn":
                text += f"⚠️ {left} kun qoldi\n"

        # Kam qolgan tovarlar
        low_stock = [p for p in products if 0 < p["qty"] <= 5]
        if low_stock:
            text += f"\n⚠️ <b>Tez to'ldiring:</b>\n"
            for p in low_stock[:5]:
                text += f"• {p['name'][:30]} — {p['qty']} dona\n"

        await bot.send_message(user_id, text, parse_mode="HTML")
        await log_notification(user_id, "morning_report")
        logger.info(f"Morning report → {user_id}")
    except Exception as e:
        logger.error(f"Morning report failed {user_id}: {e}")


async def check_storage_alerts(bot: Bot, user_id: int, lang: str,
                                api_key: str, shop_id: int):
    """Ombor muddati tugayotgan bo'lsa ogohlantirish"""
    try:
        storage_info = await get_storage_days_map(api_key, shop_id)
        all_invoices = storage_info["all_invoices"]

        for inv in all_invoices:
            days = inv["days_in_storage"]
            left = max(0, 60 - days)
            s = storage_status(days)
            inv_id = str(inv["id"])

            if s == "paid":
                key = f"paid_{inv_id}"
                if not await was_notified_today(user_id, key):
                    text = (f"💸 <b>PULLIK SAQLASH!</b>\n"
                            f"Nakładnoy #{str(inv['invoice_number'])[-6:]} — "
                            f"<b>{days} kun</b> omborxonada!\n"
                            f"Tezda tovarni olib keting yoki soting!")
                    await bot.send_message(user_id, text, parse_mode="HTML")
                    await log_notification(user_id, key)

            elif s == "critical":
                key = f"critical_{inv_id}"
                if not await was_notified_today(user_id, key):
                    text = (f"🚨 <b>SHOSHILINCH!</b>\n"
                            f"Nakładnoy #{str(inv['invoice_number'])[-6:]} — "
                            f"pullik saqlashga faqat <b>{left} kun</b> qoldi!")
                    await bot.send_message(user_id, text, parse_mode="HTML")
                    await log_notification(user_id, key)

            elif s == "warn":
                key = f"warn_{inv_id}"
                if not await was_notified_today(user_id, key):
                    text = (f"⚠️ Nakładnoy #{str(inv['invoice_number'])[-6:]} — "
                            f"{days}/60 kun. Pullik saqlashga {left} kun qoldi.")
                    await bot.send_message(user_id, text, parse_mode="HTML")
                    await log_notification(user_id, key)

    except Exception as e:
        logger.error(f"Storage alert failed {user_id}: {e}")


async def check_delivered_orders(bot: Bot, user_id: int, lang: str,
                                  api_key: str, shop_id: int):
    """
    Har 10 daqiqada COMPLETED buyurtmalarni tekshiradi.
    Haridor tovarni olib ketganda (completedDate) darhol xabar yuboradi.
    """
    global _seen_delivered
    try:
        now = datetime.datetime.now()
        d_from = int((now - datetime.timedelta(days=7)).timestamp() * 1000)
        d_to   = int(now.timestamp() * 1000)

        raw = await get_fbs_orders(api_key, shop_id, d_from, d_to)
        orders = [parse_fbs_order(o) for o in extract_fbs_orders(raw)]

        if user_id not in _seen_delivered:
            # Birinchi tekshirishda — mavjud COMPLETED larni saqla, xabar yuborme
            _seen_delivered[user_id] = {o["id"] for o in orders
                                         if o["status"] == "COMPLETED"}
            return

        seen = _seen_delivered[user_id]
        newly_completed = []

        for o in orders:
            if o["status"] == "COMPLETED" and o["id"] not in seen:
                newly_completed.append(o)
                seen.add(o["id"])

        _seen_delivered[user_id] = seen

        for o in newly_completed:
            items = o.get("items", [])
            items_text = ""
            for item in items[:3]:
                iname = (item.get("title") or item.get("skuTitle") or
                         item.get("name") or "Tovar")
                iqty = item.get("amount") or item.get("quantity") or 1
                items_text += f"\n  • {iname[:30]} × {iqty}"

            # completedDate — xaridor qabul qilgan sana (Дата получения)
            recv_date = o.get("completed_date") or o.get("date_created") or ""
            recv_str  = recv_date[:10] if recv_date else "—"

            text = (f"✅ <b>Haridor tovarni oldi!</b>\n\n"
                    f"🛍 Buyurtma: <b>#{str(o['id'])[-10:]}</b>"
                    f"{items_text}\n\n"
                    f"💰 Summa: {format_money(o['revenue'])} so\'m\n"
                    f"📅 Qabul qilindi: {recv_str}")

            await bot.send_message(user_id, text, parse_mode="HTML")
            logger.info(f"COMPLETED notification → {user_id}, order {o['id']}")

    except UzumRateLimitError:
        pass
    except Exception as e:
        logger.error(f"Delivered check failed {user_id}: {e}")


# ── Batch runners ──────────────────────────────────────────

async def run_morning_reports(bot: Bot):
    users = await get_all_users()
    for u in users:
        if not await was_notified_today(u["user_id"], "morning_report"):
            await send_morning_report(bot, u["user_id"], u["lang"] or "ru",
                                      u["api_key"], u["shop_id"])
            await asyncio.sleep(1)


async def run_storage_alerts(bot: Bot):
    users = await get_all_users()
    for u in users:
        await check_storage_alerts(bot, u["user_id"], u["lang"] or "ru",
                                   u["api_key"], u["shop_id"])
        await asyncio.sleep(0.5)


async def run_delivered_check(bot: Bot):
    users = await get_all_users()
    for u in users:
        await check_delivered_orders(bot, u["user_id"], u["lang"] or "ru",
                                     u["api_key"], u["shop_id"])
        await asyncio.sleep(0.5)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # Ertalabki hisobot — 08:00
    scheduler.add_job(run_morning_reports, "cron", hour=8, minute=0,
                      kwargs={"bot": bot}, id="morning", replace_existing=True)

    # Ombor ogohlantirish — har 4 soat
    scheduler.add_job(run_storage_alerts, "interval", hours=4,
                      kwargs={"bot": bot}, id="storage", replace_existing=True)

    # Delivered buyurtmalar — har 10 daqiqa
    scheduler.add_job(run_delivered_check, "interval", minutes=10,
                      kwargs={"bot": bot}, id="delivered", replace_existing=True)

    # Reyting tekshirish — kuniga 2 marta
    scheduler.add_job(run_rating_check, "cron", hour="9,18", minute=0,
                      kwargs={"bot": bot}, id="rating", replace_existing=True)

    # Tugashiga kun tekshirish — kuniga 1 marta (09:30)
    scheduler.add_job(run_forecast_check, "cron", hour=9, minute=30,
                      kwargs={"bot": bot}, id="forecast", replace_existing=True)

    # Yangi qaytarmalar — har 30 daqiqa
    scheduler.add_job(run_returns_check, "interval", minutes=30,
                      kwargs={"bot": bot}, id="returns", replace_existing=True)

    return scheduler


async def check_low_rating(bot: Bot, user_id: int, lang: str,
                            api_key: str, shop_id: int):
    """Reyting 4.5 dan past tushsa xabar"""
    try:
        raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(raw)]

        for p in products:
            rating = float(p.get("rating") or 0)
            if 0 < rating < 4.5:
                key = f"rating_{p['id']}_{int(rating*10)}"
                if not await was_notified_today(user_id, key):
                    text = (f"⭐ <b>Reyting pasaydi!</b>\n\n"
                            f"📦 {p['name'][:40]}\n"
                            f"⭐ Reyting: <b>{rating}</b> / 5.0\n\n"
                            f"<i>💡 Xaridorlar sharhlariga javob bering va sifatni yaxshilang.</i>")
                    await bot.send_message(user_id, text, parse_mode="HTML")
                    await log_notification(user_id, key)
    except Exception as e:
        logger.error(f"Rating check failed {user_id}: {e}")


async def check_stock_forecast(bot: Bot, user_id: int, lang: str,
                                api_key: str, shop_id: int):
    """Sotish tezligiga qarab tugashiga X kun qolganda xabar"""
    try:
        raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(raw)]

        for p in products:
            forecast = int(p.get("forecast_days") or 0)
            qty = p["qty"]
            if qty == 0 or forecast <= 0:
                continue

            # 7 kun va 3 kun ogohlantirishlari
            for threshold, label in [(3, "3kun"), (7, "7kun"), (14, "14kun")]:
                if forecast <= threshold:
                    key = f"forecast_{p['id']}_{label}"
                    if not await was_notified_today(user_id, key):
                        avg = p.get("avg_sales") or 0
                        text = (f"📉 <b>Tovar tez tugaydi!</b>\n\n"
                                f"📦 {p['name'][:40]}\n"
                                f"🔢 Qoldiq: <b>{qty} dona</b>\n"
                                f"📈 Kunlik sotuv: {avg:.1f} dona\n"
                                f"⏳ Tugashiga taxminan: <b>{forecast} kun</b>\n\n"
                                f"<i>💡 Yangi nakładnoy yaratishni unutmang!</i>")
                        await bot.send_message(user_id, text, parse_mode="HTML")
                        await log_notification(user_id, key)
                    break  # Faqat eng qisqa muddat uchun xabar
    except Exception as e:
        logger.error(f"Forecast check failed {user_id}: {e}")


async def check_new_returns(bot: Bot, user_id: int, lang: str,
                             api_key: str, shop_id: int):
    """Yangi qaytarma kelganda xabar"""
    from services.uzum_api import get_returns, extract_returns, parse_return
    try:
        raw = await get_returns(api_key, shop_id, size=10)
        returns_list = [parse_return(r) for r in extract_returns(raw)]

        # Bugun yaratilgan qaytarmalar
        today = datetime.date.today().strftime("%Y-%m-%d")
        new_returns = [
            r for r in returns_list
            if r["date"] and r["date"][:10] == today
        ]

        for ret in new_returns:
            key = f"return_{ret['id']}"
            if not await was_notified_today(user_id, key):
                text = (f"↩️ <b>Yangi qaytarma!</b>\n\n"
                        f"🔸 #{str(ret['id'])[-8:]}\n"
                        f"📝 Sabab: {ret['reason'] or 'koʻrsatilmagan'}\n"
                        f"💰 Summa: {format_money(ret['total'])} so'm\n\n"
                        f"<i>seller.uzum.uz da ko'rib chiqing.</i>")
                await bot.send_message(user_id, text, parse_mode="HTML")
                await log_notification(user_id, key)
    except Exception as e:
        logger.error(f"Returns check failed {user_id}: {e}")


async def run_rating_check(bot: Bot):
    users = await get_all_users()
    for u in users:
        await check_low_rating(bot, u["user_id"], u["lang"] or "ru",
                               u["api_key"], u["shop_id"])
        await asyncio.sleep(1)


async def run_forecast_check(bot: Bot):
    users = await get_all_users()
    for u in users:
        await check_stock_forecast(bot, u["user_id"], u["lang"] or "ru",
                                   u["api_key"], u["shop_id"])
        await asyncio.sleep(1)


async def run_returns_check(bot: Bot):
    users = await get_all_users()
    for u in users:
        await check_new_returns(bot, u["user_id"], u["lang"] or "ru",
                                u["api_key"], u["shop_id"])
        await asyncio.sleep(0.5)
