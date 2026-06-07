"""
Uzum Seller OpenAPI wrapper
Auth: Authorization: <api_key>  (Bearer prefikssiz)
Base: https://api-seller.uzum.uz/api/seller-openapi
"""
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)
BASE_URL = "https://api-seller.uzum.uz/api/seller-openapi"


class UzumAPIError(Exception):
    pass

class UzumAuthError(UzumAPIError):
    pass

class UzumRateLimitError(UzumAPIError):
    pass


def _headers(api_key: str) -> dict:
    return {
        "Authorization": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://seller.uzum.uz",
        "Referer": "https://seller.uzum.uz/",
    }


async def _get(endpoint: str, api_key: str, params: dict = None,
               retry: int = 2) -> dict | list:
    url = BASE_URL + endpoint
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=_headers(api_key),
                               params=params, ssl=False) as resp:
            body = await resp.text()
            logger.info(f"[{resp.status}] GET {endpoint}")
            if resp.status == 401:
                raise UzumAuthError("API kalit noto'g'ri")
            if resp.status == 429:
                if retry > 0:
                    await asyncio.sleep(2)
                    return await _get(endpoint, api_key, params, retry - 1)
                raise UzumRateLimitError("So'rovlar limiti. Bir oz kuting.")
            if resp.status != 200:
                raise UzumAPIError(f"API xatosi {resp.status}: {body[:150]}")
            import json
            return json.loads(body)


# ── Endpoints ──────────────────────────────────────────────

async def get_shops(api_key: str) -> list[dict]:
    """GET /v1/shops → [{"id":116973,"name":"JoyKid"}]"""
    data = await _get("/v1/shops", api_key)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("payload", "shops", "items", "data"):
            if k in data and isinstance(data[k], list):
                return data[k]
    return []


async def get_products(api_key: str, shop_id: int,
                       page: int = 0, size: int = 100) -> dict:
    """GET /v1/product/shop/{shopId}
    Response: {"productList": [{..., "skuList": [{
        "quantityActive": 49,
        "quantityAvailable": 49,
        "purchasePrice": ..., "price": ...,
        "pstorage": {...}   ← pullik saqlash ma'lumoti
    }]}]}
    """
    return await _get(f"/v1/product/shop/{shop_id}", api_key, params={
        "size": size, "page": page,
        "filter": "ACTIVE", "sortBy": "LEFTOVERS", "order": "DESC",
    })


async def get_invoices(api_key: str, shop_id: int,
                       page: int = 0, size: int = 50) -> list:
    """GET /v1/shop/{shopId}/invoice — FBO nakładnye
    Response: [{"id":..., "dateAccepted":1780529427072,
                "invoiceStatus":{"value":"ACCEPTED"}, ...}]
    """
    data = await _get(f"/v1/shop/{shop_id}/invoice", api_key,
                      params={"size": size, "page": page})
    if isinstance(data, list):
        return data
    return data.get("payload") or data.get("items") or []


async def get_invoice_products(api_key: str, shop_id: int,
                                invoice_id: int) -> dict:
    """GET /v1/shop/{shopId}/invoice/products — nakładnoy tarkibi"""
    return await _get(f"/v1/shop/{shop_id}/invoice/products", api_key,
                      params={"invoiceId": invoice_id})


async def get_finance_orders(api_key: str, shop_id: int,
                             date_from: int, date_to: int,
                             page: int = 0, size: int = 100) -> dict:
    """GET /v1/finance/orders
    Response: {"orderItems": [...], "totalElements": N}
    """
    return await _get("/v1/finance/orders", api_key, params={
        "shopIds": shop_id, "dateFrom": date_from,
        "dateTo": date_to, "page": page, "size": size,
    })


async def get_fbs_orders(api_key: str, shop_id: int,
                         date_from: int = None, date_to: int = None,
                         status: str = None,
                         page: int = 0, size: int = 50) -> dict:
    """GET /v2/fbs/orders
    Response: {"payload": {"orders": [...]}}
    """
    params = {"shopIds": shop_id, "page": page, "size": size}
    if date_from: params["dateFrom"] = date_from
    if date_to:   params["dateTo"] = date_to
    if status:    params["status"] = status
    return await _get("/v2/fbs/orders", api_key, params=params)


async def get_fbs_orders_count(api_key: str, shop_id: int) -> dict:
    return await _get("/v2/fbs/orders/count", api_key,
                      params={"shopIds": shop_id})


# ── Parsers ────────────────────────────────────────────────

def parse_shop(raw: dict) -> dict:
    return {
        "id":   raw.get("id") or raw.get("shopId") or 0,
        "name": raw.get("name") or raw.get("title") or "Do'konim",
    }


