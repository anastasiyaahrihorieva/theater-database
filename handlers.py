from aiogram import types
from collections import defaultdict
from datetime import datetime
from keyboards import *
from configuration import *
from callbacks import *
from data_b import *


async def cmd_start(message: types.Message):
    await message.answer(
        f'Добрый день, {message.from_user.full_name}\nЯ помогу купить билет или узнать отчетность.',
        reply_markup=get_main_menu_kb()
    )

async def user_menu(message: types.Message):
    await message.answer(
        "Выберите действие:",
        reply_markup=get_user_menu_kb()
    )

async def show_report_menu(message: types.Message):
    await message.answer(
        "Выберите тип отчета:",
        reply_markup=get_report_menu_kb()
    )

async def handle_buy_ticket_menu(message: types.Message):
    await message.answer(
        "Пожалуйста, выберите критерий: ",
        reply_markup=buy_ticket_menu()
    )

async def show_theatres(message: types.Message):
    theatres = await get_theatres()
    await message.answer(
        "Выберите театр:",
        reply_markup= theatres_kb(theatres)
    )
    
async def show_theatres_sold(message: types.Message):
    theatres = await get_theatres()
    await message.answer(
        "Пожалуйста, выберите театр для просмотра статистики проданных билетов:",
        reply_markup=await theatres_sold_kb(theatres)
    )

async def choose_spectacle(message: types.Message):
    spectacles = await get_spectacles()  
    keyboard = spectacles_choosing(spectacles)
    await message.answer(
        "Выберите спектакль:",
        reply_markup=keyboard
    )
    

async def choose_theatre(message: types.Message):
    theatre = await get_theatres()
    keyboard = choose_theatres_kb(theatre)
    await message.answer(
        "Выберите театр:",
        reply_markup=keyboard
    )    

#покупаем

user_carts = defaultdict(list)
user_purchases = defaultdict(list)
purchase_counter = 0

