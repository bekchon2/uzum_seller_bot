"""
debug3.py — Invoice, stocks va orders formatlarini tekshirish
"""
import asyncio, aiohttp, json, datetime

KEY = input("API kalitni kiriting: ").strip()
BASE = "https://api-seller.uzum.uz/api/seller-openapi"
SHOP_ID = 116973

HEADERS = {
    "Authorization": KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://seller.uzum.uz",
    "Referer": "https://seller.uzum.uz/",
}

async def get(session, path, params=None):
    async with session.get(BASE + path, headers=HEADERS, params=params, ssl=False) as r:
        body = await r.text()
        return r.status, body

async def test():
    print(f"\n{'='*65}")
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as s:

        # 1. Mahsulotlar — SKU qoldiqlarini ko'rish
        print("1. GET /v1/product/shop — birinchi mahsulot SKU tafsiloti")
        code, body = await get(s, f"/v1/product/shop/{SHOP_ID}", {"size": 2, "page": 0, "filter": "ACTIVE"})
        data = json.loads(body)
        products = data.get("productList", [])
        if products:
            p = products[0]
            print(f"   productId: {p.get('productId')}")
            print(f"   title: {p.get('title','?')}")
            skus = p.get("skuList", [])
            if skus:
                print(f"   skuList[0] keys: {list(skus[0].keys())}")
                print(f"   skuList[0]: {json.dumps(skus[0], ensure_ascii=False)[:400]}")
        print()

        # 2. FBO Invoice (Nakладные поставки) — omborga kelgan sana
        print("2. GET /v1/shop/{shopId}/invoice — FBO nakładnye")
        code, body = await get(s, f"/v1/shop/{SHOP_ID}/invoice", {"size": 3, "page": 0})
        print(f"   [{code}] {body[:600]}")
        print()

        # 3. Yangi invoice endpoint
        print("3. GET /v1/invoice")
        code, body = await get(s, "/v1/invoice", {"size": 3, "page": 0, "shopId": SHOP_ID})
        print(f"   [{code}] {body[:600]}")
        print()

        # 4. Finance orders — to'liq format
        now = datetime.datetime.now()
        month_ago = now - datetime.timedelta(days=30)
        d_from = int(month_ago.timestamp() * 1000)
        d_to = int(now.timestamp() * 1000)

        print("4. GET /v1/finance/orders — oxirgi 30 kun, birinchi element")
        code, body = await get(s, "/v1/finance/orders", {
            "shopIds": SHOP_ID, "dateFrom": d_from, "dateTo": d_to, "size": 3, "page": 0
        })
        print(f"   [{code}] {body[:800]}")
        print()

        # 5. FBS orders — to'liq format
        print("5. GET /v2/fbs/orders — oxirgi 30 kun")
        code, body = await get(s, "/v2/fbs/orders", {
            "shopIds": SHOP_ID, "dateFrom": d_from, "dateTo": d_to, "size": 3, "page": 0
        })
        print(f"   [{code}] {body[:800]}")
        print()

        # 6. FBS orders count
        print("6. GET /v2/fbs/orders/count")
        code, body = await get(s, "/v2/fbs/orders/count", {"shopIds": SHOP_ID})
        print(f"   [{code}] {body[:300]}")
        print()

        # 7. Return
        print("7. GET /v1/shop/{shopId}/return")
        code, body = await get(s, f"/v1/shop/{SHOP_ID}/return", {"size": 3, "page": 0})
        print(f"   [{code}] {body[:400]}")

asyncio.run(test())
