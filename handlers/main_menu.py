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
    "DELIVERED": "✅", "CANCELLED": "❌", "PROCESSING": "🔄",
    "AWAITING_PACKAGING": "📦", "SHIPPED": "🚚", "CREATED": "🆕",
    "COMPLETED": "✅", "REFUNDED": "↩️",
}


async def _ctx(user_id: int):
    user = await get_user(user_id)
    if not user or not user["api_key"]:
        return None, None, None
    return user["lang"] or "ru", user["api_key"], user["shop_id"]


# ── 1. PRODUCTS — qoldiqlar bilan ─────────────────────────
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

        # Sarlavha
        text = t(lang, "products_header")

        # Umumiy statistika
        total_qty = sum(p["qty"] for p in products)
        total_sold = sum(p["qty_sold"] for p in products)
        zero_stock = sum(1 for p in products if p["qty"] == 0)

        for p in products[:20]:
            qty = p["qty"]
            sold = p["qty_sold"]
            forecast = p["forecast_days"]
            avg = p["avg_sales"]

            # Qoldiq holati
            if qty == 0:
                stock_icon = "🚫"
            elif qty <= 5:
                stock_icon = "⚠️"
            elif qty <= 15:
                stock_icon = "🟡"
            else:
                stock_icon = "🟢"

            line = (f"{stock_icon} <b>{p['name'][:30]}</b>\n"
                    f"   📦 {qty} {'dona' if lang=='uz' else 'шт.'}")

            if sold > 0:
                line += f" | 🛒 Sotilgan: {sold}"
            if avg > 0:
                line += f" | 📈 {avg:.1f}/kun"
            if forecast > 0 and qty > 0:
                line += f" | ⏳ {forecast} kun"
            if p["price"] > 0:
                line += f"\n   💰 {format_money(p['price'])} so'm"

            text += line + "\n\n"

        # Umumiy
        text += f"─────────────────\n"
        text += f"📊 <b>Jami: {len(products)} tovar</b>\n"
        text += f"📦 Umumiy qoldiq: <b>{total_qty} dona</b>\n"
        text += f"🛒 Jami sotilgan: <b>{total_sold} dona</b>\n"
        if zero_stock:
            text += f"🚫 Tugagan tovarlar: <b>{zero_stock} ta</b>"

        if len(products) > 20:
            text += f"\n\n<i>...va yana {len(products)-20} ta tovar</i>"

        await loading.edit_text(text, parse_mode="HTML")

    except UzumRateLimitError:
        await loading.edit_text("⏳ So'rovlar limiti. 1 daqiqa kuting va qayta urining.")
    except UzumAuthError:
        await loading.edit_text("❌ " + t(lang, "api_invalid"))
    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")


