# 🛒 Uzum Seller Telegram Bot

Uzum Market sotuvchilari uchun Telegram bot — omborxona, buyurtmalar va savdo tahlili.

## 🚀 Imkoniyatlar

| Funksiya | Tavsif |
|---|---|
| 📦 Mahsulotlar | Barcha aktiv tovarlar, qoldiqlar, narxlar |
| 🛒 Buyurtmalar | Bugungi buyurtmalar va tushum |
| 🏭 Ombor holati | Har bir tovar uchun saqlash kunlari (60 kunlik limit) |
| 📊 Kunlik hisobot | Kecha sotilganlar va umumiy tushum |
| 📈 Savdo grafigi | 7 kunlik vizual grafik |
| ⚠️ Ogohlantirishlar | 7 kun, 3 kun, 0 kun qolganida avtomatik xabar |
| 🌅 Ertalabki hisobot | Har kuni soat 08:00 da Toshkent vaqti bo'yicha |
| 🌐 Ko'p tilli | Rus va O'zbek tili |

## ⚙️ O'rnatish (Local)

```bash
# 1. Papkaga kiring
cd uzum_seller_bot

# 2. Virtual muhit yarating
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Kutubxonalarni o'rnating
pip install -r requirements.txt

# 4. .env fayl yarating
cp .env.example .env
# .env faylni oching va BOT_TOKEN ni qo'ying

# 5. Botni ishga tushiring
python main.py
```

## 🔑 API Key olish

1. https://seller.uzum.uz ga kiring
2. Sozlamalar → API Keys → Yangi kalit yarating
3. Botga `/start` yuboring va kalitni kiriting

## ☁️ Render.com ga deploy qilish

1. GitHub ga push qiling
2. https://render.com → New Web Service
3. Repository ni ulang
4. Environment variable: `BOT_TOKEN = your_token`
5. Build command: `pip install -r requirements.txt`
6. Start command: `python main.py`

> **Disk:** Render free tier uchun persistent disk qo'shing (SQLite uchun)
> Mount path: `/data`
> `DB_PATH=/data/uzum_bot.db` ni env ga qo'shing

## 📁 Loyiha tuzilishi

```
uzum_seller_bot/
├── main.py              # Asosiy fayl
├── database.py          # SQLite modellari
├── requirements.txt
├── render.yaml          # Render config
├── handlers/
│   ├── start.py         # /start, onboarding, sozlamalar
│   └── main_menu.py     # Mahsulotlar, buyurtmalar, ombor, grafiklar
├── services/
│   ├── uzum_api.py      # Uzum Seller API integratsiya
│   ├── charts.py        # Matplotlib grafiklar
│   └── scheduler.py     # Avtomatik hisobotlar
├── locales/
│   └── i18n.py          # Rus/O'zbek tarjimalar
└── utils/
    ├── keyboards.py     # Telegram tugmalar
    └── helpers.py       # Yordamchi funksiyalar
```

## 🔔 Ogohlantirishlar jadvali

| Holat | Qachon | Chastota |
|---|---|---|
| 🌅 Ertalabki hisobot | 08:00 (Toshkent) | Har kuni |
| ⚠️ 7 kun qoldi | 53+ kun saqlashda | Kuniga 1 marta |
| 🚨 3 kun qoldi | 57+ kun saqlashda | Kuniga 1 marta |
| 💸 Pullik saqlash | 60+ kun | Kuniga 1 marta |