async def show_ticket_options(callback: types.CallbackQuery):
    _, theatre_id, spectacle_id, repertoire_id = callback.data.split("_")
    theatre_id = int(theatre_id)
    spectacle_id = int(spectacle_id)
    repertoire_id = int(repertoire_id)
    
    theatre = await get_theatre_name(theatre_id)
    spectacle = await get_spectacle_info(spectacle_id)
    repertoire = await get_repertoire_info(repertoire_id)
    categories = await get_seat_categories_info(theatre_id, repertoire_id)
    
    response = [
        f"<b>Театр:</b> {theatre}\n",
        f"<b>Спектакль:</b> {spectacle['name']}\n",
        f"<b>Дата:</b> {repertoire['date'].strftime('%d.%m.%Y')}\n\n",
        "<b>Доступные категории:</b>\n"
    ]
    
    builder = InlineKeyboardBuilder()
    for cat in categories:
        response.append(
            f"- {cat['category_name']}: {cat['free_seats']} мест, цена {cat['price']} руб.\n"
        )
        builder.button(
            text=f"{cat['category_name']} - {cat['price']} руб.",
            callback_data=f"addtocart_{repertoire_id}_{cat['id_category_theater']}_{cat['price']}"
        )
    builder.adjust(1)
    
    response.append("\nВыберите категорию:")
    
    await callback.message.answer(
        "".join(response),
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

async def add_to_cart(callback: types.CallbackQuery):
    try:
        parts = callback.data.split('_')
        if len(parts) != 4 or parts[0] != "addtocart":
            await callback.answer("Ошибка: неверный формат данных", show_alert=True)
            return

        repertoire_id = int(parts[1])
        category_id = int(parts[2])
        price = float(parts[3]) 
        async with asyncpg.create_pool(**DB_CONFIG) as pool:
            async with pool.acquire() as conn:
                data = await conn.fetchrow(
                    """SELECT s.name as spectacle_name, t.name as theatre_name,
                       r.start_date as date, sc.name_category_seat as category_name
                       FROM repertoire r
                       JOIN spectacle s ON r.id_spectacle = s.id_spectacle
                       JOIN theatre t ON r.id_theatre = t.id_theatre
                       JOIN category_theater ct ON ct.id_theatre = t.id_theatre
                       JOIN seat_category sc ON sc.id_seat_category = ct.id_seat_category
                       WHERE r.id_repertoire = $1 AND ct.id_category_theater = $2""",
                    repertoire_id, category_id
                )
        
        if not data:
            await callback.answer("Ошибка: данные о билете не найдены", show_alert=True)
            return

        if callback.from_user.id not in user_carts:
            user_carts[callback.from_user.id] = []
        
        user_carts[callback.from_user.id].append({
            'repertoire_id': repertoire_id,
            'category_id': category_id,
            'price': price, 
            'spectacle_name': data['spectacle_name'],
            'theatre_name': data['theatre_name'],
            'date': data['date'],
            'category_name': data['category_name'],
            'added_at': datetime.now()
        })
        
        await callback.answer("✅ Билет добавлен в корзину!", show_alert=True)
    
    except ValueError:
        await callback.answer("Ошибка: неверные числовые данные", show_alert=True)

async def show_cart(message: types.Message):
    user_id = message.from_user.id
    if not user_carts.get(user_id):
        await message.answer("🛒 Ваша корзина пуста")
        return
    
    items = user_carts[user_id]
    
    performances = {item['repertoire_id'] for item in items}
    discount = 0.1 if len(performances) >= 2 else 0 
    grouped_items = defaultdict(list)
    for item in items:
        key = (item['repertoire_id'], item['category_id'])
        grouped_items[key].append(item)
    
    response = ["<b>Ваша корзина:</b>\n\n"]
    total = 0
    discount_total = 0
    
    for (repertoire_id, category_id), tickets in grouped_items.items():
        ticket = tickets[0]
        quantity = len(tickets)
        item_total = ticket['price'] * quantity
        
        item_discount = discount + (0.1 if quantity >= 10 else 0) 
        item_final = item_total * (1 - item_discount)
        
        response.append(
            f"<b>{ticket['spectacle_name']}</b>\n"
            f"Театр: {ticket['theatre_name']}\n"
            f"Дата: {ticket['date'].strftime('%d.%m.%Y')}\n"
            f"Категория: {ticket['category_name']}\n"
            f"Количество: {quantity}\n"
            f"Стоимость: {item_total:.2f} руб."
        )
        
        if item_discount > 0:
            response.append(
                f"🔖 Скидка {item_discount*100:.0f}%: -{item_total*item_discount:.2f} руб.\n"
                f"💳 Итого: {item_final:.2f} руб.\n"
            )
        else:
            response.append("\n")
        
        total += item_total
        discount_total += item_final
    
    response.append(f"\n<b>Общая сумма: {total:.2f} руб.</b>")
    if discount_total < total:
        response.append(
            f"\n<b>Сумма со скидкой: {discount_total:.2f} руб.</b>\n"
            f"ℹ Вы экономите: {total - discount_total:.2f} руб."
        )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить", callback_data="process_payment")
    builder.button(text="Очистить корзину", callback_data="clear_cart")
    builder.adjust(1)
    
    await message.answer(
        "".join(response),
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

async def process_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not user_carts.get(user_id):
        await callback.answer("Корзина пуста!")
        return
    
    user_purchases[user_id].extend(user_carts[user_id])
    
    async with asyncpg.create_pool(**DB_CONFIG) as pool:
        async with pool.acquire() as conn:
            async with conn.transaction():
                purchase_id = await conn.fetchval(
                    """INSERT INTO purchase (date_purchase, sum_purchase, discount)
                    VALUES (CURRENT_DATE, 0, 0)
                    RETURNING id_purchase"""
                )
                
                for item in user_carts[user_id]:
                    ticket_id = await conn.fetchval(
                        """INSERT INTO ticket 
                        (id_repertoire, id_category_theater, price)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (id_repertoire, id_category_theater)
                        DO UPDATE SET price = EXCLUDED.price
                        RETURNING id_ticket""",
                        item['repertoire_id'], item['category_id'], item['price']
                    )
                    
                    await conn.execute(
                        """INSERT INTO position_purchase
                        (id_purchase, id_ticket, quantity, price)
                        VALUES ($1, $2, 1, $3)""",
                        purchase_id, ticket_id, item['price']
                    )
    
    user_carts[user_id] = []
    
    await callback.message.edit_text(
        "✅ Покупка успешно оформлена! Билеты доступны в разделе 'Мои покупки'",
        reply_markup=None
    )
    await callback.answer()

async def show_purchases(message: types.Message):
    user_id = message.from_user.id
    if not user_purchases.get(user_id):
        await message.answer("У вас нет покупок")
        return
    
    response = ["<b>Ваши покупки:</b>\n\n"]
    for item in user_purchases[user_id]:
        response.append(
            f"<b>{item['spectacle_name']}</b>\n"
            f"Театр: {item['theatre_name']}\n"
            f"Дата: {item['date'].strftime('%d.%m.%Y')}\n"
            f"Категория: {item['category_name']}\n"
            f"Цена: {item['price']:.2f} руб.\n"
            f"Дата покупки: {item['added_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        )
    
    await message.answer("".join(response), parse_mode="HTML")

async def return_to_main_menu_text(message: types.Message):
    await message.answer(
        "Вы в главном меню:",
        reply_markup=get_main_menu_kb(),
        parse_mode="HTML"
    )
    
#возвратики
async def process_refund(callback: types.CallbackQuery):
    try:
        if callback.data == "cancel_refund":
            await callback.message.edit_text("❌ Возврат отменен")
            return

        parts = callback.data.split('_')
        if len(parts) < 4:
            await callback.answer("Неверный формат запроса", show_alert=True)
            return

        repertoire_id = int(parts[1])
        category_id = int(parts[2])
        date_str = parts[3] 
        category_name = parts[4].replace('_', ' ') if len(parts) > 4 else ""
        formatted_date = f"{date_str[:2]}.{date_str[2:4]}.{date_str[4:]}"

        user_id = callback.from_user.id
        tickets_to_refund = [
            t for t in user_purchases[user_id]
            if (t['repertoire_id'] == repertoire_id and
                t['category_id'] == category_id and
                t['date'].strftime('%d%m%Y') == date_str)
        ]
        spectacle_name = tickets_to_refund[0]['spectacle_name']
        theatre_name = tickets_to_refund[0]['theatre_name']

        categories = defaultdict(list)
        for ticket in tickets_to_refund:
            categories[ticket['category_name']].append(ticket)

        keyboard_buttons = []
        for category, tickets in categories.items():
            total_quantity = sum(t.get('quantity', 1) for t in tickets)
            keyboard_buttons.append(
                [types.InlineKeyboardButton(
                    text=f"Вернуть {category} ({total_quantity} шт.)",
                    callback_data=f"confirm_refund_{repertoire_id}_{category_id}_{date_str}_{category.replace(' ', '_')}_{total_quantity}"
                )]
            )

        keyboard_buttons.append([types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_refund")])
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.edit_text(
            f"<b>Подтвердите возврат:</b>\n\n"
            f"<b>{spectacle_name}</b>\n"
            f"Театр: {theatre_name}\n"
            f"Дата: {formatted_date}\n\n"
            f"Выберите категорию билетов для возврата:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в process_refund: {e}")
        await callback.answer("⚠️ Ошибка при обработке возврата", show_alert=True)

async def show_refund_menu(message: types.Message):
        user_id = message.from_user.id
        if not user_purchases.get(user_id):
            await message.answer("ℹ У вас нет покупок для возврата")
            return

        grouped_tickets = defaultdict(list)
        for ticket in user_purchases[user_id]:
            key = (ticket['repertoire_id'], ticket['category_id'])
            grouped_tickets[key].append(ticket)

        response = ["<b>Выберите покупку для возврата:</b>\n\n"]
        builder = InlineKeyboardBuilder()

        for (repertoire_id, category_id), tickets in grouped_tickets.items():
            ticket = tickets[0] 
            quantity = len(tickets)
            
            date_str = ticket['date'].strftime('%d.%m.%Y')
            response.append(
                f"<b>{ticket['spectacle_name']}</b>\n"
                f"Театр: {ticket['theatre_name']}\n"
                f"Дата: {date_str}\n"
                f"Категория: {ticket['category_name']}\n"
                f"Количество: {quantity} шт.\n\n"
            )
            builder.button(
            text=f"{ticket['theatre_name'][:10]} - {ticket['spectacle_name'][:15]} ({ticket['category_name']}, {date_str[:5]})",
             callback_data=f"refund_{repertoire_id}_{category_id}_{date_str.replace('.', '')}_{ticket['category_name'].replace(' ', '_')}"
)

        builder.button(text="❌ Отмена", callback_data="cancel_refund")
        builder.adjust(1)  
        await message.answer(
            "".join(response),
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
     

async def confirm_refund(callback: types.CallbackQuery):
    try:
        if callback.data == "cancel_refund":
            await callback.message.edit_text("❌ Возврат отменен")
            return
        parts = callback.data.split('_')
        repertoire_id = int(parts[2])
        category_id = int(parts[3])
        date_str = parts[4] 
        category = parts[5].replace('_', ' ')
        quantity = int(parts[6])
        conn = await asyncpg.connect(**DB_CONFIG)
        
        try:
            purchase_date = datetime.strptime(date_str, '%d%m%Y').date()
            total_available = await conn.fetchval(
                '''
                SELECT COALESCE(SUM(pp.quantity), 0)
                FROM position_purchase pp
                JOIN ticket t ON pp.id_ticket = t.id_ticket
                JOIN repertoire r ON t.id_repertoire = r.id_repertoire
                JOIN category_theater ct ON t.id_category_theater = ct.id_category_theater
                JOIN seat_category sc ON ct.id_seat_category = sc.id_seat_category
                WHERE r.id_repertoire = $1 
                AND ct.id_category_theater = $2
                AND pp.quantity > 0
                ''',
                repertoire_id, category_id
            )

            if total_available < quantity:
                await callback.message.edit_text(
                    f"❌ Недостаточно билетов для возврата (доступно: {total_available})"
                )
                return

            purchases = await conn.fetch(
                '''
                SELECT pp.id_position_purchase, pp.id_purchase, pp.quantity, pp.price
                FROM position_purchase pp
                JOIN ticket t ON pp.id_ticket = t.id_ticket
                JOIN repertoire r ON t.id_repertoire = r.id_repertoire
                JOIN category_theater ct ON t.id_category_theater = ct.id_category_theater
                JOIN seat_category sc ON ct.id_seat_category = sc.id_seat_category
                WHERE r.id_repertoire = $1 
                AND ct.id_category_theater = $2
                AND pp.quantity > 0
                ORDER BY pp.id_position_purchase
                ''',
                repertoire_id, category_id
            )

            remaining = quantity
            refunded = 0
            refund_amount = 0.0
            for purchase in purchases:
                if remaining <= 0:
                    break
                to_refund = min(remaining, purchase['quantity'])
                await conn.execute(
                    '''
                        INSERT INTO position_purchase 
                        (id_purchase, id_ticket, quantity, price)
                        SELECT $1, id_ticket, -$2::integer, price
                        FROM position_purchase
                        WHERE id_position_purchase = $3
                        ''',
                        purchase['id_purchase'], quantity, purchase['id_position_purchase']
                )


                print(type(remaining), type(refund_amount),type(refunded))
                remaining -= to_refund
                refunded += to_refund
                refund_amount += to_refund * float(purchase['price'])
            ticket_data = await conn.fetchrow(
                '''
                SELECT s.name as spectacle_name, th.name as theatre_name
                FROM repertoire r
                JOIN spectacle s ON r.id_spectacle = s.id_spectacle
                JOIN theatre th ON r.id_theatre = th.id_theatre
                WHERE r.id_repertoire = $1
                ''',
                repertoire_id
            )

            await callback.message.edit_text(
                f"✅ Успешно оформлен возврат\n\n"
                f"<b>{ticket_data['spectacle_name']}</b>\n"
                f"Театр: {ticket_data['theatre_name']}\n"
                f"Дата: {date_str[:2]}.{date_str[2:4]}.{date_str[4:]}\n"
                f"Категория: {category}\n\n"
                f"Количество: {refunded} билет(ов)\n"
                f"Сумма возврата: {refund_amount:.2f} руб.",
                parse_mode="HTML"
            )

        except Exception as e:
            print(f"Ошибка при обработке возврата: {e}")
            await callback.message.edit_text("❌ Ошибка при обработке возврата")
        finally:
            await conn.close()

        await callback.answer()

    except Exception as e:
        print(f"Ошибка в confirm_refund: {e}")
        await callback.answer("⚠️ Ошибка при обработке возврата", show_alert=True)


async def show_finance_date(message: types.Message):
    quarters = [
        {"name": "Q1 (Январь-Март)", "dates": ("01.01", "31.03")},
        {"name": "Q2 (Апрель-Июнь)", "dates": ("01.04", "30.06")},
        {"name": "Q3 (Июль-Сентябрь)", "dates": ("01.07", "30.09")},
        {"name": "Q4 (Октябрь-Декабрь)", "dates": ("01.10", "31.12")},
        {"name": "Весь год", "dates": ("01.01", "31.12")}
    ]
    
    builder = InlineKeyboardBuilder()
    for quarter in quarters:
        builder.button(
            text=quarter["name"],
            callback_data=f"finance_{quarter['dates'][0]}_{quarter['dates'][1]}"
        )
    builder.adjust(1)
    
    await message.answer(
        "<b>Финансовый отчет</b>\n"
        "Выберите период для отчета:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )