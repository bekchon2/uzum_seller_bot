TRANSLATIONS = {
    "ru": {
        # Onboarding
        "welcome": "👋 Добро пожаловать в <b>Uzum Seller Bot</b>!\n\nЭтот бот поможет вам:\n• 📦 Следить за остатками товаров\n• ⏰ Получать ежедневные отчёты о продажах\n• ⚠️ Узнавать об истечении бесплатного хранения (60 дней)\n• 📊 Анализировать прибыль\n\nВыберите язык:",
        "choose_lang": "🌐 Выберите язык / Tilni tanlang:",
        "lang_set": "✅ Язык установлен: Русский",
        "enter_api_key": "🔑 Введите ваш <b>API Secret Key</b> из кабинета продавца Uzum:\n\n<i>Перейдите: seller.uzum.uz → API Keys → Скопируйте ключ</i>",
        "validating": "⏳ Проверяю ключ...",
        "api_valid": "✅ Ключ принят! Загружаю ваши товары...",
        "api_invalid": "❌ Неверный ключ. Проверьте и попробуйте снова.",
        "api_error": "⚠️ Ошибка соединения. Попробуйте позже.",
        "key_deleted": "🔒 Ключ сохранён безопасно. Сообщение удалено.",

        # Main menu
        "main_menu": "📋 <b>Главное меню</b>",
        "btn_products": "📦 Мои товары",
        "btn_orders": "🛒 Заказы",
        "btn_storage": "🏭 Склад (дни хранения)",
        "btn_report": "📊 Отчёт за сегодня",
        "btn_chart": "📈 График продаж (7 дней)",
        "btn_settings": "⚙️ Настройки",
        "btn_refresh": "🔄 Обновить",

        # Products
        "products_loading": "⏳ Загружаю список товаров...",
        "products_header": "📦 <b>Ваши товары на складе:</b>\n\n",
        "product_row": "• <b>{name}</b>\n  SKU: <code>{sku}</code> | Остаток: <b>{qty} шт.</b> | Цена: {price} сум\n",
        "no_products": "📭 Нет активных товаров.",
        "total_products": "\n<b>Всего товаров:</b> {count} позиций",

        # Orders
        "orders_loading": "⏳ Загружаю заказы...",
        "orders_header": "🛒 <b>Заказы за сегодня:</b>\n\n",
        "orders_total": "📦 Всего заказов: <b>{count}</b>\n💰 Выручка: <b>{revenue:,.0f} сум</b>",
        "no_orders": "📭 Сегодня заказов нет.",

        # Storage warnings
        "storage_header": "🏭 <b>Статус хранения на складе Uzum:</b>\n\n",
        "storage_ok": "✅ {name}\n   Дней в хранении: <b>{days}</b> / 60\n",
        "storage_warn": "⚠️ {name}\n   Дней в хранении: <b>{days}</b> / 60 — <i>осталось {left} дней!</i>\n",
        "storage_critical": "🚨 {name}\n   Дней в хранении: <b>{days}</b> / 60 — <b>КРИТИЧНО! {left} дней!</b>\n",
        "storage_paid": "💸 {name}\n   Дней в хранении: <b>{days}</b> / 60 — <b>ПЛАТНОЕ ХРАНЕНИЕ!</b>\n",
        "storage_tip": "\n<i>💡 Uzum даёт 60 бесплатных дней хранения. После — платное.</i>",

        # Morning report
        "morning_report": "🌅 <b>Утренний отчёт — {date}</b>\n\n"
                          "🛒 Заказов вчера: <b>{orders}</b>\n"
                          "💰 Выручка: <b>{revenue:,.0f} сум</b>\n"
                          "📦 Активных товаров: <b>{products}</b>\n"
                          "⚠️ Товаров с истекающим сроком хранения: <b>{expiring}</b>",

        # Alerts
        "alert_7days": "⚠️ <b>Внимание!</b> Товар <b>{name}</b> хранится <b>{days} дней</b>. Осталось {left} дней до платного хранения!",
        "alert_3days": "🚨 <b>Срочно!</b> Товар <b>{name}</b> — до платного хранения <b>{left} дня!</b>",
        "alert_paid": "💸 <b>ПЛАТНОЕ ХРАНЕНИЕ!</b> Товар <b>{name}</b> находится на складе уже <b>{days} дней!</b> Срочно заберите или продайте!",

        # Settings
        "settings_menu": "⚙️ <b>Настройки</b>",
        "btn_change_lang": "🌐 Сменить язык",
        "btn_change_key": "🔑 Сменить API ключ",
        "btn_back": "◀️ Назад",

        # Chart
        "chart_loading": "📈 Строю график...",
        "chart_title": "Продажи за 7 дней",
        "chart_ylabel": "Выручка (сум)",

        # Errors
        "not_registered": "❌ Сначала введите API ключ. Нажмите /start",
        "token_expired": "🔄 Токен истёк. Обновляю...",
    },

    "uz": {
        # Onboarding
        "welcome": "👋 <b>Uzum Seller Bot</b>ga xush kelibsiz!\n\nBu bot sizga yordam beradi:\n• 📦 Tovarlar qoldiqlarini kuzatish\n• ⏰ Kunlik savdo hisobotlarini olish\n• ⚠️ Bepul saqlash muddati tugashi haqida xabar (60 kun)\n• 📊 Foyda tahlili\n\nTilni tanlang:",
        "choose_lang": "🌐 Tilni tanlang / Выберите язык:",
        "lang_set": "✅ Til o'rnatildi: O'zbek",
        "enter_api_key": "🔑 Uzum sotuvchi kabinetidagi <b>API Secret Key</b>ni kiriting:\n\n<i>O'ting: seller.uzum.uz → API Keys → Kalitni nusxalang</i>",
        "validating": "⏳ Kalit tekshirilmoqda...",
        "api_valid": "✅ Kalit qabul qilindi! Mahsulotlaringiz yuklanmoqda...",
        "api_invalid": "❌ Noto'g'ri kalit. Tekshirib qayta kiriting.",
        "api_error": "⚠️ Ulanish xatosi. Keyinroq urinib ko'ring.",
        "key_deleted": "🔒 Kalit xavfsiz saqlandi. Xabar o'chirildi.",

        # Main menu
        "main_menu": "📋 <b>Asosiy menyu</b>",
        "btn_products": "📦 Mening mahsulotlarim",
        "btn_orders": "🛒 Buyurtmalar",
        "btn_storage": "🏭 Ombor (saqlash kunlari)",
        "btn_report": "📊 Bugungi hisobot",
        "btn_chart": "📈 Savdo grafigi (7 kun)",
        "btn_settings": "⚙️ Sozlamalar",
        "btn_refresh": "🔄 Yangilash",

        # Products
        "products_loading": "⏳ Mahsulotlar ro'yxati yuklanmoqda...",
        "products_header": "📦 <b>Omboringizdagi mahsulotlar:</b>\n\n",
        "product_row": "• <b>{name}</b>\n  SKU: <code>{sku}</code> | Qoldiq: <b>{qty} dona</b> | Narx: {price} so'm\n",
        "no_products": "📭 Faol mahsulotlar yo'q.",
        "total_products": "\n<b>Jami mahsulotlar:</b> {count} ta",

        # Orders
        "orders_loading": "⏳ Buyurtmalar yuklanmoqda...",
        "orders_header": "🛒 <b>Bugungi buyurtmalar:</b>\n\n",
        "orders_total": "📦 Jami buyurtmalar: <b>{count}</b>\n💰 Tushum: <b>{revenue:,.0f} so'm</b>",
        "no_orders": "📭 Bugun buyurtma yo'q.",

        # Storage warnings
        "storage_header": "🏭 <b>Uzum omborida saqlash holati:</b>\n\n",
        "storage_ok": "✅ {name}\n   Saqlash kunlari: <b>{days}</b> / 60\n",
        "storage_warn": "⚠️ {name}\n   Saqlash kunlari: <b>{days}</b> / 60 — <i>{left} kun qoldi!</i>\n",
        "storage_critical": "🚨 {name}\n   Saqlash kunlari: <b>{days}</b> / 60 — <b>KRITIK! {left} kun!</b>\n",
        "storage_paid": "💸 {name}\n   Saqlash kunlari: <b>{days}</b> / 60 — <b>PULLIK SAQLASH!</b>\n",
        "storage_tip": "\n<i>💡 Uzum 60 kun bepul saqlash beradi. Keyin — pullik.</i>",

        # Morning report
        "morning_report": "🌅 <b>Ertalabki hisobot — {date}</b>\n\n"
                          "🛒 Kecha buyurtmalar: <b>{orders}</b>\n"
                          "💰 Tushum: <b>{revenue:,.0f} so'm</b>\n"
                          "📦 Faol mahsulotlar: <b>{products}</b>\n"
                          "⚠️ Muddati tugayotgan mahsulotlar: <b>{expiring}</b>",

        # Alerts
        "alert_7days": "⚠️ <b>Diqqat!</b> <b>{name}</b> mahsuloti <b>{days} kun</b> saqlanmoqda. Pullik saqlashga {left} kun qoldi!",
        "alert_3days": "🚨 <b>Shoshilinch!</b> <b>{name}</b> — pullik saqlashga <b>{left} kun qoldi!</b>",
        "alert_paid": "💸 <b>PULLIK SAQLASH!</b> <b>{name}</b> mahsuloti <b>{days} kun</b> omborida turibdi! Shoshilinch olib keting yoki soting!",

        # Settings
        "settings_menu": "⚙️ <b>Sozlamalar</b>",
        "btn_change_lang": "🌐 Tilni o'zgartirish",
        "btn_change_key": "🔑 API kalitni o'zgartirish",
        "btn_back": "◀️ Orqaga",

        # Chart
        "chart_loading": "📈 Grafik tayyorlanmoqda...",
        "chart_title": "7 kunlik savdo",
        "chart_ylabel": "Tushum (so'm)",

        # Errors
        "not_registered": "❌ Avval API kalitni kiriting. /start ni bosing",
        "token_expired": "🔄 Token eskirdi. Yangilanmoqda...",
    }
}


def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in TRANSLATIONS else "ru"
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["ru"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text
