import asyncpg
from configuration import DB_CONFIG
from datetime import datetime
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def get_spectacles():
    conn = await asyncpg.connect(**DB_CONFIG)
    spectacles = await conn.fetch('SELECT id_spectacle, name FROM spectacle ORDER BY name')
    return [dict(spect) for spect in spectacles]

async def get_theatres():
    conn = await asyncpg.connect(**DB_CONFIG)
    theatres = await conn.fetch('SELECT id_theatre, name FROM theatre ORDER BY name')
    return [dict(theatre) for theatre in theatres]


async def repertoire_db(theatre_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        query = """
            SELECT 
                r.id_repertoire,  
                s.name AS spectacle_name,
                s.genre,
                s.director,
                r.start_date,
                r.end_date
            FROM repertoire r
            JOIN spectacle s ON r.id_spectacle = s.id_spectacle
            WHERE r.id_theatre = $1
            """
        rows = await conn.fetch(query, theatre_id)
        theatre_name = await conn.fetchval("SELECT name FROM theatre WHERE id_theatre = $1", theatre_id)
        return theatre_name, [dict(row) for row in rows]  # Преобразуем в список словарей
    finally:
        await conn.close()

    
async def get_theatre_name(theatre_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    return await conn.fetchval(
        "SELECT name FROM theatre WHERE id_theatre = $1", 
        theatre_id
    )
    await conn.close()
    
async def get_theatre_performances(theatre_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    performances = await conn.fetch(
            """
            SELECT 
                s.id_spectacle,
                s.name as spectacle_name,
                r.start_date,
                r.end_date,
                r.id_repertoire
            FROM repertoire r
            JOIN spectacle s ON r.id_spectacle = s.id_spectacle
            WHERE r.id_theatre = $1
            ORDER BY s.name, r.start_date
            """,
            theatre_id
    )
    return [dict(perf) for perf in performances]
    #await conn.close()


async def get_tickets_count_for_date(repertoire_id: int, date) -> int:
    conn = await asyncpg.connect(**DB_CONFIG)
    count = await conn.fetchval(
            """
           SELECT COALESCE(SUM(pp.quantity), 0)
                FROM position_purchase pp
                JOIN ticket t ON pp.id_ticket = t.id_ticket
                JOIN purchase p ON pp.id_purchase = p.id_purchase
                WHERE t.id_repertoire = $1
                AND p.date_purchase = $2
            """,
            repertoire_id, date
    )
    await conn.close()
    return count

async def get_theatres_for_spect(spectacle_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    return await conn.fetch (
            "SELECT DISTINCT t.id_theatre, t.name FROM repertoire r "
            "JOIN theatre t ON r.id_theatre = t.id_theatre "
            "WHERE r.id_spectacle = $1 ORDER BY t.name",
            spectacle_id
        )
    
    
async def get_spectacle_dates(spectacle_id: int, theatre_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        return await conn.fetch(
            "SELECT id_repertoire, start_date as date FROM repertoire "
            "WHERE id_spectacle = $1 AND id_theatre = $2 "
            "UNION "
            "SELECT id_repertoire, end_date as date FROM repertoire "
            "WHERE id_spectacle = $1 AND id_theatre = $2 "
            "ORDER BY date",
            spectacle_id, theatre_id
        )
    finally:
        await conn.close()
        
        
async def get_spectacle_dates_one(spectacle_id: int, theatre_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        return await conn.fetchrow(
            "SELECT id_repertoire, start_date, end_date FROM repertoire "
            "WHERE id_spectacle = $1 AND id_theatre = $2",
            spectacle_id, theatre_id
        )
    finally:
        await conn.close()
        
async def get_dates_for_spectacle_in_theatre(spectacle_id: int, theatre_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
    SELECT id_repertoire, start_date, end_date
    FROM repertoire
    WHERE id_spectacle = $1 AND id_theatre = $2
    """
    return await conn.fetchrow(query, spectacle_id, theatre_id)

async def get_spectacle_info(spectacle_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        return await conn.fetchrow(
            "SELECT id_spectacle, name, genre, director FROM spectacle "
            "WHERE id_spectacle = $1",
            spectacle_id
        )
    finally:
        await conn.close()
        
async def get_repertoire_info(repertoire_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        return await conn.fetchrow(
            "SELECT id_repertoire, start_date as date FROM repertoire "
            "WHERE id_repertoire = $1",
            repertoire_id
        )
    finally:
        await conn.close()
        
async def get_repertoire_info_all(repertoire_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
    SELECT r.id_repertoire, r.start_date, r.end_date,
           s.name as spectacle_name, t.name as theatre_name
    FROM repertoire r
    JOIN spectacle s ON r.id_spectacle = s.id_spectacle
    JOIN theatre t ON r.id_theatre = t.id_theatre
    WHERE r.id_repertoire = $1
    """
    result = await conn.fetchrow(query, repertoire_id)
    return dict(result) if result else None


async def get_spectacle_name(spectacle_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = "SELECT name FROM spectacle WHERE id_spectacle = $1"
    result = await conn.fetchval(query, spectacle_id)
    return result

async def calculate_empty_ratio(repertoire_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        total_sold = await conn.fetchval(
            """SELECT COALESCE(SUM(pp.quantity), 0)
               FROM position_purchase pp
               JOIN ticket t ON pp.id_ticket = t.id_ticket
               WHERE t.id_repertoire = $1
               AND pp.quantity > 0""",
            repertoire_id
        )
        
        total_refunded = await conn.fetchval(
            """SELECT COALESCE(SUM(ABS(pp.quantity)), 0)
               FROM position_purchase pp
               JOIN ticket t ON pp.id_ticket = t.id_ticket
               WHERE t.id_repertoire = $1
               AND pp.quantity < 0""",
            repertoire_id
        )
        
        if total_sold <= 0:
            return 0.0
            
        actual_refunded = min(total_refunded, total_sold)
        ratio = actual_refunded / total_sold
        
        return max(0.0, min(1.0, ratio))
        
    except Exception as e:
        print(f"Error calculating empty ratio: {e}")
        return 0.0
    finally:
        await conn.close()
     
async def get_theatres_for_spectacle(spectacle_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        return await conn.fetch(
            "SELECT DISTINCT t.id_theatre, t.name FROM repertoire r "
            "JOIN theatre t ON r.id_theatre = t.id_theatre "
            "WHERE r.id_spectacle = $1 ORDER BY t.name",
            spectacle_id
        )
    finally:
        await conn.close()

async def get_repertoire_for_spectacle_theatre(spectacle_id: int, theatre_id: int):

    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        return await conn.fetch(
            "SELECT id_repertoire, start_date FROM repertoire "
            "WHERE id_spectacle = $1 AND id_theatre = $2 "
            "AND start_date >= CURRENT_DATE "
            "ORDER BY start_date",
            spectacle_id, theatre_id
        )
    finally:
        await conn.close()
    

async def create_purchase(user_id: int, cart_items: list):
    async with asyncpg.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Создаем покупку
                purchase_id = await conn.fetchval(
                    """INSERT INTO purchase (date_purchase, sum_purchase, discount)
                       VALUES ($1, $2, $3) RETURNING id_purchase""",
                    datetime.now().date(),
                    sum(item['price'] for item in cart_items),
                    0.0
                )
                
                await conn.execute(
                    """INSERT INTO user_purchases (user_id, purchase_id)
                       VALUES ($1, $2)""",
                    user_id, purchase_id
                )

                for item in cart_items:
                    ticket_id = await conn.fetchval(
                        """SELECT id_ticket FROM ticket
                           WHERE id_repertoire = $1 AND id_category_theater = $2""",
                        item['repertoire_id'], item['category_id']
                    )
                    
                    if not ticket_id:
                        ticket_id = await conn.fetchval(
                            """INSERT INTO ticket (id_repertoire, id_category_theater, price)
                               VALUES ($1, $2, $3) RETURNING id_ticket""",
                            item['repertoire_id'], item['category_id'], item['price']
                        )
                    
                    await conn.execute(
                        """INSERT INTO position_purchase
                           (id_purchase, id_ticket, quantity, price)
                           VALUES ($1, $2, $3, $4)""",
                        purchase_id, ticket_id, 1, item['price']
                    )
                
                return purchase_id

async def get_user_purchases(user_id: int):
    async with asyncpg.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_purchases (
                    user_id INTEGER,
                    purchase_id INTEGER REFERENCES purchase(id_purchase),
                    PRIMARY KEY (user_id, purchase_id)
                )
            """)
            
            return await conn.fetch(
                """SELECT 
                    pp.id_position_purchase,
                    p.id_purchase,
                    s.name as spectacle_name,
                    t.name as theatre_name,
                    r.start_date as date,
                    sc.name_category_seat as category_name,
                    pp.price,
                    p.date_purchase
                FROM position_purchase pp
                JOIN purchase p ON pp.id_purchase = p.id_purchase
                JOIN user_purchases up ON p.id_purchase = up.purchase_id
                JOIN ticket tk ON pp.id_ticket = tk.id_ticket
                JOIN repertoire r ON tk.id_repertoire = r.id_repertoire
                JOIN spectacle s ON r.id_spectacle = s.id_spectacle
                JOIN theatre t ON r.id_theatre = t.id_theatre
                JOIN category_theater ct ON tk.id_category_theater = ct.id_category_theater
                JOIN seat_category sc ON ct.id_seat_category = sc.id_seat_category
                WHERE up.user_id = $1""",
                user_id
            )

async def refund_ticket(position_id: int):
    async with asyncpg.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            # Проверяем дату спектакля
            spectacle_date = await conn.fetchval(
                """SELECT r.start_date FROM position_purchase pp
                   JOIN ticket t ON pp.id_ticket = t.id_ticket
                   JOIN repertoire r ON t.id_repertoire = r.id_repertoire
                   WHERE pp.id_position_purchase = $1""",
                position_id
            )
            
            if spectacle_date < datetime.now().date():
                return False
                
            deleted = await conn.execute(
                "DELETE FROM position_purchase WHERE id_position_purchase = $1",
                position_id
            )
            return deleted.endswith("1")

#
async def show_purchases_ret(message: types.Message):
    purchases = await get_user_purchases(message.from_user.id)
    
    if not purchases:
        await message.answer("У вас нет покупок")
        return
    
    builder = InlineKeyboardBuilder()
    response = ["<b>Ваши покупки:</b>\n\n"]
    
    for purchase in purchases:
        response.extend([
            f"<b>Покупка #{purchase['id_purchase']}</b>\n",
            f"Спектакль: {purchase['spectacle_name']}\n",
            f"Театр: {purchase['theatre_name']}\n",
            f"Дата: {purchase['date'].strftime('%d.%m.%Y')}\n",
            f"Категория: {purchase['category_name']}\n",
            f"Цена: {purchase['price']:.2f} руб.\n\n"
        ])
        
        builder.button(
            text=f"Вернуть {purchase['spectacle_name']}",
            callback_data=f"refund_{purchase['id_position_purchase']}"
        )
    
    await message.answer("".join(response), parse_mode="HTML")
    await message.answer(
        "Выберите билет для возврата:",
        reply_markup=builder.as_markup()
    )


async def process_refund(callback: types.CallbackQuery):
    position_id = int(callback.data.split("_")[1])
    
    success = await refund_ticket(position_id)
    if success:
        await callback.answer("✅ Билет успешно возвращен!", show_alert=True)
        await show_purchases_ret(callback.message)
    else:
        await callback.answer("⚠️ Нельзя вернуть билет на прошедший спектакль", show_alert=True)
        
async def get_spectacles_for_theatre(theatre_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    return await conn.fetch(
                """SELECT DISTINCT s.id_spectacle, s.name
                   FROM repertoire r
                   JOIN spectacle s ON r.id_spectacle = s.id_spectacle
                   WHERE r.id_theatre = $1
                   ORDER BY s.name""",
                theatre_id
            )

async def get_seat_categories_info(theatre_id: int, repertoire_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    return await conn.fetch(
                """SELECT 
                      ct.id_category_theater,
                      sc.name_category_seat as category_name,
                      ct.seats_amount,
                      t.price,
                      ct.seats_amount - COALESCE((
                          SELECT SUM(pp.quantity)
                          FROM position_purchase pp
                          WHERE pp.id_ticket = t.id_ticket
                      ), 0) as free_seats
                   FROM category_theater ct
                   JOIN seat_category sc ON ct.id_seat_category = sc.id_seat_category
                   LEFT JOIN ticket t ON t.id_category_theater = ct.id_category_theater
                      AND t.id_repertoire = $2
                   WHERE ct.id_theatre = $1""",
                theatre_id, repertoire_id
            )
            
async def get_spectacle_by_name(spectacle_name: str, theatre_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
    SELECT s.id_spectacle, s.name, s.genre, s.director
    FROM spectacle s
    JOIN repertoire r ON s.id_spectacle = r.id_spectacle
    WHERE s.name = $1 AND r.id_theatre = $2
    LIMIT 1
    """
    result = await conn.fetchrow(query, spectacle_name, theatre_id)
    
    return dict(result) if result else None


async def get_theatre_by_name(theatre_name: str):
    conn = await asyncpg.connect(**DB_CONFIG)
    query = "SELECT id_theatre, name FROM theatre WHERE name = $1 LIMIT 1"
    result = await conn.fetchrow(query, theatre_name)
    return dict(result) if result else None

async def get_repertoire_by_date(theatre_id: int, spectacle_id: int, date_str: str):
    try:
        date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        return None
    conn = await asyncpg.connect(**DB_CONFIG)
    query = """
    SELECT id_repertoire, id_spectacle, id_theatre, start_date, end_date 
    FROM repertoire 
    WHERE id_theatre = $1 AND id_spectacle = $2 
    AND $3 BETWEEN start_date AND end_date
    LIMIT 1
    """
    result = await conn.fetchrow(query, theatre_id, spectacle_id, date_obj)
    return dict(result) if result else None