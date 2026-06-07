"""
Omborxona saqlash kunlarini hisoblash.
Invoice (nakładnoy) dan dateAccepted ni olib, hozirgi kungacha hisoblaydi.
Faqat status=ACCEPTED bo'lgan invoicelar hisobga olinadi.
"""
import datetime
import logging
from services.uzum_api import get_invoices, parse_invoice

logger = logging.getLogger(__name__)


async def get_storage_days_map(api_key: str, shop_id: int) -> dict[str, int]:
    """
    Returns: {invoice_id_str: days_in_storage}
    Eng oxirgi ACCEPTED invoice asosida hisoblanadi.
    """
    try:
        raw_invoices = await get_invoices(api_key, shop_id, size=50)
        invoices = [parse_invoice(inv) for inv in raw_invoices]

        # Faqat qabul qilinganlar
        accepted = [inv for inv in invoices if inv["is_accepted"]]
        accepted.sort(key=lambda x: x["date_accepted_ms"], reverse=True)

        # Eng oxirgi invoice necha kun omborga kelganini qaytaradi
        if accepted:
            latest = accepted[0]
            return {
                "days": latest["days_in_storage"],
                "date_accepted": latest["date_accepted"],
                "invoice_number": latest["invoice_number"],
                "total_accepted": latest["total_accepted"],
                "all_invoices": accepted,
            }
    except Exception as e:
        logger.error(f"Storage tracker error: {e}")

    return {"days": 0, "date_accepted": None, "invoice_number": "", "total_accepted": 0, "all_invoices": []}
