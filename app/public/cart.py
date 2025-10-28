from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from . import router
from .helpers import _notify_admins, _order_title
from ..config import ADMIN_IDS, CARD_NAME, CARD_NUMBER, CURRENCY
from ..db import (
    change_wallet,
    get_order,
    get_user,
    is_user_contact_verified,
    set_order_customer_message,
    set_order_payment_type,
    set_order_receipt,
    set_order_status,
    set_order_wallet_reserved,
    set_order_wallet_used,
    user_has_delivered_order,
)
from ..keyboards import (
    ik_card_receipt_prompt,
    ik_plan_review,
    ik_receipt_review,
    ik_wallet_confirm,
    reply_main,
    reply_request_contact,
)
from ..states import CheckoutStates, VerifyStates
from ..utils import mention


async def _require_contact_verification(callback: CallbackQuery, state: FSMContext) -> bool:
    if is_user_contact_verified(callback.from_user.id):
        return True
    await state.set_state(VerifyStates.wait_contact)
    await callback.message.answer(
        "جهت استفاده از ربات نیاز به احراز هویت می‌باشد. لطفاً با استفاده از دکمهٔ زیر شماره خود را به اشتراک بگذارید.",
        reply_markup=reply_request_contact(),
    )
    await callback.answer()
    return False


