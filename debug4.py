"""debug4.py — return, finance/expenses, price update endpointlari"""
import asyncio, aiohttp, json, datetime

KEY = input("API key: ").strip()
BASE = "https://api-seller.uzum.uz/api/seller-openapi"
SHOP_ID = 116973
HEADERS = {
    "Authorization": KEY, "Accept": "application/json",
    "Content-Type": "application/json", "User-Agent": "Mozilla/5.0",
    "Origin": "https://seller.uzum.uz", "Referer": "https://seller.uzum.uz/",
}

async def get(s, path, params=None):
    async with s.get(BASE+path, headers=HEADERS, params=params, ssl=False) as r:
        return r.status, await r.text()

async def put(s, path, body):
    async with s.put(BASE+path, headers=HEADERS, json=body, ssl=False) as r:
        return r.status, await r.text()

async def test():
    now = datetime.datetime.now()
    week_ago   = int((now - datetime.timedelta(days=7)).timestamp()*1000)
    month_ago  = int((now - datetime.timedelta(days=30)).timestamp()*1000)
    d_to       = int(now.timestamp()*1000)

    t = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=t) as s:

        print("1. GET /v1/shop/{id}/return (qaytarmalar)")
        await asyncio.sleep(1)
        code, body = await get(s, f"/v1/shop/{SHOP_ID}/return", {"size":3,"page":0})
        print(f"   [{code}] {body[:500]}\n")

        print("2. GET /v1/finance/expenses (xarajatlar)")
        await asyncio.sleep(1)
        code, body = await get(s, "/v1/finance/expenses", {
            "shopId": SHOP_ID, "dateFrom": month_ago, "dateTo": d_to, "size":3})
        print(f"   [{code}] {body[:500]}\n")

        print("3. GET /v1/finance/commission (komissiya)")
        await asyncio.sleep(1)
        code, body = await get(s, "/v1/finance/commission", {
            "shopIds": SHOP_ID, "dateFrom": week_ago, "dateTo": d_to})
        print(f"   [{code}] {body[:500]}\n")

        print("4. GET /v1/product/shop/{id} — birinchi SKU reyting va narx")
        await asyncio.sleep(1)
        code, body = await get(s, f"/v1/product/shop/{SHOP_ID}", {"size":1,"page":0})
        data = json.loads(body)
        prods = data.get("productList",[])
        if prods:
            sku = (prods[0].get("skuList") or [{}])[0]
            keys_interest = ["price","purchasePrice","rating","feedbackQuantity",
                             "skuId","skuFullTitle","avgdsales","forecastOutOfStock"]
            for k in keys_interest:
                val = prods[0].get(k) or sku.get(k)
                if val is not None:
                    print(f"   {k}: {val}")
        print()

        print("5. PUT /v1/sku/price — narx o'zgartirish (dry run, noto'g'ri body)")
        await asyncio.sleep(1)
        code, body = await put(s, "/v1/sku/price", {"test": True})
        print(f"   [{code}] {body[:300]}\n")

        print("6. PUT /v2/sku/price — v2 narx")
        await asyncio.sleep(1)
        code, body = await put(s, "/v2/sku/price", {"test": True})
        print(f"   [{code}] {body[:300]}\n")

        print("7. GET /v1/finance/orders — haftalik (keys tekshirish)")
        await asyncio.sleep(1)
        code, body = await get(s, "/v1/finance/orders", {
            "shopIds": SHOP_ID, "dateFrom": week_ago, "dateTo": d_to, "size":2})
        data = json.loads(body) if code==200 else {}
        items = data.get("orderItems",[])
        if items:
            print(f"   orderItem keys: {list(items[0].keys())}")
            print(f"   sample: {json.dumps(items[0], ensure_ascii=False)[:400]}")
        else:
            print(f"   [{code}] {body[:300]}")
        print()

asyncio.run(test())
