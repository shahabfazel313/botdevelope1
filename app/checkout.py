from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from .db import get_order
from .config import CURRENCY

def _status_fa(code: str) -> str:
    return {
        "AWAITING_PAYMENT": "در انتظار پرداخت",
        "PENDING_CONFIRM": "در انتظار تایید پرداخت",
        "PENDING_PLAN": "در انتظار تایید طرح",
        "APPROVED": "پرداخت تایید شد",
        "IN_PROGRESS": "در حال انجام",
        "READY_TO_DELIVER": "آماده تحویل",
        "DELIVERED": "تحویل شد",
        "COMPLETED": "تکمیل‌شده",
        "EXPIRED": "منقضی",
        "REJECTED": "رد شده",
        "CANCELED": "لغو شده",
    }.get(code, code)

def _order_title(service_category: str, code: str) -> str:
    if service_category == "AI":
        return {"team":"اکانت ChatGPT Team", "plus":"اکانت ChatGPT Plus", "google":"اکانت Google AI Pro"}.get(code, "سرویس هوش مصنوعی")
    if service_category == "TG":
        if code.startswith("premium_"):
            period = code.split("_")[1]
            label = {"3m":"۳ ماهه","6m":"۶ ماهه","12m":"۱۲ ماهه"}.get(period, period)
            return f"تلگرام پرمیوم ({label})"
        if code == "ready_pre": return "اکانت تلگرام آماده (از پیش ساخته‌شده)"
        if code == "ready_country": return "اکانت تلگرام آماده (کشور دلخواه)"
    return "سفارش"

def _kb_checkout(oid: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="💳 پرداخت کارت", callback_data=f"cart:paycard:{oid}"),
            InlineKeyboardButton(text="👛 کیف پول", callback_data=f"cart:paywallet:{oid}"),
        ],
        [
            InlineKeyboardButton(text="🔀 پرداخت ترکیبی", callback_data=f"cart:paymix:{oid}"),
            InlineKeyboardButton(text="✨ طرح خرید اول", callback_data=f"cart:payplan:{oid}"),
        ],
        [InlineKeyboardButton(text="❌ لغو سفارش", callback_data=f"cart:cancel:{oid}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def send_checkout_prompt(msg: Message, order_id: int):
    o = get_order(order_id)
    if not o:
        await msg.answer("سفارش پیدا نشد.")
        return
    title = _order_title(o.get("service_category",""), o.get("service_code",""))
    amount = int(o.get("amount_total") or 0)
    status = _status_fa(o.get("status") or "")
    text = (
        f"📦 <b>{title}</b>\n"
        f"شماره سفارش: <code>#{o['id']}</code>\n"
        f"مبلغ: <b>{amount} {CURRENCY}</b>\n"
        f"وضعیت: <b>{status}</b>\n\n"
        f"برای ادامه، روش پرداخت را انتخاب کنید:"
    )
    await msg.answer(text, reply_markup=_kb_checkout(o["id"]))
