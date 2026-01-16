import aiosqlite

DB_NAME = 'botstars.db'

async def init_db():
    """Инициализация базы данных и создание таблиц"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей (добавили referrer_id)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                referrer_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заявок на вывод
        await db.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card_number TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def add_user(user_id: int, username: str, referrer_id: int = None):
    """Добавляет пользователя. Если есть реферер, записывает его."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, есть ли пользователь
        cursor = await db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        user = await cursor.fetchone()
        
        if not user:
            # Если пользователя нет, регистрируем
            await db.execute(
                'INSERT INTO users (user_id, username, balance, referrer_id) VALUES (?, ?, ?, ?)',
                (user_id, username, 0, referrer_id)
            )
            await db.commit()
            return True # Новый пользователь
        return False # Уже был

async def get_user_data(user_id: int):
    """Получить все данные о пользователе"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def get_balance(user_id: int) -> int:
    """Получить баланс"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def add_balance(user_id: int, amount: int):
    """Пополнить баланс"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'UPDATE users SET balance = balance + ? WHERE user_id = ?',
            (amount, user_id)
        )
        await db.commit()

async def get_referrer(user_id: int):
    """Получить ID того, кто пригласил юзера"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def count_referrals(user_id: int) -> int:
    """Посчитать количество рефералов"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def create_withdrawal(user_id: int, card_number: str, amount: int):
    """Создать заявку на вывод и списать баланс"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
        await db.execute(
            'INSERT INTO withdrawals (user_id, card_number, amount) VALUES (?, ?, ?)',
            (user_id, card_number, amount)
        )
        await db.commit()

# --- НОВЫЕ ФУНКЦИИ ДЛЯ АДМИНА ---

async def get_user_id_by_username(username: str):
    """Получить ID пользователя по username (без учета регистра)"""
    username = username.lstrip('@') # Убираем @ если есть
    async with aiosqlite.connect(DB_NAME) as db:
        # Используем LOWER для поиска без учета регистра
        async with db.execute('SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)', (username,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_all_users_data():
    """Получить список всех пользователей"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT user_id, username, balance FROM users ORDER BY balance DESC') as cursor:
            return await cursor.fetchall()