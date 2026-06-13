import datetime
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from database import get_user
from locales.i18n import t
from utils.helpers import (today_timestamps, yesterday_timestamps,
                           day_timestamps, storage_status, format_money)
from utils.keyboards import storage_chart_keyboard
from services.uzum_api import (
    get_products, get_finance_orders, get_fbs_orders,
    extract_products, extract_finance_orders, extract_fbs_orders,
    parse_product, parse_finance_order, parse_fbs_order,
    UzumAPIError, UzumAuthError, UzumRateLimitError
)
from services.storage_tracker import get_storage_days_map
from services.charts import generate_sales_chart, generate_storage_chart

router = Router()

STATUS_EMOJI = {
    "CREATED": "🆕", "PACKING": "📦", "PENDING_DELIVERY": "⏳",
    "DELIVERING": "🚚", "DELIVERED": "📬", "COMPLETED": "✅",
    "ACCEPTED_AT_DP": "🏪", "DELIVERED_TO_CUSTOMER_DELIVERY_POINT": "🏪",
    "CANCELED": "❌", "PENDING_CANCELLATION": "🔄", "RETURNED": "↩️",
}

STATUS_LABEL = {
    "CREATED": "Yangi", "PACKING": "Qadoqlanmoqda",
    "PENDING_DELIVERY": "Kuryerda", "DELIVERING": "Yetkazilmoqda",
    "DELIVERED": "Yetkazildi", "COMPLETED": "Haridor oldi ✅",
    "ACCEPTED_AT_DP": "Punktda", "DELIVERED_TO_CUSTOMER_DELIVERY_POINT": "Punktda",
    "CANCELED": "Bekor", "PENDING_CANCELLATION": "Bekor bo'lmoqda",
    "RETURNED": "Qaytarildi",
}


async def _ctx(user_id: int):
    user = await get_user(user_id)
    if not user or not user["api_key"]:
        return None, None, None
    return user["lang"] or "ru", user["api_key"], user["shop_id"]


# ── 1. PRODUCTS ────────────────────────────────────────────
@router.message(F.text.contains("Мои товары") | F.text.contains("Mening mahsulotlarim"))
async def show_products(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer(t(lang, "products_loading"))
    try:
        raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(raw)]

        if not products:
            return await loading.edit_text(t(lang, "no_products"))

        text = t(lang, "products_header")
        total_qty   = sum(p["qty"] for p in products)
        total_sold  = sum(p["qty_sold"] for p in products)
        zero_stock  = sum(1 for p in products if p["qty"] == 0)

        for p in products[:20]:
            qty      = p["qty"]
            sold     = p["qty_sold"]
            forecast = p["forecast_days"]
            avg      = p["avg_sales"]

            if qty == 0:   stock_icon = "🚫"
            elif qty <= 5: stock_icon = "⚠️"
            elif qty <= 15:stock_icon = "🟡"
            else:          stock_icon = "🟢"

            line = f"{stock_icon} <b>{p['name'][:30]}</b>\n"
            line += f"   📦 {qty} dona"
            if sold:    line += f" | 🛒 {sold} sotilgan"
            if avg > 0: line += f" | 📈 {avg:.1f}/kun"
            if forecast > 0 and qty > 0:
                line += f" | ⏳ {forecast} kun"
            if p["price"] > 0:
                line += f"\n   💰 {format_money(p['price'])} so'm"
            text += line + "\n\n"

        text += f"─────────────────\n"
        text += f"📊 Jami: {len(products)} tovar | {total_qty} dona\n"
        text += f"🛒 Sotilgan: {total_sold} dona\n"
        if zero_stock:
            text += f"🚫 Tugagan: {zero_stock} ta"

        await loading.edit_text(text, parse_mode="HTML")

    except UzumRateLimitError:
        await loading.edit_text("⏳ Rate limit. 1 daqiqa kuting.")
    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")


