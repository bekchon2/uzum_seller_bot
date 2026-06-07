"""
Uzum Seller API debug — to'g'ri auth bilan
python debug_api.py
"""
import asyncio
import aiohttp
import json

KEY = input("API kalitni kiriting: ").strip()
BASE = "https://api-seller.uzum.uz/api/seller-openapi"

HEADERS = {
    "Authorization": KEY,   # Bearer prefikssiz!
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Origin": "https://seller.uzum.uz",
    "Referer": "https://seller.uzum.uz/",
}

async def test():
    print(f"\n{'='*60}")
    print("Uzum Seller OpenAPI — Test")
    print(f"{'='*60}\n")
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as s:

        # 1. Do'konlar ro'yxati
        print("1. GET /v1/shops")
        async with s.get(BASE + "/v1/shops", headers=HEADERS, ssl=False) as r:
            body = await r.text()
            print(f"   [{r.status}] {body[:400]}")
        print()

        # 2. Do'kon ID ni olamiz
        shop_id = None
        try:
            data = json.loads(body)
            if isinstance(data, list) and data:
                shop_id = data[0].get("id")
            elif isinstance(data, dict):
                payload = data.get("payload", data)
                if isinstance(payload, list) and payload:
                    shop_id = payload[0].get("id")
                elif isinstance(payload, dict):
                    shop_id = payload.get("id")
            print(f"   Shop ID: {shop_id}")
        except Exception as e:
            print(f"   Shop ID topilmadi: {e}")
        print()

        if shop_id:
            # 3. Mahsulotlar
            print(f"2. GET /v1/product/shop/{shop_id}")
            async with s.get(BASE + f"/v1/product/shop/{shop_id}",
                             headers=HEADERS, ssl=False,
                             params={"size": 5, "page": 0, "filter": "ACTIVE"}) as r:
                body = await r.text()
                print(f"   [{r.status}] {body[:500]}")
            print()

            # 4. Finance orders (bugun)
            import datetime
            now = datetime.datetime.now()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            d_from = int(start.timestamp() * 1000)
            d_to = int(now.timestamp() * 1000)

            print(f"3. GET /v1/finance/orders (bugun)")
            async with s.get(BASE + "/v1/finance/orders",
                             headers=HEADERS, ssl=False,
                             params={"shopIds": shop_id, "dateFrom": d_from, "dateTo": d_to, "size": 5}) as r:
                body = await r.text()
                print(f"   [{r.status}] {body[:400]}")
            print()

            # 5. FBS orders
            print(f"4. GET /v2/fbs/orders")
            async with s.get(BASE + "/v2/fbs/orders",
                             headers=HEADERS, ssl=False,
                             params={"shopIds": shop_id, "size": 5, "page": 0}) as r:
                body = await r.text()
                print(f"   [{r.status}] {body[:400]}")
            print()

            # 6. Stocks
            print(f"5. GET /v3/fbs/sku/stocks")
            async with s.get(BASE + "/v3/fbs/sku/stocks",
                             headers=HEADERS, ssl=False,
                             params={"size": 5, "page": 0}) as r:
                body = await r.text()
                print(f"   [{r.status}] {body[:400]}")

asyncio.run(test())
