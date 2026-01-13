from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, PreCheckoutQuery

import database as db
import keyboards as kb
from states import PaymentState

router = Router()

# --- СТАРТ И РЕФЕРАЛКА ---

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    referrer_id = None
    args = command.args
    
    # Проверяем, перешел ли по реф. ссылке
    if args and args.isdigit():
        referrer_id = int(args)
        if referrer_id == message.from_user.id:
            referrer_id = None # Нельзя пригласить самого себя

    is_new = await db.add_user(message.from_user.id, message.from_user.username, referrer_id)
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я бот для обмена Telegram Stars.\n"
    )
    
    if is_new and referrer_id:
        # Уведомляем пригласившего (опционально)
        try:
            # Примечание: Это сработает только если реферер уже писал боту
            # await message.bot.send_message(referrer_id, f"🎉 У вас новый реферал: {message.from_user.first_name}")
            pass 
        except:
            pass

    await message.answer(welcome_text, reply_markup=kb.main_menu())

@router.message(F.text == "⬅️ Назад")
async def cmd_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=kb.main_menu())

# --- ПРОФИЛЬ И РЕФЕРАЛЫ ---

@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    balance = await db.get_balance(message.from_user.id)
    await message.answer(
        f"👤 <b>Личный кабинет</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"💰 Баланс: <b>{balance} ⭐️</b>",
        parse_mode="HTML"
    )

@router.message(F.text == "👥 Рефералы")
async def cmd_referrals(message: types.Message):
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    count = await db.count_referrals(message.from_user.id)
    
    await message.answer(
        f"👥 <b>Партнерская программа</b>\n\n"
        f"Приглашайте друзей и отслеживайте статистику!\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n<code>{ref_link}</code>\n\n"
        f"📊 Приглашено людей: <b>{count}</b>",
        parse_mode="HTML"
    )

# --- ПОПОЛНЕНИЕ ---

@router.message(F.text == "⭐️ Пополнить звездами")
async def cmd_topup(message: types.Message, state: FSMContext):
    await message.answer("Введите количество звезд для пополнения:", reply_markup=kb.cancel_keyboard())
    await state.set_state(PaymentState.waiting_for_topup_amount)

@router.message(PaymentState.waiting_for_topup_amount)
async def process_topup_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите целое число.")
        return
    amount = int(message.text)
    if amount <= 0:
        await message.answer("Минимум 1 звезда.")
        return

    prices = [LabeledPrice(label="Пополнение", amount=amount)]
    await message.answer_invoice(
        title="Покупка звезд",
        description=f"Пополнение на {amount} ⭐️",
        prices=prices,
        provider_token="", # Оставить пустым для Stars
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
    
    # 1. Зачисляем баланс пользователю
    await db.add_balance(user_id, amount)
    
    # 2. (Опционально) Начисляем бонус рефереру, например 10%
    referrer_id = await db.get_referrer(user_id)
    if referrer_id:
        bonus = int(amount * 0.10) # 10%
        if bonus > 0:
            await db.add_balance(referrer_id, bonus)
            try:
                await message.bot.send_message(referrer_id, f"💰 Бонус за реферала: +{bonus} ⭐️")
            except:
                pass

    await message.answer(
        f"✅ Баланс успешно пополнен на <b>{amount} ⭐️</b>\n"
        "Вы можете вывести их через кнопку '💸 Вывести средства'.",
        parse_mode="HTML",
        reply_markup=kb.main_menu()
    )

# --- ВЫВОД СРЕДСТВ (НОВАЯ ЛОГИКА) ---

@router.message(F.text == "💸 Вывести средства")
async def cmd_withdraw(message: types.Message, state: FSMContext):
    balance = await db.get_balance(message.from_user.id)
    if balance <= 0:
        await message.answer("У вас нулевой баланс.", reply_markup=kb.main_menu())
        return

    await message.answer(
        f"Ваш баланс: <b>{balance} ⭐️</b>\n"
        "Введите количество звезд для вывода:",
        parse_mode="HTML",
        reply_markup=kb.cancel_keyboard()
    )
    await state.set_state(PaymentState.waiting_for_withdraw_amount)

@router.message(PaymentState.waiting_for_withdraw_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите целое число.")
        return
    
    request_amount = int(message.text)
    balance = await db.get_balance(message.from_user.id)

    if request_amount <= 0:
        await message.answer("Сумма должна быть больше 0.")
        return
    if request_amount > balance:
        await message.answer(f"Недостаточно средств. Ваш баланс: {balance} ⭐️")
        return

    # Сохраняем сумму, которую хочет вывести юзер
    await state.update_data(withdraw_amount=request_amount)
    
    await message.answer("Теперь введите номер карты (16 цифр):")
    await state.set_state(PaymentState.waiting_for_withdraw_card)

@router.message(PaymentState.waiting_for_withdraw_card)
async def process_withdraw_card(message: types.Message, state: FSMContext):
    card = message.text.replace(" ", "").strip()
    if not card.isdigit() or len(card) < 16:
        await message.answer("Некорректный номер карты. Попробуйте еще раз.")
        return

    data = await state.get_data()
    amount = data.get('withdraw_amount')
    
    # Создаем заявку
    await db.create_withdrawal(message.from_user.id, card, amount)
    
    await message.answer(
        f"✅ <b>Заявка создана!</b>\n\n"
        f"💸 Сумма: {amount} ⭐️\n"
        f"💳 Карта: <code>{card}</code>\n"
        f"Статус: В обработке",
        parse_mode="HTML",
        reply_markup=kb.main_menu()
    )
    await state.clear()


