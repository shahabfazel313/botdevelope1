from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .config import CURRENCY, PLANS

# ====== Reply Keyboards ======
REPLY_BTN_PRODUCTS = "🛍️ محصولات و خدمات"
REPLY_BTN_CART = "🧺 سبد خرید"
REPLY_BTN_PROFILE = "👤 اطلاعات کاربری"
REPLY_BTN_SUPPORT = "🛟 پشتیبانی"


def reply_main() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=REPLY_BTN_PRODUCTS), KeyboardButton(text=REPLY_BTN_CART)],
            [KeyboardButton(text=REPLY_BTN_PROFILE), KeyboardButton(text=REPLY_BTN_SUPPORT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="یک گزینه را انتخاب کنید…",
    )


def reply_request_contact() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 اشتراک‌گذاری شماره من", request_contact=True)],
            [KeyboardButton(text="انصراف")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="برای ادامه، دکمه را بزنید",
    )


def ik_force_join(join_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if join_url:
        builder.button(text="عضویت در کانال", url=join_url)
    builder.button(text="بررسی عضویت", callback_data="forcejoin:check")
    builder.adjust(1)
    return builder.as_markup()


# ====== Legacy Inline Keyboards (برای بخش‌هایی که هنوز بازطراحی نشده‌اند) ======

def kb_home() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 خرید اکانت", callback_data="buy")
    builder.button(text="👤 حساب کاربری", callback_data="account")
    builder.button(text="ℹ️ راهنما", callback_data="help")
    builder.adjust(1)
    return builder.as_markup()


def kb_plans() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in PLANS:
        builder.button(
            text=f"{plan['title']} — {plan['price']} {CURRENCY}",
            callback_data=f"plan:{plan['id']}",
        )
    builder.button(text="🔙 بازگشت", callback_data="home")
    builder.adjust(1)
    return builder.as_markup()


def kb_admin_actions(order_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data=f"admin:approve:{order_id}"),
            InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"admin:reject:{order_id}"),
        ],
        [InlineKeyboardButton(text="📦 تحویل شد", callback_data=f"admin:delivered:{order_id}")],
        [InlineKeyboardButton(text="✉️ پیام به مشتری", callback_data=f"admin:msg:{order_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_account() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 بروزرسانی", callback_data="account_refresh")
    builder.button(text="✉️ پشتیبانی", callback_data="support")
    builder.button(text="🔙 بازگشت", callback_data="home")
    builder.adjust(2, 1)
    return builder.as_markup()


# ====== Shop Navigation ======

def ik_shop_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📣 خدمات تلگرام", callback_data="shop:tg")
    builder.button(text="🤖 هوش مصنوعی", callback_data="shop:ai")
    builder.button(text="🧩 ساخت بات تلگرام برای شما", callback_data="shop:buildbot")
    builder.button(text="🧰 خدمات دیگر", callback_data="shop:other")
    builder.adjust(1)
    return builder.as_markup()


def ik_ai_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="اکانت ChatGPT Team", callback_data="ai:team")
    builder.button(text="اکانت ChatGPT Plus", callback_data="ai:plus")
    builder.button(text="اکانت Google AI Pro", callback_data="ai:google")
    builder.button(text="🔙 بازگشت", callback_data="shop:main")
    builder.adjust(1)
    return builder.as_markup()


def ik_ai_buy_modes(plan_code: str, modes: list[dict[str, str]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for mode in modes:
        rows.append([
            InlineKeyboardButton(text=mode["text"], callback_data=mode["callback"])
        ])
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"ai:{plan_code}:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_ai_confirm_purchase(plan_code: str, mode: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 خرید", callback_data=f"ai:{plan_code}:mode:{mode}:buy")
    builder.button(text="🔙 بازگشت", callback_data=f"ai:{plan_code}:mode:{mode}:back")
    builder.adjust(2)
    return builder.as_markup()


def ik_tg_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="تلگرام پرمیوم", callback_data="tg:premium")
    builder.button(text="استارز", callback_data="tg:stars")
    builder.button(text="اکانت تلگرام آماده", callback_data="tg:ready")
    builder.button(text="🔙 بازگشت", callback_data="shop:main")
    builder.adjust(1)
    return builder.as_markup()