@router.callback_query(F.data.startswith("cart:paycard:"))
async def cb_cart_paycard(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_contact_verification(callback, state):
        return
    order_id = int(callback.data.split(":")[2])
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id or order["status"] != "AWAITING_PAYMENT":
        await callback.answer("سفارش نامعتبر یا منقضی است.", show_alert=True)
        return
    set_order_payment_type(order_id, "CARD")
    await state.update_data(
        order_receipt_for=order_id,
        receipt_file_id=None,
        receipt_text=None,
        receipt_comment="",
        receipt_kind="",
    )
    await callback.message.answer(
        f"💳 پرداخت کارت‌به‌کارت برای سفارش #{order_id}\n"
        f"• شماره کارت: <code>{CARD_NUMBER}</code>\n"
        f"• به نام: {CARD_NAME}\n\n"
        "پس از پرداخت، تصویر یا فایل رسید را ارسال کنید. برای لغو می‌توانید از دکمه زیر استفاده کنید.",
        reply_markup=ik_card_receipt_prompt(order_id),
    )
    await callback.message.answer(f"🧾 رسید کارت سفارش #{order_id} را ارسال کنید.")
    await state.set_state(CheckoutStates.wait_card_receipt)
    await callback.answer()


@router.message(CheckoutStates.wait_card_receipt)
async def on_card_receipt(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_receipt_for")
    order = get_order(int(order_id)) if order_id else None
    if not order or order["user_id"] != message.from_user.id:
        await message.answer("سفارش یافت نشد یا معتبر نیست.", reply_markup=reply_main())
        await state.clear()
        return

    file_id = None
    text = None
    receipt_kind = ""
    caption_seed = ""
    if message.photo:
        file_id = message.photo[-1].file_id
        receipt_kind = "photo"
        caption_seed = (message.caption or "").strip()
    elif message.document:
        file_id = message.document.file_id
        receipt_kind = "document"
        caption_seed = (message.caption or "").strip()
    elif message.text:
        text = (message.text or "").strip()
    else:
        await message.answer("فرمت رسید نامعتبر است. لطفاً عکس، فایل یا متن ارسال کنید.")
        return

    await state.update_data(
        receipt_file_id=file_id,
        receipt_text=text,
        receipt_comment=caption_seed,
        receipt_kind=receipt_kind,
    )
    await message.answer(
        "اگر توضیحاتی برای سفارش خود دارید بنویسید. در صورت نداشتن توضیح عبارت «بدون توضیح» را ارسال کنید."
    )
    if caption_seed:
        await message.answer("✏️ توضیح همراه رسید ذخیره شد. برای تغییر، متن جدید ارسال کنید یا «بدون توضیح» بنویسید.")
    await state.set_state(CheckoutStates.wait_card_comment)


@router.message(CheckoutStates.wait_card_comment)
async def on_card_comment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_receipt_for")
    order = get_order(int(order_id)) if order_id else None
    if not order or order["user_id"] != message.from_user.id:
        await message.answer("سفارش یافت نشد یا معتبر نیست.", reply_markup=reply_main())
        await state.clear()
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("لطفاً توضیح را به‌صورت متن ارسال کنید یا عبارت «بدون توضیح» را وارد کنید.")
        return
    lowered = text.lower()
    if lowered in {"بدون توضیح", "بدون توضیحات", "ندارم", "-", "تمام"}:
        comment = ""
    else:
        comment = text
    await state.update_data(receipt_comment=comment)
    preview_lines = [
        f"🧾 پیش‌نمایش ثبت رسید سفارش #{order_id}",
        "رسید شما آماده ثبت است.",
    ]
    if comment:
        preview_lines.append("📝 توضیحات شما:\n" + comment)
    else:
        preview_lines.append("📝 توضیحات شما: —")
    preview_lines.append("برای ادامه یکی از گزینه‌های زیر را انتخاب کنید.")
    await message.answer("\n\n".join(preview_lines), reply_markup=ik_receipt_review(int(order_id)))
    await state.set_state(CheckoutStates.wait_card_confirm)


@router.callback_query(F.data.startswith("cart:rcpt:edit:"))
async def cb_receipt_edit(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[3])
    data = await state.get_data()
    current = data.get("order_receipt_for")
    if not current or int(current) != order_id:
        await callback.answer("برای ویرایش ابتدا رسید را دوباره ارسال کنید.", show_alert=True)
        return
    await state.set_state(CheckoutStates.wait_card_comment)
    await callback.message.answer("توضیح جدید خود را ارسال کنید. برای حذف توضیح عبارت «بدون توضیح» را بنویسید.")
    await callback.answer()


@router.callback_query(F.data.startswith("cart:rcpt:confirm:"))
async def cb_receipt_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[3])
    data = await state.get_data()
    current = data.get("order_receipt_for")
    if not current or int(current) != order_id:
        await callback.answer("رسید برای این سفارش پیدا نشد.", show_alert=True)
        return
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id:
        await callback.answer("سفارش یافت نشد یا منقضی شده است.", show_alert=True)
        await state.clear()
        return

    receipt_file_id = data.get("receipt_file_id")
    receipt_text = data.get("receipt_text")
    receipt_comment = data.get("receipt_comment") or ""
    receipt_kind = data.get("receipt_kind")

    set_order_receipt(order_id, receipt_file_id, receipt_text)
    set_order_customer_message(order_id, receipt_comment)
    set_order_status(order_id, "PENDING_CONFIRM")

    await callback.message.answer(
        f"✅ رسید سفارش #{order_id} ثبت شد.\nوضعیت: «در انتظار تایید پرداخت»",
        reply_markup=reply_main(),
    )
    await callback.answer()
    await state.clear()

    admin_caption = (
        f"🧾 رسید جدید برای سفارش #{order_id}\n"
        f"مشتری: {mention(callback.from_user)} (@{callback.from_user.username or '—'})\n"
        f"وضعیت: در انتظار تایید پرداخت"
    )
    if receipt_comment:
        admin_caption += f"\n\n📝 توضیح مشتری:\n{receipt_comment}"

    for admin_id in ADMIN_IDS:
        try:
            if receipt_file_id and receipt_kind == "photo":
                await callback.bot.send_photo(admin_id, receipt_file_id, caption=admin_caption)
            elif receipt_file_id and receipt_kind == "document":
                await callback.bot.send_document(admin_id, receipt_file_id, caption=admin_caption)
            else:
                text_body = admin_caption
                if receipt_text:
                    text_body += f"\n\nمتن رسید:\n{receipt_text}"
                await callback.bot.send_message(admin_id, text_body)
        except Exception:
            pass


@router.callback_query(F.data.startswith("cart:paywallet:"))
async def cb_cart_paywallet(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_contact_verification(callback, state):
        return
    order_id = int(callback.data.split(":")[2])
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id or order["status"] != "AWAITING_PAYMENT":
        await callback.answer("سفارش نامعتبر یا منقضی است.", show_alert=True)
        return
    user = get_user(callback.from_user.id)
    amount = int(order["amount_total"] or 0)
    if int(user["wallet_balance"]) < amount:
        await callback.answer("موجودی کیف پول کافی نیست.", show_alert=True)
        return
    await state.update_data(
        wallet_for=order_id,
        wallet_amount=amount,
        wallet_comment="",
    )
    await state.set_state(CheckoutStates.wait_wallet_comment)
    await callback.message.answer(
        f"👛 پرداخت با کیف پول برای سفارش #{order_id}\n"
        "اگر توضیحاتی برای سفارش خود دارید بنویسید. پس از پایان روی «تایید پرداخت» بزنید.",
        reply_markup=ik_wallet_confirm(order_id),
    )
    await callback.answer()


@router.message(CheckoutStates.wait_wallet_comment)
async def on_wallet_comment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("wallet_for")
    order = get_order(int(order_id)) if order_id else None
    if not order or order["user_id"] != message.from_user.id:
        await message.answer("سفارش معتبر نیست یا منقضی شده است.", reply_markup=reply_main())
        await state.clear()
        return
    if not message.text:
        await message.answer("لطفاً توضیحات خود را به‌صورت متن ارسال کنید یا برای ادامه دکمه «تایید پرداخت» را بزنید.")
        return
    text = (message.text or "").strip()
    if text.lower() in {"بدون توضیح", "بدون توضیحات", "ندارم", "-", "تمام"}:
        comment = ""
    else:
        comment = text
    await state.update_data(wallet_comment=comment)
    await message.answer("📝 توضیح شما ذخیره شد. برای نهایی کردن پرداخت روی «تایید پرداخت» بزنید.")


@router.callback_query(F.data.startswith("cart:wallet:confirm:"))
async def cb_wallet_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[3])
    data = await state.get_data()
    current = data.get("wallet_for")
    if not current or int(current) != order_id:
        await callback.answer("پرداخت کیف پول برای این سفارش فعال نیست.", show_alert=True)
        return
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id or order["status"] != "AWAITING_PAYMENT":
        await callback.answer("سفارش قابل پرداخت نیست.", show_alert=True)
        await state.clear()
        return
    amount = int(order["amount_total"] or data.get("wallet_amount") or 0)
    user = get_user(callback.from_user.id)
    if int(user["wallet_balance"]) < amount:
        await callback.answer("موجودی کیف پول کافی نیست.", show_alert=True)
        return
    if not change_wallet(callback.from_user.id, -amount, "DEBIT", note=f"Order #{order_id}", order_id=order_id):
        await callback.answer("عدم امکان کسر از کیف پول.", show_alert=True)
        return
    comment = data.get("wallet_comment") or ""
    set_order_wallet_used(order_id, amount)
    set_order_payment_type(order_id, "WALLET")
    set_order_customer_message(order_id, comment)
    set_order_status(order_id, "IN_PROGRESS")
    await callback.message.answer(
        f"✅ پرداخت کیف پول برای سفارش #{order_id} انجام شد.\nوضعیت: «در حال انجام»",
        reply_markup=reply_main(),
    )
    await callback.answer()
    await state.clear()
    notice = f"👛 پرداخت کیف پول — سفارش #{order_id} توسط {mention(callback.from_user)}"
    if comment:
        notice += f"\n\n📝 توضیح مشتری:\n{comment}"
    await _notify_admins(callback.bot, notice)


@router.callback_query(F.data.startswith("cart:payplan:"))
async def cb_cart_payplan(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_contact_verification(callback, state):
        return
    order_id = int(callback.data.split(":")[2])
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id or order["status"] != "AWAITING_PAYMENT":
        await callback.answer("سفارش نامعتبر یا منقضی است.", show_alert=True)
        return
    if user_has_delivered_order(callback.from_user.id):
        await callback.answer("شما قبلاً از این طرح استفاده کرده‌اید.", show_alert=True)
        await callback.message.answer("⚠️ شما قبلاً سفارش تحویل‌شده دارید و امکان استفاده مجدد از طرح خرید اول وجود ندارد.")
        return
    set_order_payment_type(order_id, "FIRST_PLAN")
    await state.update_data(plan_for=order_id, plan_comment="")
    await state.set_state(CheckoutStates.wait_plan_comment)
    await callback.message.answer(
        "✨ طرح خرید اول فعال شد.\n"
        "اگر توضیحاتی برای سفارش خود دارید بنویسید. در صورت نداشتن توضیح عبارت «بدون توضیح» را ارسال کنید."
    )
    await callback.answer()


@router.message(CheckoutStates.wait_plan_comment)
async def on_plan_comment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("plan_for")
    order = get_order(int(order_id)) if order_id else None
    if not order or order["user_id"] != message.from_user.id:
        await message.answer("سفارش یافت نشد یا معتبر نیست.", reply_markup=reply_main())
        await state.clear()
        return
    if not message.text:
        await message.answer("لطفاً توضیحات خود را به‌صورت متن ارسال کنید یا عبارت «بدون توضیح» را وارد کنید.")
        return
    text = (message.text or "").strip()
    if text.lower() in {"بدون توضیح", "بدون توضیحات", "ندارم", "-", "تمام"}:
        comment = ""
    else:
        comment = text
    await state.update_data(plan_comment=comment)
    preview_lines = [
        f"✨ طرح خرید اول — سفارش #{order_id}",
        "درخواست شما آماده ارسال برای تایید است.",
    ]
    if comment:
        preview_lines.append("📝 توضیحات شما:\n" + comment)
    else:
        preview_lines.append("📝 توضیحات شما: —")
    preview_lines.append("برای ادامه یکی از گزینه‌های زیر را انتخاب کنید.")
    await message.answer("\n\n".join(preview_lines), reply_markup=ik_plan_review(int(order_id)))
    await state.set_state(CheckoutStates.wait_plan_confirm)


@router.callback_query(F.data.startswith("cart:plan:edit:"))
async def cb_plan_edit(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[3])
    data = await state.get_data()
    current = data.get("plan_for")
    if not current or int(current) != order_id:
        await callback.answer("برای ویرایش ابتدا طرح را دوباره ثبت کنید.", show_alert=True)
        return
    await state.set_state(CheckoutStates.wait_plan_comment)
    await callback.message.answer("توضیح جدید خود را ارسال کنید. برای حذف توضیح عبارت «بدون توضیح» را بنویسید.")
    await callback.answer()


@router.callback_query(F.data.startswith("cart:plan:confirm:"))
async def cb_plan_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[3])
    data = await state.get_data()
    current = data.get("plan_for")
    if not current or int(current) != order_id:
        await callback.answer("طرح خرید اول برای این سفارش فعال نیست.", show_alert=True)
        return
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id or order["status"] != "AWAITING_PAYMENT":
        await callback.answer("سفارش یافت نشد یا منقضی شده است.", show_alert=True)
        await state.clear()
        return
    comment = data.get("plan_comment") or ""
    set_order_customer_message(order_id, comment)
    set_order_status(order_id, "PENDING_PLAN")
    set_order_payment_type(order_id, "FIRST_PLAN")
    await callback.message.answer(
        f"✅ درخواست طرح خرید اول برای سفارش #{order_id} ثبت شد.\nوضعیت: «در انتظار تایید طرح»",
        reply_markup=reply_main(),
    )
    await callback.answer()
    await state.clear()

    title = _order_title(order.get("service_category", ""), order.get("service_code", ""), order.get("notes"))
    notice = (
        f"✨ طرح خرید اول — سفارش #{order_id}\n"
        f"مشتری: {mention(callback.from_user)} (@{callback.from_user.username or '—'})\n"
        f"محصول: {title}"
    )
    if comment:
        notice += f"\n\n📝 توضیح مشتری:\n{comment}"
    await _notify_admins(callback.bot, notice)


@router.callback_query(F.data.startswith("cart:paymix:"))
async def cb_cart_paymix(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _require_contact_verification(callback, state):
        return
    order_id = int(callback.data.split(":")[2])
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id or order["status"] != "AWAITING_PAYMENT":
        await callback.answer("سفارش نامعتبر یا منقضی است.", show_alert=True)
        return
    await state.update_data(mixed_for=order_id)
    await state.set_state(CheckoutStates.wait_mixed_amount)
    await callback.message.answer("چه مقدار از کیف پول پرداخت شود؟ (فقط عدد به تومان)")
    await callback.answer()


@router.message(CheckoutStates.wait_mixed_amount)
async def on_mixed_amount(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("لطفاً فقط عدد (تومان) وارد کنید:")
        return
    amt_wallet = int(text)
    data = await state.get_data()
    order_id = int(data.get("mixed_for"))
    order = get_order(order_id)
    if not order or order["user_id"] != message.from_user.id or order["status"] != "AWAITING_PAYMENT":
        await message.answer("سفارش نامعتبر یا منقضی است.", reply_markup=reply_main())
        await state.clear()
        return
    total = int(order["amount_total"] or 0)
    user = get_user(message.from_user.id)
    if amt_wallet <= 0 or amt_wallet > total:
        await message.answer("مقدار نامعتبر است.")
        return
    if int(user["wallet_balance"]) < amt_wallet:
        await message.answer("موجودی کیف پول کافی نیست.")
        return
    if not change_wallet(
        message.from_user.id,
        -amt_wallet,
        "RESERVE",
        note=f"Reserve for order #{order_id}",
        order_id=order_id,
    ):
        await message.answer("امکان رزرو کیف پول نیست.")
        return
    set_order_wallet_reserved(order_id, amt_wallet)
    set_order_payment_type(order_id, "MIXED")
    await state.update_data(
        order_receipt_for=order_id,
        receipt_file_id=None,
        receipt_text=None,
        receipt_comment="",
        receipt_kind="",
    )
    await message.answer(
        f"✅ {amt_wallet} {CURRENCY} از کیف پول رزرو شد.\n"
        "باقیمانده را کارت‌به‌کارت پرداخت کنید و پس از پرداخت رسید را ارسال کنید.",
        reply_markup=ik_card_receipt_prompt(order_id),
    )
    await message.answer(f"🧾 رسید کارت سفارش #{order_id} را ارسال کنید.")
    await state.set_state(CheckoutStates.wait_card_receipt)


@router.callback_query(F.data.startswith("cart:cancel:"))
async def cb_cart_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[2])
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id or order["status"] not in ("AWAITING_PAYMENT", "PENDING_CONFIRM"):
        await callback.answer("قابل لغو نیست.", show_alert=True)
        return
    reserved = int(order.get("wallet_reserved_amount") or 0)
    if reserved > 0:
        change_wallet(callback.from_user.id, reserved, "REFUND", note=f"Cancel order #{order_id}", order_id=order_id)
        set_order_wallet_reserved(order_id, 0)
    set_order_status(order_id, "CANCELED")
    await callback.message.answer(f"❌ سفارش #{order_id} لغو شد.", reply_markup=reply_main())
    await callback.answer()
