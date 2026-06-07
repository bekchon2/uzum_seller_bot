import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "uzum_bot.db")

CREATE_TABLES = [
    """CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        username    TEXT,
        lang        TEXT DEFAULT 'ru',
        api_key     TEXT,
        shop_id     INTEGER DEFAULT 0,
        shop_name   TEXT DEFAULT '',
        created_at  INTEGER DEFAULT (strftime('%s','now'))
    )""",
    """CREATE TABLE IF NOT EXISTS notification_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        notif_type  TEXT,
        sent_at     INTEGER DEFAULT (strftime('%s','now'))
    )""",
]


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        for stmt in CREATE_TABLES:
            await db.execute(stmt)
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone()


async def upsert_user(user_id: int, username: str = None, lang: str = "ru",
                      api_key: str = None, shop_id: int = None, shop_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users(user_id, username, lang, api_key, shop_id, shop_name)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=COALESCE(excluded.username, username),
                lang=COALESCE(excluded.lang, lang),
                api_key=COALESCE(excluded.api_key, api_key),
                shop_id=COALESCE(excluded.shop_id, shop_id),
                shop_name=COALESCE(excluded.shop_name, shop_name)
        """, (user_id, username, lang, api_key, shop_id or 0, shop_name or ""))
        await db.commit()


async def set_lang(user_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE api_key IS NOT NULL") as cur:
            return await cur.fetchall()


async def log_notification(user_id: int, notif_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO notification_log(user_id, notif_type) VALUES(?,?)",
            (user_id, notif_type)
        )
        await db.commit()


async def was_notified_today(user_id: int, notif_type: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT 1 FROM notification_log
            WHERE user_id=? AND notif_type=?
              AND date(sent_at,'unixepoch')=date('now')
        """, (user_id, notif_type)) as cur:
            return await cur.fetchone() is not None