# ── 2. ORDERS ──────────────────────────────────────────────
@router.message(F.text.contains("Заказы") | F.text.contains("Buyurtmalar"))
async def show_orders(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer(t(lang, "orders_loading"))
    try:
        # Oxirgi 30 kun — barcha buyurtmalar
        now = datetime.datetime.now()
        d_from = int((now - datetime.timedelta(days=30)).timestamp() * 1000)
        d_to   = int(now.timestamp() * 1000)

        fbs_raw = await get_fbs_orders(api_key, shop_id, d_from, d_to)
        all_orders = [parse_fbs_order(o) for o in extract_fbs_orders(fbs_raw)]

        if not all_orders:
            return await loading.edit_text(
                "📭 Oxirgi 30 kunda buyurtma yo'q." if lang=="uz"
                else "📭 За последние 30 дней заказов нет."
            )

        # Statuslar bo'yicha guruhlash
        completed = [o for o in all_orders if o["status"] == "COMPLETED"]
        active    = [o for o in all_orders if o["status"] not in
                     ("COMPLETED","CANCELED","RETURNED")]
        cancelled = [o for o in all_orders if o["status"] == "CANCELED"]

        total_rev = sum(o["revenue"] for o in completed)

        text = "🛒 <b>Buyurtmalar (30 kun)</b>\n\n"

        # Faol buyurtmalar
        if active:
            text += f"🔄 <b>Faol ({len(active)} ta):</b>\n"
            for o in active[:10]:
                emoji = STATUS_EMOJI.get(o["status"], "📋")
                label = STATUS_LABEL.get(o["status"], o["status"])
                items = o.get("items", [])
                item_names = ""
                for item in items[:2]:
                    name = (item.get("title") or item.get("skuTitle") or
                            item.get("name") or "Tovar")
                    qty  = item.get("amount") or item.get("quantity") or 1
                    item_names += f"\n     • {name[:25]} × {qty}"
                date = o["date_created"][:10] if o["date_created"] else "—"
                text += (f"  {emoji} #{str(o['id'])[-8:]} — {label}"
                         f"{item_names}\n"
                         f"     💰 {format_money(o['revenue'])} so'm | 📅 {date}\n\n")

        # Yakunlangan (haridor oldi)
        if completed:
            text += f"✅ <b>Haridor oldi ({len(completed)} ta):</b>\n"
            for o in completed[:5]:
                date = o["completed_date"][:10] if o["completed_date"] else \
                       o["date_created"][:10] if o["date_created"] else "—"
                text += f"  ✅ #{str(o['id'])[-8:]} — {format_money(o['revenue'])} so'm | {date}\n"
            text += "\n"

        text += f"─────────────────\n"
        text += f"✅ Yakunlangan: <b>{len(completed)} ta</b>\n"
        text += f"💰 Jami tushum: <b>{format_money(total_rev)} so'm</b>\n"
        if cancelled:
            text += f"❌ Bekor qilingan: {len(cancelled)} ta\n"

        await loading.edit_text(text, parse_mode="HTML")

    except UzumRateLimitError:
        await loading.edit_text("⏳ Rate limit. 1 daqiqa kuting.")
    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")


# ── 3. STORAGE ─────────────────────────────────────────────
@router.message(F.text.contains("Склад") | F.text.contains("Ombor"))
async def show_storage(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer("⏳ ...")
    try:
        storage_info = await get_storage_days_map(api_key, shop_id)
        all_invoices = storage_info["all_invoices"]

        await asyncio.sleep(0.5)
        raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(raw)]

        if not products:
            return await loading.edit_text(t(lang, "no_products"))

        text = t(lang, "storage_header")

        if all_invoices:
            text += f"📋 <b>Nakładnoylar:</b>\n"
            for inv in all_invoices[:5]:
                days = inv["days_in_storage"]
                left = max(0, 60 - days)
                s    = storage_status(days)

                if s == "paid":     icon = "💸"; detail = f"PULLIK (+{days-60} kun)"
                elif s == "critical":icon = "🚨"; detail = f"{left} kun qoldi!"
                elif s == "warn":   icon = "⚠️"; detail = f"{left} kun qoldi"
                else:               icon = "✅"; detail = f"{left} kun bepul"

                date_str = inv["date_accepted"].strftime("%d.%m.%Y") \
                           if inv["date_accepted"] else "—"
                text += (f"{icon} #{str(inv['invoice_number'])[-6:]}\n"
                         f"   📅 {date_str} | ⏱ {days}/60 kun | {detail}\n\n")

        text += f"\n📦 <b>Mahsulotlar qoldig'i:</b>\n"
        for p in products[:15]:
            qty = p["qty"]
            icon = "🚫" if qty==0 else ("⚠️" if qty<=5 else "📦")
            text += f"{icon} {p['name'][:28]} — <b>{qty} dona</b>\n"

        text += t(lang, "storage_tip")

        await loading.edit_text(text, parse_mode="HTML",
                                reply_markup=storage_chart_keyboard(lang))

    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")


@router.callback_query(F.data == "storage_chart")
async def cb_storage_chart(callback: CallbackQuery):
    lang, api_key, shop_id = await _ctx(callback.from_user.id)
    if not api_key:
        return await callback.answer("❌ /start")
    await callback.answer("📊 ...")
    try:
        storage_info = await get_storage_days_map(api_key, shop_id)
        days = storage_info["days"]
        raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(raw)]
        for p in products:
            p["days_in_storage"] = days
        chart = generate_storage_chart(products, lang)
        cap = "🏭 " + ("Omborxona holati" if lang=="uz" else "Статус хранения")
        await callback.message.answer_photo(BufferedInputFile(chart, "storage.png"), caption=cap)
    except Exception as e:
        await callback.message.answer(f"⚠️ {e}")


