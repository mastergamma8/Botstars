from aiogram.fsm.state import State, StatesGroup

class PaymentState(StatesGroup):
    # Состояния для пополнения
    waiting_for_topup_amount = State() 
    
    # Состояния для вывода
    waiting_for_withdraw_amount = State() # Сколько выводить
    waiting_for_withdraw_card = State()   # На какую карту


