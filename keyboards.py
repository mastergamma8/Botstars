from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="👥 Рефералы")],
            [KeyboardButton(text="⭐️ Пополнить звездами")],
            [KeyboardButton(text="💸 Вывести в рубли")]
        ],
        resize_keyboard=True
    )
    return keyboard

def cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def pay_button(amount: int):
    """Инлайн кнопка оплаты"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Оплатить {amount} ⭐️", pay=True)]
        ]
    )
    return keyboard