# ── 4. TODAY REPORT ────────────────────────────────────────
@router.message(F.text.contains("Отчёт") | F.text.contains("hisobot"))
async def show_report(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer("📊 Yuklanmoqda...")
    try:
        # Bugungi buyurtmalar — FBS orders (completed_date bugun)
        now = datetime.datetime.now()
        d_from = int((now - datetime.timedelta(days=7)).timestamp() * 1000)
        d_to   = int(now.timestamp() * 1000)
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        fbs_raw = await get_fbs_orders(api_key, shop_id, d_from, d_to)
        all_fbs = [parse_fbs_order(o) for o in extract_fbs_orders(fbs_raw)]

        # Bugun yakunlangan (haridor oldi)
        today_completed = [
            o for o in all_fbs
            if o["status"] == "COMPLETED" and
               (o["completed_date"] or o["date_created"] or "")[:10] == today_str
        ]
        # Bugun yaratilgan
        today_created = [
            o for o in all_fbs
            if (o["date_created"] or "")[:10] == today_str
        ]

        await asyncio.sleep(0.5)
        prods_raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(prods_raw)]

        await asyncio.sleep(0.3)
        storage_info = await get_storage_days_map(api_key, shop_id)
        storage_days = storage_info["days"]
        s_status     = storage_status(storage_days)

        total_qty  = sum(p["qty"] for p in products)
        zero_stock = [p for p in products if p["qty"] == 0]
        low_stock  = [p for p in products if 0 < p["qty"] <= 5]
        total_rev  = sum(o["revenue"] for o in today_completed)

        text = f"📊 <b>Bugungi hisobot — {today_str}</b>\n\n"

        text += f"🛒 <b>Buyurtmalar:</b>\n"
        text += f"   Bugun yaratilgan: {len(today_created)} ta\n"
        text += f"   Bugun haridor oldi: <b>{len(today_completed)} ta</b>\n"
        text += f"   💰 Tushum: <b>{format_money(total_rev)} so'm</b>\n\n"

        text += f"📦 <b>Ombor:</b>\n"
        text += f"   Jami tovarlar: {len(products)} ta | {total_qty} dona\n"
        if zero_stock: text += f"   🚫 Tugagan: {len(zero_stock)} ta\n"
        if low_stock:  text += f"   ⚠️ Kam qolgan (≤5): {len(low_stock)} ta\n"

        if storage_info["date_accepted"]:
            left = max(0, 60 - storage_days)
            date_str = storage_info["date_accepted"].strftime("%d.%m.%Y")
            text += f"\n🏭 <b>Saqlash:</b> {storage_days}/60 kun ({date_str})\n"
            if s_status == "paid":
                text += f"   💸 <b>PULLIK SAQLASH!</b>\n"
            elif s_status in ("critical", "warn"):
                text += f"   ⚠️ {left} kun qoldi\n"
            else:
                text += f"   ✅ {left} kun bepul\n"

        if low_stock:
            text += f"\n⚠️ <b>Tez to'ldiring:</b>\n"
            for p in low_stock[:5]:
                text += f"• {p['name'][:28]} — {p['qty']} dona\n"

        await loading.edit_text(text, parse_mode="HTML")

    except UzumRateLimitError:
        await loading.edit_text("⏳ Rate limit. 1 daqiqa kuting.")
    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")