# ── 2. ORDERS — sotilgan tovarlar ro'yxati ────────────────
@router.message(F.text.contains("Заказы") | F.text.contains("Buyurtmalar"))
async def show_orders(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer(t(lang, "orders_loading"))
    try:
        date_from, date_to = today_timestamps()
        await asyncio.sleep(0.3)
        fbs_raw = await get_fbs_orders(api_key, shop_id, date_from, date_to)
        fbs_orders = [parse_fbs_order(o) for o in extract_fbs_orders(fbs_raw)]

        await asyncio.sleep(0.5)
        fin_raw = await get_finance_orders(api_key, shop_id, date_from, date_to)
        fin_orders = [parse_finance_order(o) for o in extract_finance_orders(fin_raw)]

        total_rev = sum(o["revenue"] for o in fin_orders)

        if not fbs_orders and not fin_orders:
            return await loading.edit_text(t(lang, "no_orders"))

        text = t(lang, "orders_header")

        if fbs_orders:
            for o in fbs_orders[:20]:
                emoji = STATUS_EMOJI.get(o["status"].upper(), "📋")
                items = o.get("items", [])
                items_text = ""
                for item in items[:2]:
                    iname = (item.get("title") or item.get("name") or
                             item.get("productName") or "Tovar")
                    iqty = item.get("quantity") or 1
                    items_text += f"\n     • {iname[:25]} × {iqty}"

                date_str = o["date"][:10] if o["date"] else ""
                text += (f"{emoji} <b>#{o['id'][-8:]}</b> — {o['status']}"
                         f"{items_text}\n"
                         f"     📅 {date_str}\n\n")
        else:
            # Finance orders dan
            for o in fin_orders[:15]:
                text += f"✅ #{o['id'][-8:]} — {format_money(o['revenue'])} so'm\n"

        text += "─────────────────\n"
        text += t(lang, "orders_total",
                  count=len(fbs_orders) or len(fin_orders),
                  revenue=total_rev)

        await loading.edit_text(text, parse_mode="HTML")

    except UzumRateLimitError:
        await loading.edit_text("⏳ So'rovlar limiti. 1 daqiqa kuting.")
    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")


# ── 3. STORAGE — invoice dan hisoblangan kunlar ───────────
@router.message(F.text.contains("Склад") | F.text.contains("Ombor"))
async def show_storage(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer("⏳ ...")
    try:
        # Invoice dan saqlash kunlarini olamiz
        storage_info = await get_storage_days_map(api_key, shop_id)
        days_global = storage_info["days"]
        date_accepted = storage_info["date_accepted"]
        all_invoices = storage_info["all_invoices"]

        # Mahsulotlar qoldiqlarini olamiz
        await asyncio.sleep(0.5)
        raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(raw)]

        if not products:
            return await loading.edit_text(t(lang, "no_products"))

        text = t(lang, "storage_header")

        # Har bir invoice uchun ma'lumot
        if all_invoices:
            word_inv = "Nakładnoylar" if lang == "uz" else "Поставки"
            text += f"📋 <b>{word_inv}:</b>\n"
            for inv in all_invoices[:5]:
                days = inv["days_in_storage"]
                left = max(0, 60 - days)
                s = storage_status(days)

                if s == "paid":
                    icon = "💸"
                    detail = f"PULLIK (+{days-60} kun)" if lang=="uz" else f"ПЛАТНОЕ (+{days-60} дн.)"
                elif s == "critical":
                    icon = "🚨"
                    detail = f"{left} kun qoldi!" if lang=="uz" else f"Осталось {left} дн.!"
                elif s == "warn":
                    icon = "⚠️"
                    detail = f"{left} kun qoldi" if lang=="uz" else f"Осталось {left} дн."
                else:
                    icon = "✅"
                    detail = f"{left} kun bepul" if lang=="uz" else f"{left} дн. бесплатно"

                date_str = inv["date_accepted"].strftime("%d.%m.%Y") if inv["date_accepted"] else "—"
                text += (f"{icon} Nakładnoy #{str(inv['invoice_number'])[-6:]}\n"
                         f"   📅 Qabul: {date_str} | "
                         f"⏱ {days}/60 kun | {detail}\n\n")

        # Mahsulotlar — qoldiq bilan
        word_prods = "Mahsulotlar qoldig'i" if lang == "uz" else "Остатки товаров"
        text += f"\n📦 <b>{word_prods}:</b>\n"

        # Har bir mahsulotga global days ni qo'shamiz
        for p in products[:15]:
            qty = p["qty"]
            if qty == 0:
                icon = "🚫"
            elif qty <= 5:
                icon = "⚠️"
            else:
                icon = "📦"
            text += f"{icon} {p['name'][:28]} — <b>{qty} dona</b>\n"

        text += t(lang, "storage_tip")

        # Pstorage (pullik saqlash) tekshirish
        paid_items = [p for p in products if p.get("pstorage")]
        if paid_items:
            word = "Pullik saqlashda" if lang == "uz" else "На платном хранении"
            text += f"\n\n💸 <b>{word}:</b>\n"
            for p in paid_items[:5]:
                ps = p["pstorage"]
                amount = ps.get("amount") or ps.get("price") or 0
                text += f"• {p['name'][:28]}: {format_money(amount)} so'm/kun\n"

        await loading.edit_text(text, parse_mode="HTML",
                                reply_markup=storage_chart_keyboard(lang))

    except UzumRateLimitError:
        await loading.edit_text("⏳ So'rovlar limiti. 1 daqiqa kuting.")
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
        all_invoices = storage_info["all_invoices"]

        raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(raw)]

        # Har bir mahsulotga storage kunlarini qo'shamiz
        days = storage_info["days"]
        for p in products:
            p["days_in_storage"] = days

        chart = generate_storage_chart(products, lang)
        cap = "🏭 " + ("Omborxona holati" if lang == "uz" else "Статус хранения")
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
        date_from, date_to = today_timestamps()

        # Finance orders
        fin_raw = await get_finance_orders(api_key, shop_id, date_from, date_to)
        orders = [parse_finance_order(o) for o in extract_finance_orders(fin_raw)]
        total_rev = sum(o["revenue"] for o in orders)

        await asyncio.sleep(0.5)

        # Mahsulotlar
        prods_raw = await get_products(api_key, shop_id)
        products = [parse_product(p) for p in extract_products(prods_raw)]

        await asyncio.sleep(0.3)

        # Storage
        storage_info = await get_storage_days_map(api_key, shop_id)
        storage_days = storage_info["days"]
        storage_status_val = storage_status(storage_days)

        total_qty = sum(p["qty"] for p in products)
        zero_stock = [p for p in products if p["qty"] == 0]
        low_stock = [p for p in products if 0 < p["qty"] <= 5]

        # Hisobot matni
        today_str = datetime.date.today().strftime("%d.%m.%Y")
        text = f"📊 <b>Bugungi hisobot — {today_str}</b>\n\n"

        # Savdo
        text += f"🛒 <b>{'Bugungi buyurtmalar' if lang=='uz' else 'Заказы сегодня'}:</b> {len(orders)}\n"
        text += f"💰 <b>{'Tushum' if lang=='uz' else 'Выручка'}:</b> {format_money(total_rev)} so'm\n\n"

        # Mahsulotlar
        text += f"📦 <b>{'Mahsulotlar' if lang=='uz' else 'Товары'}:</b>\n"
        text += f"   • {'Jami tovarlar' if lang=='uz' else 'Всего товаров'}: {len(products)} ta\n"
        text += f"   • {'Umumiy qoldiq' if lang=='uz' else 'Общий остаток'}: {total_qty} dona\n"

        if zero_stock:
            text += f"   • 🚫 {'Tugagan' if lang=='uz' else 'Закончились'}: {len(zero_stock)} ta\n"
        if low_stock:
            text += f"   • ⚠️ {'Kam qolgan (≤5)' if lang=='uz' else 'Мало остатков (≤5)'}: {len(low_stock)} ta\n"

        # Ombor holati
        text += f"\n🏭 <b>{'Ombor holati' if lang=='uz' else 'Склад'}:</b>\n"
        if storage_info["date_accepted"]:
            date_str = storage_info["date_accepted"].strftime("%d.%m.%Y")
            left = max(0, 60 - storage_days)
            text += f"   • {'Qabul qilingan' if lang=='uz' else 'Принято'}: {date_str}\n"
            text += f"   • {'Omborxonada' if lang=='uz' else 'Дней на складе'}: {storage_days}/60 kun\n"
            if storage_status_val == "paid":
                text += f"   • 💸 {'PULLIK SAQLASH!' if lang=='uz' else 'ПЛАТНОЕ ХРАНЕНИЕ!'}\n"
            elif storage_status_val in ("critical", "warn"):
                text += f"   • ⚠️ {left} {'kun qoldi' if lang=='uz' else 'дней осталось'}\n"
            else:
                text += f"   • ✅ {left} {'kun bepul' if lang=='uz' else 'дней бесплатно'}\n"

        # Kam qolgan tovarlar ro'yxati
        if low_stock:
            word = "Tez to'ldiring" if lang == "uz" else "Пополните скорее"
            text += f"\n⚠️ <b>{word}:</b>\n"
            for p in low_stock[:5]:
                text += f"• {p['name'][:28]} — {p['qty']} dona\n"

        if zero_stock:
            word = "Tugagan tovarlar" if lang == "uz" else "Закончились"
            text += f"\n🚫 <b>{word}:</b>\n"
            for p in zero_stock[:5]:
                text += f"• {p['name'][:28]}\n"

        await loading.edit_text(text, parse_mode="HTML")

    except UzumRateLimitError:
        await loading.edit_text("⏳ So'rovlar limiti. 1 daqiqa kuting.")
    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")


