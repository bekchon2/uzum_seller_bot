from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales.i18n import t


def lang_keyboard() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇷🇺 Русский", callback_data="lang_ru")
    b.button(text="🇺🇿 O'zbek",  callback_data="lang_uz")
    b.adjust(2)
    return b.as_markup()


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=t(lang, "btn_products"))
    b.button(text=t(lang, "btn_orders"))
    b.button(text=t(lang, "btn_storage"))
    b.button(text=t(lang, "btn_report"))
    b.button(text="📈 Haftalik hisobot" if lang=="uz" else "📈 Недельный отчёт")
    b.button(text="📅 Oylik hisobot"   if lang=="uz" else "📅 Месячный отчёт")
    b.button(text="↩️ Qaytarmalar"     if lang=="uz" else "↩️ Возвраты")
    b.button(text=t(lang, "btn_settings"))
    b.adjust(2, 2, 2, 2)
    return b.as_markup(resize_keyboard=True)


def settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "btn_change_lang"), callback_data="change_lang")
    b.button(text=t(lang, "btn_change_key"),  callback_data="change_key")
    b.button(text=t(lang, "btn_back"),         callback_data="back_main")
    b.adjust(1)
    return b.as_markup()


def storage_chart_keyboard(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📊 Grafik ko'rish" if lang=="uz" else "📊 Показать график",
             callback_data="storage_chart")
    b.button(text=t(lang, "btn_back"), callback_data="back_main")
    b.adjust(1)
    return b.as_markup()


def back_keyboard(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t(lang, "btn_back"), callback_data="back_main")
    return b.as_markup()
