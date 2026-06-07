"""
debug2.py — form-data, query param va boshqa formatlarni sinash
python debug2.py
"""
import asyncio
import aiohttp
import json

KEY = input("Secret key kiriting: ").strip()
BASE = "https://api-seller.uzum.uz"

BASE_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Origin": "https://seller.uzum.uz",
    "Referer": "https://seller.uzum.uz/",
}

async def post_json(session, url, payload, extra_h={}):
    h = {**BASE_HEADERS, "Content-Type": "application/json", **extra_h}
    async with session.post(url, json=payload, headers=h, ssl=False) as r:
        return r.status, await r.text()

async def post_form(session, url, payload, extra_h={}):
    h = {**BASE_HEADERS, **extra_h}
    async with session.post(url, data=payload, headers=h, ssl=False) as r:
        return r.status, await r.text()

async def post_text(session, url, body_str, extra_h={}):
    h = {**BASE_HEADERS, "Content-Type": "text/plain", **extra_h}
    async with session.post(url, data=body_str, headers=h, ssl=False) as r:
        return r.status, await r.text()

async def get_req(session, url, params={}, extra_h={}):
    h = {**BASE_HEADERS, **extra_h}
    async with session.get(url, params=params, headers=h, ssl=False) as r:
        return r.status, await r.text()

def show(code, body, desc):
    short = body[:300].replace("\n", " ")
    tag = "✅ SUCCESS" if code == 200 else f"[{code}]"
    print(f"{tag} {desc}")
    print(f"   {short}\n")

async def test():
    print(f"\n{'='*65}")
    print("debug2 — Form-data, query, plain text formatlar")
    print(f"{'='*65}\n")

    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        ep1 = BASE + "/api/seller/v1/auth/token"
        ep2 = BASE + "/api/main/v1/token"

        # 1. Form-data formatlar
        for field in ["secret_key", "secretKey", "apiKey", "key", "token"]:
            code, body = await post_form(s, ep1, {field: KEY})
            show(code, body, f"form-data {field} → seller/v1/auth/token")

        # 2. Query parameter
        for field in ["secret_key", "secretKey", "key"]:
            code, body = await get_req(s, ep1, {field: KEY})
            show(code, body, f"GET ?{field} → seller/v1/auth/token")

        # 3. Plain text body
        code, body = await post_text(s, ep1, KEY)
        show(code, body, f"plain text body → seller/v1/auth/token")

        # 4. JSON bilan turli wrapper
        for wrapper in [
            {"credentials": {"secret_key": KEY}},
            {"auth": {"secret_key": KEY}},
            {"data": {"secret_key": KEY}},
            {"request": {"secret_key": KEY}},
        ]:
            code, body = await post_json(s, ep1, wrapper)
            show(code, body, f"wrapped JSON {list(wrapper.keys())[0]} → seller/v1/auth/token")

        # 5. main/v1/token with form-data
        for field in ["secret_key", "secretKey"]:
            code, body = await post_form(s, ep2, {field: KEY})
            show(code, body, f"form-data {field} → main/v1/token")

        # 6. Swagger UI dan keladigan /api/main/v1/token boshqa header bilan
        code, body = await post_json(s, ep2, {"secret_key": KEY},
                                     {"X-Seller-Token": KEY})
        show(code, body, "main/v1/token + X-Seller-Token header")

        # 7. Kalit to'g'ridan to'g'ri Authorization header sifatida
        code, body = await post_json(s, ep2, {},
                                     {"Authorization": KEY})
        show(code, body, "main/v1/token + Authorization: raw key")

asyncio.run(test())
