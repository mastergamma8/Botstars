from aiogram import Router, F, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, PreCheckoutQuery

import database as db
import keyboards as kb
from states import PaymentState

router = Router()

# --- КОНФИГУРАЦИЯ ---
STAR_RATE = 1.18  # Курс: 1 звезда = 1.18 рубля
REFERRAL_BONUS_PERCENT = 10  # Процент отчислений рефереру

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def rub_format(stars: int) -> str:
    """Конвертирует звезды в рубли и форматирует строку"""
    rub = stars * STAR_RATE
    return f"{rub:.2f}₽"

# --- СТАРТ И ГЛАВНОЕ МЕНЮ ---

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    referrer_id = None
    args = command.args
    
    # Проверка реферальной ссылки
    if args and args.isdigit():
        referrer_id = int(args)
        if referrer_id == message.from_user.id:
            referrer_id = None 

    is_new = await db.add_user(message.from_user.id, message.from_user.username, referrer_id)
    
    welcome_text = (
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        "Я — ваш надежный помощник для <b>вывода Telegram Stars в рубли</b> на карту.\n\n"
        "С моей помощью вы можете быстро и безопасно обменять ваши звезды "
        "на реальные деньги и перевести их на свою банковскую карту.\n\n"
        f"💎 <b>Актуальный курс обмена:</b>\n"
        f"1 ⭐️ = <b>{STAR_RATE}₽</b>\n\n"
        "💳 <i>Вывод доступен на карты всех популярных банков РФ.</i>\n\n"
        "👇 Выберите нужное действие в меню:"
    )
    
    if is_new and referrer_id:
        try:
            # Уведомление рефереру (если бот не заблокирован)
            pass 
        except:
            pass

    await message.answer(welcome_text, reply_markup=kb.main_menu(), parse_mode="HTML")

@router.message(F.text == "⬅️ Назад")
async def cmd_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 <b>Главное меню</b>", reply_markup=kb.main_menu(), parse_mode="HTML")

# --- ПРОФИЛЬ ---

@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    balance = await db.get_balance(message.from_user.id)
    rub_equivalent = rub_format(balance)
    
    await message.answer(
        f"👤 <b>Ваш Личный кабинет</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"👤 Имя: <b>{message.from_user.full_name}</b>\n\n"
        f"💰 <b>Баланс:</b>\n"
        f"• {balance} ⭐️\n"
        f"• ≈ {rub_equivalent}\n"
        f"➖➖➖➖➖➖➖➖➖➖",
        parse_mode="HTML"
    )

# --- РЕФЕРАЛЬНАЯ СИСТЕМА ---

@router.message(F.text == "👥 Рефералы")
async def cmd_referrals(message: types.Message):
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    count = await db.count_referrals(message.from_user.id)
    
    text = (
        f"👥 <b>Партнерская программа</b>\n\n"
        f"Приглашайте друзей и зарабатывайте реальные деньги!\n"
        f"Вы будете получать <b>{REFERRAL_BONUS_PERCENT}%</b> от каждого пополнения баланса вашими рефералами.\n\n"
        f"🔗 <b>Ваша ссылка для приглашений:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"Приглашено людей: <b>{count}</b>"
    )
    
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

# --- ПОПОЛНЕНИЕ ---