def ik_tg_premium_durations() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="3 ماهه", callback_data="tg:premium:3m")
    builder.button(text="6 ماهه", callback_data="tg:premium:6m")
    builder.button(text="12 ماهه", callback_data="tg:premium:12m")
    builder.button(text="🔙 بازگشت", callback_data="tg:back")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def ik_tg_ready_options() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="اکانت از پیش ساخته‌شده", callback_data="tg:ready:pre")
    builder.button(text="اکانت با کشور مورد نظر شما", callback_data="tg:ready:country")
    builder.button(text="🔙 بازگشت", callback_data="tg:back")
    builder.adjust(1)
    return builder.as_markup()


def ik_ready_pre_actions() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🛒 خرید", callback_data="tg:ready:pre:buy")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="tg:ready")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_build_actions() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📝 ثبت درخواست", callback_data="build:request")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="shop:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_other_services_actions() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📝 درخواست محصول/خدمت", callback_data="other:request")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="shop:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ====== Cart / Checkout ======

def ik_cart_actions(order_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="💳 پرداخت کارت‌به‌کارت", callback_data=f"cart:paycard:{order_id}")],
        [InlineKeyboardButton(text="👛 پرداخت با کیف پول", callback_data=f"cart:paywallet:{order_id}")],
        [
            InlineKeyboardButton(text="🔄 پرداخت ترکیبی", callback_data=f"cart:paymix:{order_id}"),
            InlineKeyboardButton(text="✨ طرح خرید اول", callback_data=f"cart:payplan:{order_id}"),
        ],
        [InlineKeyboardButton(text="❌ لغو سفارش", callback_data=f"cart:cancel:{order_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_card_receipt_prompt(order_id: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="❌ لغو", callback_data=f"cart:cancel:{order_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_receipt_review(order_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✅ ثبت سفارش", callback_data=f"cart:rcpt:confirm:{order_id}")],
        [InlineKeyboardButton(text="✏️ ویرایش پیام", callback_data=f"cart:rcpt:edit:{order_id}")],
        [InlineKeyboardButton(text="❌ لغو سفارش", callback_data=f"cart:cancel:{order_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_wallet_confirm(order_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✅ تایید پرداخت", callback_data=f"cart:wallet:confirm:{order_id}")],
        [InlineKeyboardButton(text="❌ لغو سفارش", callback_data=f"cart:cancel:{order_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_plan_review(order_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✅ ارسال برای تایید", callback_data=f"cart:plan:confirm:{order_id}")],
        [InlineKeyboardButton(text="✏️ ویرایش توضیح", callback_data=f"cart:plan:edit:{order_id}")],
        [InlineKeyboardButton(text="❌ لغو سفارش", callback_data=f"cart:cancel:{order_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ====== Profile / History ======

def ik_profile_actions() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="🧾 تاریخچه سفارشات", callback_data="hist:menu")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_history_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🟡 سفارشات در حال انجام", callback_data="hist:show:inprog:p1")],
        [InlineKeyboardButton(text="✅ سفارشات تکمیل‌شده", callback_data="hist:show:done:p1")],
        [InlineKeyboardButton(text="📚 تمام سفارشات", callback_data="hist:show:all:p1")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="hist:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ik_history_more(cat: str, next_page: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="⬇️ نمایش بیشتر", callback_data=f"hist:show:{cat}:p{next_page}")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="hist:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


__all__ = [
    "REPLY_BTN_PRODUCTS",
    "REPLY_BTN_CART",
    "REPLY_BTN_PROFILE",
    "REPLY_BTN_SUPPORT",
    "reply_main",
    "reply_request_contact",
    "ik_force_join",
    "kb_home",
    "kb_plans",
    "kb_admin_actions",
    "kb_account",
    "ik_shop_main",
    "ik_ai_main",
    "ik_ai_buy_modes",
    "ik_ai_confirm_purchase",
    "ik_tg_main",
    "ik_tg_premium_durations",
    "ik_tg_ready_options",
    "ik_ready_pre_actions",
    "ik_build_actions",
    "ik_other_services_actions",
    "ik_cart_actions",
    "ik_card_receipt_prompt",
    "ik_receipt_review",
    "ik_wallet_confirm",
    "ik_profile_actions",
    "ik_history_menu",
    "ik_history_more",
]
