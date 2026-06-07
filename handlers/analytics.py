"""
Yangi funksiyalar:
1. Haftalik tushum + komissiya hisobi
2. Oylik foyda/zarar
3. Qaytarmalar ro'yxati
"""
import datetime
import asyncio
from aiogram import Router, F
from aiogram.types import Message

from database import get_user
from locales.i18n import t
from utils.helpers import format_money, day_timestamps
from services.uzum_api import (
    get_products, get_finance_orders, get_returns, get_expenses,
    extract_products, extract_finance_orders, extract_returns, extract_expenses,
    parse_product, parse_finance_order, parse_return, parse_expense,
    UzumAPIError, UzumRateLimitError
)

router = Router()


async def _ctx(user_id: int):
    user = await get_user(user_id)
    if not user or not user["api_key"]:
        return None, None, None
    return user["lang"] or "ru", user["api_key"], user["shop_id"]


# ── HAFTALIK HISOBOT ────────────────────────────────────────
@router.message(F.text.contains("Haftalik") | F.text.contains("Недельный"))
async def weekly_report(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer("📊 Haftalik hisobot tayyorlanmoqda...")
    try:
        now = datetime.datetime.now()
        week_ago = now - datetime.timedelta(days=7)

        total_rev = 0
        total_orders = 0
        daily_rows = ""

        for i in range(6, -1, -1):
            day = datetime.date.today() - datetime.timedelta(days=i)
            d_from, d_to = day_timestamps(day)
            await asyncio.sleep(0.4)
            try:
                raw = await get_finance_orders(api_key, shop_id, d_from, d_to)
                orders = [parse_finance_order(o) for o in extract_finance_orders(raw)]
                rev = sum(o["revenue"] for o in orders)
                cnt = len(orders)
                total_rev += rev
                total_orders += cnt
                bar = "█" * min(10, int(rev / 200000)) if rev > 0 else "░"
                daily_rows += f"  {day.strftime('%d.%m')} {bar} {format_money(rev)} so'm ({cnt} ta)\n"
            except Exception:
                daily_rows += f"  {day.strftime('%d.%m')} — ma'lumot yo'q\n"

        # Xarajatlar
        await asyncio.sleep(0.5)
        d_from_w = int(week_ago.timestamp() * 1000)
        d_to_w   = int(now.timestamp() * 1000)
        total_expenses = 0
        commission_total = 0
        storage_fees = 0

        try:
            exp_raw = await get_expenses(api_key, shop_id, d_from_w, d_to_w)
            expenses = [parse_expense(e) for e in extract_expenses(exp_raw)]
            for e in expenses:
                src = e["source"].upper() if e["source"] else ""
                price = e["price"]
                total_expenses += price
                if "COMMISSION" in src or "комисси" in e["name"].lower():
                    commission_total += price
                elif "STORAGE" in src or "хранени" in e["name"].lower():
                    storage_fees += price
        except Exception:
            pass

        profit = total_rev - total_expenses

        text = f"📈 <b>Haftalik hisobot</b>\n"
        text += f"📅 {week_ago.strftime('%d.%m')} — {datetime.date.today().strftime('%d.%m.%Y')}\n\n"
        text += f"<b>Kunlik sotuv:</b>\n{daily_rows}\n"
        text += f"─────────────────\n"
        text += f"💰 Jami tushum: <b>{format_money(total_rev)} so'm</b>\n"
        text += f"🛒 Jami buyurtma: <b>{total_orders} ta</b>\n"

        if total_orders > 0:
            text += f"📊 O'rtacha: <b>{format_money(total_rev // max(total_orders,1))} so'm/buyurtma</b>\n"

        if total_expenses > 0:
            text += f"\n<b>Xarajatlar:</b>\n"
            if commission_total > 0:
                text += f"  📋 Komissiya: {format_money(commission_total)} so'm\n"
            if storage_fees > 0:
                text += f"  🏭 Saqlash: {format_money(storage_fees)} so'm\n"
            other = total_expenses - commission_total - storage_fees
            if other > 0:
                text += f"  📦 Boshqa: {format_money(other)} so'm\n"
            text += f"  Jami xarajat: <b>{format_money(total_expenses)} so'm</b>\n"
            text += f"\n{'✅' if profit>0 else '❌'} Foyda: <b>{format_money(profit)} so'm</b>\n"
        else:
            text += f"\n<i>ℹ️ Xarajatlar API dan olinmadi (ruxsat yo'q)</i>\n"

        await loading.edit_text(text, parse_mode="HTML")

    except UzumRateLimitError:
        await loading.edit_text("⏳ Rate limit. 1 daqiqa kuting.")
    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")


# ── OYLIK HISOBOT ───────────────────────────────────────────
@router.message(F.text.contains("Oylik") | F.text.contains("Месячный"))
async def monthly_report(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer("📊 Oylik hisobot tayyorlanmoqda...")
    try:
        now = datetime.datetime.now()
        month_ago = now - datetime.timedelta(days=30)
        d_from = int(month_ago.timestamp() * 1000)
        d_to   = int(now.timestamp() * 1000)

        total_rev = 0
        total_orders = 0
        weekly_rows = ""

        for week in range(4):
            w_end_dt   = now - datetime.timedelta(days=week*7)
            w_start_dt = now - datetime.timedelta(days=(week+1)*7)
            wf = int(w_start_dt.timestamp() * 1000)
            wt = int(w_end_dt.timestamp() * 1000)
            await asyncio.sleep(0.5)
            try:
                raw = await get_finance_orders(api_key, shop_id, wf, wt)
                orders = [parse_finance_order(o) for o in extract_finance_orders(raw)]
                rev = sum(o["revenue"] for o in orders)
                cnt = len(orders)
                total_rev += rev
                total_orders += cnt
                label = f"{w_start_dt.strftime('%d.%m')}–{w_end_dt.strftime('%d.%m')}"
                weekly_rows += f"  {label}: {format_money(rev)} so'm ({cnt} ta)\n"
            except Exception:
                pass

        # Xarajatlar
        await asyncio.sleep(0.5)
        total_expenses = 0
        commission_total = 0
        storage_fees = 0
        expense_rows = ""

        try:
            exp_raw = await get_expenses(api_key, shop_id, d_from, d_to)
            expenses = [parse_expense(e) for e in extract_expenses(exp_raw)]
            by_source: dict[str, int] = {}
            for e in expenses:
                src = e["name"] or e["source"] or "Boshqa"
                by_source[src] = by_source.get(src, 0) + e["price"]
                total_expenses += e["price"]
                src_up = e["source"].upper() if e["source"] else ""
                if "COMMISSION" in src_up:
                    commission_total += e["price"]
                elif "STORAGE" in src_up:
                    storage_fees += e["price"]
            for src, amount in sorted(by_source.items(), key=lambda x: -x[1])[:6]:
                expense_rows += f"  • {src[:28]}: {format_money(amount)} so'm\n"
        except Exception:
            pass

        profit = total_rev - total_expenses

        text = f"📅 <b>Oylik hisobot (30 kun)</b>\n"
        text += f"{month_ago.strftime('%d.%m')} — {datetime.date.today().strftime('%d.%m.%Y')}\n\n"
        text += f"<b>Hafta bo'yicha sotuv:</b>\n{weekly_rows}\n"
        text += f"─────────────────\n"
        text += f"💰 Jami tushum: <b>{format_money(total_rev)} so'm</b>\n"
        text += f"🛒 Jami buyurtma: <b>{total_orders} ta</b>\n"

        if total_expenses > 0:
            text += f"\n<b>Xarajatlar:</b>\n{expense_rows}"
            text += f"  Jami: <b>{format_money(total_expenses)} so'm</b>\n"
            text += f"\n{'✅' if profit>0 else '❌'} <b>Sof foyda: {format_money(profit)} so'm</b>\n"
            if total_rev > 0:
                margin = (profit / total_rev) * 100
                text += f"📊 Rentabellik: <b>{margin:.1f}%</b>\n"
        else:
            text += f"\n<i>ℹ️ Xarajatlar API dan olinmadi (ruxsat yo'q)</i>"

        await loading.edit_text(text, parse_mode="HTML")

    except UzumRateLimitError:
        await loading.edit_text("⏳ Rate limit. 1 daqiqa kuting.")
    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")


# ── QAYTARMALAR ─────────────────────────────────────────────
@router.message(F.text.contains("Qaytarmalar") | F.text.contains("Возвраты"))
async def show_returns(message: Message):
    lang, api_key, shop_id = await _ctx(message.from_user.id)
    if not api_key:
        return await message.answer(t(lang or "ru", "not_registered"))

    loading = await message.answer("↩️ Qaytarmalar yuklanmoqda...")
    try:
        raw = await get_returns(api_key, shop_id, size=20)
        returns = [parse_return(r) for r in extract_returns(raw)]

        if not returns:
            return await loading.edit_text(
                "✅ Hozircha qaytarmalar yo'q!" if lang=="uz"
                else "✅ Возвратов пока нет!"
            )

        text = "↩️ <b>Qaytarmalar:</b>\n\n"
        for ret in returns[:15]:
            date = ret["date"][:10] if ret["date"] else "—"
            text += f"🔸 #{str(ret['id'])[-8:]} — {ret['status']}\n"
            if ret["reason"]:
                text += f"   📝 Sabab: {ret['reason'][:40]}\n"
            text += f"   📅 {date}\n\n"

        text += f"Jami: <b>{len(returns)} ta qaytarma</b>"
        await loading.edit_text(text, parse_mode="HTML")

    except UzumAPIError as e:
        await loading.edit_text(f"⚠️ {e}")