def parse_product(raw: dict) -> dict:
    """
    Haqiqiy SKU kalitlari:
      quantityActive   — faol (sotuvdagi) qoldiq ✅
      quantityAvailable — mavjud qoldiq
      quantityFbs      — FBS qoldiq
      purchasePrice    — xarid narxi
      price            — sotish narxi
      pstorage         — pullik saqlash ma'lumoti
      avgdsales        — o'rtacha kunlik sotuv
      forecastOutOfStock — tugashiga taxminiy kun
    """
    skus = raw.get("skuList") or []
    s0 = skus[0] if skus else {}

    qty_active    = sum(s.get("quantityActive") or 0 for s in skus)
    qty_available = sum(s.get("quantityAvailable") or 0 for s in skus)
    qty_fbs       = sum(s.get("quantityFbs") or 0 for s in skus)
    qty_sold      = sum(s.get("quantitySold") or 0 for s in skus)

    price    = s0.get("price") or s0.get("purchasePrice") or 0
    avg_sale = s0.get("avgdsales") or 0
    forecast = s0.get("forecastOutOfStock") or 0

    # Pstorage — pullik saqlash
    pstorage = s0.get("pstorage") or {}

    name = (raw.get("title") or
            s0.get("productTitle") or
            s0.get("skuFullTitle") or
            f"Mahsulot #{raw.get('productId','')}")

    return {
        "id":           raw.get("productId") or raw.get("id") or "",
        "sku_id":       s0.get("skuId") or "",
        "sku":          s0.get("skuFullTitle") or s0.get("article") or "",
        "name":         name,
        "qty":          qty_active,       # Asosiy ko'rsatkich
        "qty_available":qty_available,
        "qty_fbs":      qty_fbs,
        "qty_sold":     qty_sold,
        "price":        price,
        "avg_sales":    avg_sale,         # Kunlik o'rtacha sotuv
        "forecast_days":forecast,         # Tugashiga taxminiy kun
        "days_in_storage": 0,             # Invoice dan hisoblanadi
        "pstorage":     pstorage,
        "category":     raw.get("category") or "",
        "status":       (raw.get("status") or {}).get("value") or "",
    }


def parse_invoice(raw: dict) -> dict:
    """
    Haqiqiy format:
    {
      "id": 3524496,
      "dateCreated": "19.05.2026",        ← string
      "dateAccepted": 1780529427072,      ← Unix ms ✅
      "invoiceStatus": {"value": "ACCEPTED"},
      "totalAccepted": 254,
    }
    """
    import datetime
    status = (raw.get("invoiceStatus") or {}).get("value") or raw.get("status") or ""

    # dateAccepted — omborga qabul qilingan vaqt (Unix ms)
    date_accepted_ms = raw.get("dateAccepted") or 0
    date_accepted = None
    days_in_storage = 0

    if date_accepted_ms and status == "ACCEPTED":
        date_accepted = datetime.datetime.fromtimestamp(date_accepted_ms / 1000)
        days_in_storage = (datetime.datetime.now() - date_accepted).days

    return {
        "id":              raw.get("id") or 0,
        "invoice_number":  raw.get("invoiceNumber") or "",
        "date_created":    raw.get("dateCreated") or "",
        "date_accepted":   date_accepted,
        "date_accepted_ms":date_accepted_ms,
        "days_in_storage": days_in_storage,
        "status":          status,
        "is_accepted":     status == "ACCEPTED",
        "total_accepted":  raw.get("totalAccepted") or 0,
    }


def parse_finance_order(raw: dict) -> dict:
    return {
        "id":      str(raw.get("id") or raw.get("orderId") or ""),
        "revenue": raw.get("sellerPrice") or raw.get("amount") or raw.get("totalPrice") or 0,
        "status":  raw.get("status") or "",
        "date":    raw.get("date") or raw.get("orderDate") or raw.get("createdAt") or "",
    }


def parse_fbs_order(raw: dict) -> dict:
    items = raw.get("orderItems") or raw.get("items") or []
    revenue = sum(
        (i.get("price") or i.get("sellPrice") or 0) * (i.get("quantity") or 1)
        for i in items
    )
    if not revenue:
        revenue = raw.get("totalPrice") or raw.get("amount") or 0
    return {
        "id":      str(raw.get("id") or raw.get("orderId") or ""),
        "status":  raw.get("status") or "",
        "revenue": revenue,
        "date":    raw.get("createdAt") or raw.get("date") or "",
        "items":   items,
    }


# ── Extractors ─────────────────────────────────────────────