@router.message(F.text == "⭐️ Пополнить звездами")
async def cmd_topup(message: types.Message, state: FSMContext):
    await message.answer(
        "📥 <b>Пополнение баланса</b>\n\n"
        "Введите количество звезд, которое хотите приобрести:", 
        reply_markup=kb.cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(PaymentState.waiting_for_topup_amount)

@router.message(PaymentState.waiting_for_topup_amount)
async def process_topup_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите целое число.")
        return
    amount = int(message.text)
    if amount <= 0:
        await message.answer("⚠️ Сумма должна быть больше 0.")
        return

    prices = [LabeledPrice(label=f"Покупка {amount} зв.", amount=amount)] # amount в XTR
    
    await message.answer_invoice(
        title="Покупка Telegram Stars",
        description=f"Пополнение баланса на {amount} ⭐️",
        prices=prices,
        provider_token="", # Для Stars токен не нужен
        payload=f"pay_{amount}",
        currency="XTR",
        reply_markup=kb.pay_button(amount)
    )

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def success_payment(message: types.Message):
    amount = message.successful_payment.total_amount
    user_id = message.from_user.id
    
    # 1. Зачисляем баланс
    await db.add_balance(user_id, amount)
    
    # 2. Начисляем бонус рефереру (10%)
    referrer_id = await db.get_referrer(user_id)
    if referrer_id:
        bonus = int(amount * (REFERRAL_BONUS_PERCENT / 100))
        if bonus > 0:
            await db.add_balance(referrer_id, bonus)
            try:
                await message.bot.send_message(
                    referrer_id, 
                    f"🎉 <b>Реферальный бонус!</b>\n"
                    f"Ваш реферал пополнил баланс.\n"
                    f"Вам начислено: <b>+{bonus} ⭐️</b>",
                    parse_mode="HTML"
                )
            except:
                pass

    await message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"На ваш баланс зачислено: <b>{amount} ⭐️</b>\n"
        "Теперь вы можете вывести их в рубли.",
        parse_mode="HTML",
        reply_markup=kb.main_menu()
    )

# --- ВЫВОД СРЕДСТВ ---

@router.message(F.text == "💸 Вывести в рубли")
async def cmd_withdraw(message: types.Message, state: FSMContext):
    balance = await db.get_balance(message.from_user.id)
    if balance <= 0:
        await message.answer("⚠️ У вас нулевой баланс. Пополните счет или пригласите друзей.", reply_markup=kb.main_menu())
        return

    rub_avail = rub_format(balance)
    await message.answer(
        f"📤 <b>Вывод средств</b>\n\n"
        f"Ваш баланс: <b>{balance} ⭐️</b> (≈ {rub_avail})\n"
        f"Курс конвертации: 1 ⭐️ = {STAR_RATE}₽\n\n"
        "Введите количество звезд для вывода:",
        parse_mode="HTML",
        reply_markup=kb.cancel_keyboard()
    )
    await state.set_state(PaymentState.waiting_for_withdraw_amount)

@router.message(PaymentState.waiting_for_withdraw_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Введите целое число.")
        return
    
    request_amount = int(message.text)
    balance = await db.get_balance(message.from_user.id)

    if request_amount <= 0:
        await message.answer("⚠️ Сумма должна быть больше 0.")
        return
    if request_amount > balance:
        await message.answer(f"⚠️ Недостаточно средств. Ваш баланс: {balance} ⭐️")
        return

    # Расчет суммы к получению
    to_receive = rub_format(request_amount)
    
    await state.update_data(withdraw_amount=request_amount, to_receive_str=to_receive)
    
    await message.answer(
        f"Вы указали: <b>{request_amount} ⭐️</b>\n"
        f"Вы получите на карту: <b>{to_receive}</b>\n\n"
        "💳 Введите номер карты (без пробелов) для получения выплаты:",
        parse_mode="HTML"
    )
    await state.set_state(PaymentState.waiting_for_withdraw_card)

@router.message(PaymentState.waiting_for_withdraw_card)
async def process_withdraw_card(message: types.Message, state: FSMContext):
    card = message.text.replace(" ", "").strip()
    # Простая проверка на цифры и длину (можно усложнить)
    if not card.isdigit() or len(card) < 16:
        await message.answer("⚠️ Некорректный номер карты. Попробуйте еще раз (минимум 16 цифр).")
        return

    data = await state.get_data()
    amount = data.get('withdraw_amount')
    to_receive_str = data.get('to_receive_str')
    
    # Создаем заявку в БД
    await db.create_withdrawal(message.from_user.id, card, amount)
    
    await message.answer(
        f"✅ <b>Заявка на вывод создана!</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💸 Сумма списания: <b>{amount} ⭐️</b>\n"
        f"💰 К получению: <b>{to_receive_str}</b>\n"
        f"💳 Карта: <code>{card}</code>\n"
        f"⏳ Статус: <b>В обработке</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
        "Ожидайте поступления средств.",
        parse_mode="HTML",
        reply_markup=kb.main_menu()
    )
    await state.clear()