from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user, upsert_user, set_lang
from locales.i18n import t
from utils.keyboards import lang_keyboard, main_menu_keyboard, settings_keyboard
from services.uzum_api import get_shops, parse_shop, UzumAuthError, UzumAPIError

router = Router()


class States(StatesGroup):
    waiting_lang = State()
    waiting_api_key = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    if user and user["api_key"]:
        lang = user["lang"] or "ru"
        shop = user["shop_name"] or "Do'konim"
        await message.answer(
            f"🏪 <b>{shop}</b>\n\n" + t(lang, "main_menu"),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML"
        )
        return
    await state.set_state(States.waiting_lang)
    await message.answer(t("ru", "welcome"), reply_markup=lang_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.in_({"lang_ru", "lang_uz"}), States.waiting_lang)
async def cb_lang_onboard(callback: CallbackQuery, state: FSMContext):
    lang = "ru" if callback.data == "lang_ru" else "uz"
    await upsert_user(callback.from_user.id, callback.from_user.username, lang=lang)
    await state.update_data(lang=lang)
    await callback.message.edit_text(t(lang, "lang_set"), parse_mode="HTML")
    await callback.message.answer(t(lang, "enter_api_key"), parse_mode="HTML")
    await state.set_state(States.waiting_api_key)
    await callback.answer()


@router.message(States.waiting_api_key)
async def handle_api_key(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    api_key = message.text.strip()

    try:
        await message.delete()
    except Exception:
        pass

    processing = await message.answer(t(lang, "validating"), parse_mode="HTML")

    try:
        shops = await get_shops(api_key)

        if shops:
            shop = parse_shop(shops[0])
            shop_id = shop["id"]
            shop_name = shop["name"]
        else:
            shop_id = 0
            shop_name = "Do'konim"

        await upsert_user(
            message.from_user.id,
            message.from_user.username,
            lang=lang,
            api_key=api_key,
            shop_id=shop_id,
            shop_name=shop_name,
        )

        await processing.edit_text(
            f"✅ {t(lang, 'api_valid')}\n🏪 <b>{shop_name}</b>",
            parse_mode="HTML"
        )
        await state.clear()
        await message.answer(
            f"🏪 <b>{shop_name}</b>\n\n" + t(lang, "main_menu"),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML"
        )

    except UzumAuthError:
        await processing.edit_text(t(lang, "api_invalid"), parse_mode="HTML")
        await message.answer(t(lang, "enter_api_key"), parse_mode="HTML")
    except UzumAPIError as e:
        await processing.edit_text(
            f"{t(lang, 'api_error')}\n\n<code>{e}</code>", parse_mode="HTML"
        )
    except Exception as e:
        await processing.edit_text(f"❌ Xato:\n<code>{e}</code>", parse_mode="HTML")


@router.message(F.text.contains("Настройки") | F.text.contains("Sozlamalar"))
async def show_settings(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return await message.answer("❌ /start")
    lang = user["lang"] or "ru"
    await message.answer(t(lang, "settings_menu"),
                         reply_markup=settings_keyboard(lang), parse_mode="HTML")


@router.callback_query(F.data == "change_lang")
async def cb_change_lang(callback: CallbackQuery, state: FSMContext):
    user = await get_user(callback.from_user.id)
    lang = user["lang"] if user else "ru"
    await state.update_data(lang=lang)
    await callback.message.edit_text(t(lang, "choose_lang"), reply_markup=lang_keyboard())
    await state.set_state(States.waiting_lang)
    await callback.answer()


@router.callback_query(F.data.in_({"lang_ru", "lang_uz"}))
async def cb_lang_change(callback: CallbackQuery, state: FSMContext):
    lang = "ru" if callback.data == "lang_ru" else "uz"
    await set_lang(callback.from_user.id, lang)
    await callback.message.edit_text(t(lang, "lang_set"), parse_mode="HTML")
    await callback.message.answer(t(lang, "main_menu"),
                                  reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "change_key")
async def cb_change_key(callback: CallbackQuery, state: FSMContext):
    user = await get_user(callback.from_user.id)
    lang = user["lang"] if user else "ru"
    await state.update_data(lang=lang)
    await callback.message.answer(t(lang, "enter_api_key"), parse_mode="HTML")
    await state.set_state(States.waiting_api_key)
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def cb_back(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    lang = user["lang"] if user else "ru"
    await callback.message.answer(t(lang, "main_menu"),
                                  reply_markup=main_menu_keyboard(lang), parse_mode="HTML")
    await callback.answer()