def extract_products(data: dict) -> list:
    if isinstance(data, list): return data
    return (data.get("productList") or data.get("products") or
            data.get("items") or data.get("content") or [])


def extract_finance_orders(data: dict) -> list:
    if isinstance(data, list): return data
    return (data.get("orderItems") or data.get("orders") or
            data.get("items") or data.get("content") or [])


def extract_fbs_orders(data: dict) -> list:
    if isinstance(data, list): return data
    payload = data.get("payload", data)
    if isinstance(payload, dict):
        return (payload.get("orders") or payload.get("items") or
                payload.get("content") or [])
    if isinstance(payload, list): return payload
    return []


# ── Yangi endpointlar ──────────────────────────────────────

async def get_returns(api_key: str, shop_id: int,
                      page: int = 0, size: int = 50) -> dict:
    """GET /v1/return — qaytarmalar ro'yxati
    Response: {"payload": [...], "timestamp": "..."}
    """
    return await _get("/v1/return", api_key,
                      params={"page": page, "size": size})


async def get_expenses(api_key: str, shop_id: int,
                       date_from: int = None, date_to: int = None,
                       page: int = 0, size: int = 100) -> dict:
    """GET /v1/finance/expenses — xarajatlar (komissiya, saqlash, va h.k.)
    Response: {"payload": {"payments": [...]}}
    """
    params = {"shopId": shop_id, "shopIds": shop_id, "page": page, "size": size}
    if date_from: params["dateFrom"] = date_from
    if date_to:   params["dateTo"] = date_to
    return await _get("/v1/finance/expenses", api_key, params=params)


async def update_sku_price(api_key: str, shop_id: int,
                           product_id: int, sku_id: int,
                           sell_price: int, full_price: int = None) -> dict:
    """POST /v1/product/{shopId}/sendPriceData — narx o'zgartirish
    Body: {"productId": 123, "skuList": [{"skuId": 456, "sellPrice": 50000, "fullPrice": 60000}]}
    """
    url = BASE_URL + f"/v1/product/{shop_id}/sendPriceData"
    body = {
        "productId": product_id,
        "skuList": [{
            "skuId": sku_id,
            "sellPrice": sell_price,
            "fullPrice": full_price or sell_price,
        }]
    }
    import aiohttp, json as _json
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, headers=_headers(api_key),
                                json=body, ssl=False) as resp:
            body_text = await resp.text()
            import logging as _log
            _log.getLogger(__name__).info(f"[{resp.status}] POST sendPriceData → {body_text[:150]}")
            if resp.status == 401:
                raise UzumAuthError("API kalit noto'g'ri")
            if resp.status == 429:
                raise UzumRateLimitError("Rate limit")
            if resp.status not in (200, 201, 204):
                raise UzumAPIError(f"Narx o'zgartirishda xato {resp.status}: {body_text[:200]}")
            try:
                return _json.loads(body_text)
            except Exception:
                return {"ok": True}


def parse_return(raw: dict) -> dict:
    """Qaytarma formati"""
    items = raw.get("items") or raw.get("returnItems") or []
    return {
        "id":        raw.get("id") or raw.get("returnId") or "",
        "status":    raw.get("status") or raw.get("returnStatus") or "",
        "date":      raw.get("dateCreated") or raw.get("date") or "",
        "reason":    raw.get("reason") or raw.get("returnReason") or "",
        "items":     items,
        "total":     raw.get("totalPrice") or raw.get("amount") or 0,
    }


def parse_expense(raw: dict) -> dict:
    """Xarajat (to'lov) formati
    fields: id, name, source, paymentPrice, amount, status, dateCreated
    """
    return {
        "id":     raw.get("id") or "",
        "name":   raw.get("name") or "",
        "source": raw.get("source") or "",
        "price":  raw.get("paymentPrice") or raw.get("amount") or 0,
        "qty":    raw.get("amount") or 1,
        "status": raw.get("status") or "",
        "date":   raw.get("dateCreated") or raw.get("dateUpdated") or "",
    }


def extract_returns(data: dict) -> list:
    """{"payload": [...]} → list"""
    if isinstance(data, list): return data
    payload = data.get("payload", data)
    if isinstance(payload, list): return payload
    if isinstance(payload, dict):
        return (payload.get("returns") or payload.get("items") or
                payload.get("content") or [])
    return []


def extract_expenses(data: dict) -> list:
    """{"payload": {"payments": [...]}} → list"""
    if isinstance(data, list): return data
    payload = data.get("payload", data)
    if isinstance(payload, dict):
        return (payload.get("payments") or payload.get("items") or
                payload.get("content") or [])
    if isinstance(payload, list): return payload
    return []