# ── 5. SALES CHART ─────────────────────────────────────────
@router.message(F.text.contains("График") | F.text.contains("grafik"))
async def show_chart(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer(t(lang, "chart_loading"))
    try:
        daily_data = []
        for i in range(6, -1, -1):
            day = datetime.date.today() - datetime.timedelta(days=i)
            d_from, d_to = day_timestamps(day)
            await asyncio.sleep(0.4)  # rate limit uchun
            try:
                raw = await get_finance_orders(api_key, shop_id, d_from, d_to)
                parsed = [parse_finance_order(o) for o in extract_finance_orders(raw)]
                daily_data.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "revenue": sum(o["revenue"] for o in parsed),
                    "orders": len(parsed),
                })
            except UzumRateLimitError:
                await asyncio.sleep(3)
                daily_data.append({"date": day.strftime("%Y-%m-%d"), "revenue": 0, "orders": 0})
            except Exception:
                daily_data.append({"date": day.strftime("%Y-%m-%d"), "revenue": 0, "orders": 0})

        chart = generate_sales_chart(daily_data,
                                     title=t(lang, "chart_title"),
                                     ylabel=t(lang, "chart_ylabel"))
        await loading.delete()
        await message.answer_photo(
            BufferedInputFile(chart, "sales.png"),
            caption="📈 " + t(lang, "chart_title")
        )
    except Exception as e:
        await loading.edit_text(f"⚠️ {e}")
