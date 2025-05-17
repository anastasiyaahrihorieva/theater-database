from aiogram import types, F
from data_b import *
from keyboards import *
from datetime import date

async def show_theatre_info(callback: types.CallbackQuery):
    theatre_id = int(callback.data.split("_")[1])
    theatre_name, repertoire = await repertoire_db(theatre_id)
    response = [f"<b>Театр: {theatre_name}</b>\n\n"]
    
    for item in repertoire:
        response.append(
            f"<b>{item['spectacle_name']}</b>\n"
            f"Жанр: {item['genre']}\n"
            f"Режиссер: {item['director']}\n"
            f"Даты: {item['start_date'].strftime('%d.%m.%Y')} , {item['end_date'].strftime('%d.%m.%Y')}\n\n"
        )
    
    await callback.message.answer(
        "".join(response),
        parse_mode="HTML"
    )
    await callback.answer()

        
async def choose_theatre_info(callback: types.CallbackQuery):
    theatre_id = int(callback.data.split("_")[1])
    theatre_name = await get_theatre_name(theatre_id)
    spectacles = await get_spectacles_for_theatre(theatre_id)
    builder = InlineKeyboardBuilder()
    for spect in spectacles:
        builder.button(
            text=spect['name'],
            callback_data=f"spectacle_{spect['id_spectacle']}_{theatre_id}"
        )
    builder.adjust(1)
    
    await callback.message.answer(
        f"<b>Театр: {theatre_name}</b>\nВыберите спектакль:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


async def choose_spectacle_date(callback: types.CallbackQuery):
    _, spectacle_id, theatre_id = callback.data.split("_")
    spectacle_id = int(spectacle_id)
    theatre_id = int(theatre_id)
    
    spectacle = await get_spectacle_info(spectacle_id)
    dates = await get_spectacle_dates(spectacle_id, theatre_id)
    
    builder = InlineKeyboardBuilder()
    for date in dates:
        builder.button(
            text=date['date'].strftime('%d.%m.%Y'),
            callback_data=f"date_{theatre_id}_{spectacle_id}_{date['id_repertoire']}"
        )
    builder.adjust(1) 
    await callback.message.answer(
        f"<b>Спектакль: {spectacle['name']}</b>\n"
        "Выберите дату:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
    
async def choose_spectacle_date2(callback: types.CallbackQuery):
        _, theatre_id, spectacle_id = callback.data.split("_")
        theatre_id = int(theatre_id)
        spectacle_id = int(spectacle_id)
        dates = await get_spectacle_dates(spectacle_id, theatre_id)
        spectacle = await get_spectacle_info(spectacle_id)
        
        builder = InlineKeyboardBuilder()
        for date in dates:
            builder.button(
                text=date['date'].strftime('%d.%m.%Y'),
                callback_data=f"date_{theatre_id}_{spectacle_id}_{date['id_repertoire']}"
            )
        builder.adjust(2) 
        await callback.message.answer(
            f"<b>Спектакль:</b> {spectacle['name']}\n"
            "Выберите дату:",
            reply_markup=builder.as_markup(), parse_mode="HTML"
        )
    
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
            callback_data=f"addtocart_{repertoire_id}_{cat['id_category_theater']}"
        )
    builder.button( text="Назад", callback_data=f"back_to_theatres_{spectacle_id}")
    builder.button( text="В главное меню", callback_data="main_menu" )
    
    await callback.message.edit_text(
        "".join(response), reply_markup=builder.as_markup(), parse_mode="HTML"
    )
    await callback.answer()

async def add_to_cart(callback: types.CallbackQuery):
    repertoire_id, category_id = callback.data.split("_")

    await callback.answer("Билет добавлен в корзину! \n Пожалуйста, перейдите в корзину для оплаты", show_alert=True)



async def handle_spectacle_choosing(callback: types.CallbackQuery):
    spectacle_id = int(callback.data.split("_")[1])
    theatres = await get_theatres_for_spect(spectacle_id)
    keyboard = theatres_for_spect_kb(theatres, spectacle_id)  
    await callback.message.answer(
        "Выберите театр, где идет этот спектакль:",
        reply_markup=keyboard
    )
    await callback.answer()
    
async def show_theatre_repertoire(callback: types.CallbackQuery):
    theatre_id = int(callback.data.split("_")[1])
    theatre_name, performances = await repertoire_db(theatre_id)  
    response = [f"<b>Репертуар театра {theatre_name}:</b>\n\n"]
    
    for perf in performances:
        response.append(
            f"<b>{perf['spectacle_name']}</b>\n"
            f"{perf['start_date'].strftime('%d.%m.%Y')} - {perf['end_date'].strftime('%d.%m.%Y')}\n"
            f"Жанр: {perf['genre']}\n"
            f"Режиссер: {perf['director']}\n\n"
        )
    
    await callback.message.answer(
        "".join(response),
        parse_mode="HTML"
    )
    await callback.answer()
    
    

async def handle_date_selection(callback: types.CallbackQuery):
    parts = callback.data.split('_')
    date_type = parts[2]
    repertoire_id = int(parts[3])
    spectacle_id = int(parts[4])
    theatre_id = int(parts[5])
    
    repertoire = await get_repertoire_info(repertoire_id)
    selected_date = repertoire['start_date'] if date_type == 'start' else repertoire['end_date']
    theatre_name = await get_theatre_name(theatre_id)
    spectacle = await get_spectacle_info(spectacle_id)
    categories = await get_seat_categories_info(theatre_id, repertoire_id)
    
    response = [
        f"<b>Вы выбрали:</b>\n\n",
        f"<b>Спектакль:</b> {spectacle['name']}\n",
        f"<b>Театр:</b> {theatre_name}\n",
        f"<b>Дата:</b> {selected_date.strftime('%d.%m.%Y')}\n\n",
        "<b>Доступные категории билетов:</b>\n\n"
    ]
    
    for cat in categories:
        response.append(
            f"<b>{cat['category_name']}</b>\n"
            f"• Свободно мест: {cat['free_seats']}\n"
            f"• Цена: {cat['price']} руб.\n\n"
        )
    
    builder = InlineKeyboardBuilder()
    for cat in categories:
        if cat['free_seats'] > 0:
            builder.button(
                text=f"{cat['category_name']} - {cat['price']} руб.",
                callback_data=f"add_to_cart_{repertoire_id}_{cat['id_category_theater']}_{date_type}"
            )
    
    builder.button(
        text="Назад к выбору театра",
        callback_data=f"back_to_theatres_{spectacle_id}"
    )
    builder.adjust(1)
    
    await callback.message.edit_text(
        "".join(response),
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
   

    
async def back_to_theatres(callback: types.CallbackQuery):
    spectacle_id = int(callback.data.split("_")[1])
    theatres = await get_theatres_for_spectacle(spectacle_id)
    keyboard = theatres_for_spect_kb(theatres, spectacle_id)
    await callback.message.edit_text(
        "Выберите театр:",
        reply_markup=keyboard
    )
    await callback.answer()

async def show_theatre_sold_info(callback: types.CallbackQuery):
    theatre_id = int(callback.data.split("_")[1])
    theatre_name = await get_theatre_name(theatre_id)
    spectacles = await get_spectacles_for_theatre(theatre_id)
    
    builder = InlineKeyboardBuilder()
    for spect in spectacles:
        builder.button(
            text=spect['name'],
            callback_data=f"spectstats_{spect['id_spectacle']}_{theatre_id}"
        )
    builder.adjust(1)
    
    await callback.message.answer(
        f"<b>Театр: {theatre_name}</b>\nВыберите спектакль для просмотра статистики:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

async def show_spectacle_stats(callback: types.CallbackQuery):
    _, spectacle_id, theatre_id = callback.data.split("_")
    spectacle_id = int(spectacle_id)
    theatre_id = int(theatre_id)
    
    spectacle = await get_spectacle_info(spectacle_id)
    dates = await get_spectacle_dates(spectacle_id, theatre_id)
    
    builder = InlineKeyboardBuilder()
    for date in dates:
        builder.button(
            text=date['date'].strftime('%d.%m.%Y'),
            callback_data=f"datestats_{theatre_id}_{spectacle_id}_{date['id_repertoire']}"
        )
    builder.adjust(1)
    
    await callback.message.answer(
        f"<b>Спектакль: {spectacle['name']}</b>\nВыберите дату для просмотра статистики:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

async def show_date_stats(callback: types.CallbackQuery):
    try:
        _, theatre_id, spectacle_id, repertoire_id = callback.data.split("_")
        theatre_id = int(theatre_id)
        spectacle_id = int(spectacle_id)
        repertoire_id = int(repertoire_id)
        
        theatre_name = await get_theatre_name(theatre_id)
        spectacle = await get_spectacle_info(spectacle_id)
        repertoire = await get_repertoire_info(repertoire_id)
        categories = await get_seat_categories_info(theatre_id, repertoire_id)
        
        async with asyncpg.create_pool(**DB_CONFIG) as pool:
            async with pool.acquire() as conn:
                stats = []
                total_sold = 0
                total_seats = 0
                
                for cat in categories:
                    sold = await conn.fetchval(
                        """SELECT COALESCE(SUM(pp.quantity), 0)
                           FROM position_purchase pp
                           JOIN ticket t ON pp.id_ticket = t.id_ticket
                           WHERE t.id_repertoire = $1 
                           AND t.id_category_theater = $2""",
                        repertoire_id, cat['id_category_theater']
                    )
                    
                    total = await conn.fetchval(
                        """SELECT seats_amount 
                           FROM category_theater
                           WHERE id_category_theater = $1""",
                        cat['id_category_theater']
                    )
                    
                    stats.append({
                        'category': cat['category_name'],
                        'sold': sold,
                        'total': total,
                        'available': total - sold
                    })
                    
                    total_sold += sold
                    total_seats += total
        
        response = [
            f"<b>Статистика продаж</b>\n\n",
            f"<b>Театр:</b> {theatre_name}\n",
            f"<b>Спектакль:</b> {spectacle['name']}\n",
            f"<b>Дата:</b> {repertoire['date'].strftime('%d.%m.%Y')}\n\n",
            "<b>По категориям:</b>\n"
        ]
        
        for stat in stats:
            response.append(
                f"▸ {stat['category']}: {stat['sold']}/{stat['total']} "
                f"(осталось {stat['available']})\n"
            )
        
        response.append(
            f"\n<b>Итого:</b> {total_sold}/{total_seats} "
            f"(свободно {total_seats - total_sold})"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(
            text="← Назад к датам",
            callback_data=f"spectstats_{spectacle_id}_{theatre_id}"
        )
        
        await callback.message.answer(
            "".join(response),
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        print(f"Ошибка в show_date_stats: {e}")
        await callback.answer("⚠️ Ошибка при получении статистики")

#коэффициенты

async def show_theatres_for_empty_coeff(message: types.Message):
        theatres = await get_theatres()
        
        builder = InlineKeyboardBuilder()
        for theatre in theatres:
            builder.button(
                text=f"{theatre['name']}",
                callback_data=f"ratio_theatre_{theatre['id_theatre']}"
            )
        
        builder.button(
            text="↩️ Главное меню",
            callback_data="main_menu"
        )
        await message.answer(
            "🎭 Выберите театр для расчета коэффициента:",
            reply_markup=builder.as_markup()
        )
        
async def handle_empty_coeff_theatre(callback: types.CallbackQuery):
    try:
        theatre_id = int(callback.data.split("_")[2])
        theatre_name = await get_theatre_name(theatre_id)
        spectacles = await get_spectacles_for_theatre(theatre_id)
        
        builder = InlineKeyboardBuilder()
        for spect in spectacles:
            builder.button(
                text=f"{spect['name']}",
                callback_data=f"ratio_spect_{spect['id_spectacle']}_{theatre_id}"
            )
        
        builder.button(
            text="↩️ Назад к театрам",
            callback_data="back_to_ratio_theatres"
        )
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"📌 Выберите спектакль в театре <b>{theatre_name}</b>:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        print(f"Error in handle_empty_coeff_theatre: {e}")
        await callback.answer("⚠️ Ошибка при загрузке спектаклей")

async def handle_theatre_choice(callback: types.CallbackQuery):
        print(f"Получены данные: {callback.data}")  
        if callback.data == "ratio_back":
            await callback.message.delete()
            return

        if not callback.data.startswith("ratio_th_"):
            await callback.answer("Неверный формат данных")
            return

        theatre_id = int(callback.data.split("_")[2])
        print(f"Пробуем получить театр ID: {theatre_id}")

        theatre = await get_theatre_name(theatre_id)
        if not theatre:
            await callback.answer("❌ Театр не найден")
            return

        spectacles = await get_spectacles_for_theatre(theatre_id)
        if not spectacles:
            await callback.answer("❌ Нет спектаклей в этом театре")
            return

        builder = InlineKeyboardBuilder()
        for spect in spectacles:
            builder.button(
                text=f"{spect['name']}",
                callback_data=f"ratio_sp_{spect['id_spectacle']}_{theatre_id}"
            )

        builder.button(text="↩️ Назад", callback_data="ratio_theatres_list")
        builder.adjust(1)

        await callback.message.edit_text(
            f"📌 Выберите спектакль в театре <b>{theatre}</b>:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

async def handle_empty_coeff_spectacle(callback: types.CallbackQuery):
    try:
        _, _, spectacle_id, theatre_id = callback.data.split("_")
        spectacle_id = int(spectacle_id)
        theatre_id = int(theatre_id)
        
        spectacle = await get_spectacle_info(spectacle_id)
        dates = await get_spectacle_dates(spectacle_id, theatre_id)
        
        builder = InlineKeyboardBuilder()
        for date in dates:
            btn_text = date['date'].strftime('%d.%m.%Y')
            
            builder.button(
                text=btn_text,
                callback_data=f"ratio_date_{theatre_id}_{spectacle_id}_{date['id_repertoire']}"
            )
        
        builder.button(
            text="↩️ Назад",
            callback_data=f"back_to_ratio_spect_{theatre_id}"
        )
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"Выберите дату для <b>{spectacle['name']}</b>:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        print(f"Error in handle_empty_coeff_spectacle: {str(e)}")
        await callback.answer("⚠️ Ошибка при загрузке дат")

async def handle_empty_coeff_date(callback: types.CallbackQuery):
    try:
        _, _, theatre_id, spectacle_id, repertoire_id = callback.data.split("_")
        theatre_id = int(theatre_id)
        spectacle_id = int(spectacle_id)
        repertoire_id = int(repertoire_id)
        
        ratio = await calculate_empty_ratio(repertoire_id)
        theatre = await get_theatre_name(theatre_id)
        spectacle = await get_spectacle_name(spectacle_id)
        repertoire = await get_repertoire_info(repertoire_id)
        
        builder = InlineKeyboardBuilder()
        builder.button(
            text="↩️ К выбору дат",
            callback_data=f"ratio_spect_{spectacle_id}_{theatre_id}"
        )
        
        await callback.message.edit_text(
            f"<b>📊 Результат</b>\n\n"
            f"Театр: {theatre}\n"
            f"Спектакль: {spectacle}\n"
            f"Дата: {repertoire['date'].strftime('%d.%m.%Y')}\n\n"
            f"🔴 Коэффициент пустых продаж: <b>{ratio:.2%}</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        print(f"Error in handle_empty_coeff_date: {e}")
        await callback.answer("⚠️ Ошибка при расчете коэффициента")

async def back_to_ratio_theatres(callback: types.CallbackQuery):
    await show_theatres_for_empty_coeff(callback.message)
    await callback.answer()

async def back_to_ratio_spect(callback: types.CallbackQuery):
    theatre_id = int(callback.data.split("_")[3])
    await handle_empty_coeff_theatre(callback)
    await callback.answer()
    
    
#успешности
async def show_theatres_for_success_coeff(message: types.Message):
        theatres = await get_theatres()
        builder = InlineKeyboardBuilder()
        for theatre in theatres:
            builder.button(
                text=f"{theatre['name']}",
                callback_data=f"success_theatre_{theatre['id_theatre']}"
            )
        
        builder.button(
            text="↩️ Главное меню",
            callback_data="main_menu"
        )
        builder.adjust(1)
        
        await message.answer(
            "🎭 Выберите театр для расчета коэффициента успешности:",
            reply_markup=builder.as_markup()
        )

async def handle_success_coeff_theatre(callback: types.CallbackQuery):
    try:
        theatre_id = int(callback.data.split("_")[2])
        theatre_name = await get_theatre_name(theatre_id)
        spectacles = await get_spectacles_for_theatre(theatre_id)
        
        builder = InlineKeyboardBuilder()
        for spect in spectacles:
            builder.button(
                text=f"{spect['name']}",
                callback_data=f"success_spect_{spect['id_spectacle']}_{theatre_id}"
            )
        
        builder.button(
            text="↩️ Назад к театрам",
            callback_data="back_to_success_theatres"
        )
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"📌 Выберите спектакль в театре <b>{theatre_name}</b>:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        print(f"Error in handle_success_coeff_theatre: {e}")
        await callback.answer("⚠️ Ошибка при загрузке спектаклей")

async def handle_success_coeff_spectacle(callback: types.CallbackQuery):
    try:
        _, _, spectacle_id, theatre_id = callback.data.split("_")
        spectacle_id = int(spectacle_id)
        theatre_id = int(theatre_id)
        
        spectacle = await get_spectacle_info(spectacle_id)
        dates = await get_spectacle_dates(spectacle_id, theatre_id)
        
        builder = InlineKeyboardBuilder()
        for date in dates:
            btn_text = date['date'].strftime('%d.%m.%Y')
            
            builder.button(
                text=btn_text,
                callback_data=f"success_date_{theatre_id}_{spectacle_id}_{date['id_repertoire']}"
            )
        
        builder.button(
            text="↩️ Назад",
            callback_data=f"back_to_success_spect_{theatre_id}"
        )
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"Выберите дату для <b>{spectacle['name']}</b>:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        print(f"Error in handle_success_coeff_spectacle: {str(e)}")
        await callback.answer("⚠️ Ошибка при загрузке дат")

async def handle_success_coeff_date(callback: types.CallbackQuery):
    try:
        _, _, theatre_id, spectacle_id, repertoire_id = callback.data.split("_")
        theatre_id = int(theatre_id)
        spectacle_id = int(spectacle_id)
        repertoire_id = int(repertoire_id)
        
        success_ratios = await calculate_success_ratio(repertoire_id)
        theatre = await get_theatre_name(theatre_id)
        spectacle = await get_spectacle_name(spectacle_id)
        repertoire = await get_repertoire_info(repertoire_id)
        message_text = (
            f"<b>📊 Коэффициент успешности</b>\n\n"
            f"Театр: {theatre}\n"
            f"Спектакль: {spectacle}\n"
            f"📅 Дата: {repertoire['date'].strftime('%d.%m.%Y')}\n\n"
        )
        
        for category in success_ratios:
            message_text += (
                f"<b>{category['category_name']}</b>:\n"
                f"• Продано: {category['sold']}/{category['total']}\n"
                f"• Коэффициент: <b>{category['ratio']:.2%}</b>\n\n"
            )
        
        total_sold = sum(c['sold'] for c in success_ratios)
        total_seats = sum(c['total'] for c in success_ratios)
        total_ratio = total_sold / total_seats if total_seats > 0 else 0
        
        message_text += (
            f"<b>Итого по всем категориям:</b>\n"
            f"• Продано: {total_sold}/{total_seats}\n"
            f"• Общий коэффициент: <b>{total_ratio:.2%}</b>"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(
            text="↩️ К выбору дат",
            callback_data=f"success_spect_{spectacle_id}_{theatre_id}"
        )
        
        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        print(f"Error in handle_success_coeff_date: {e}")
        await callback.answer("⚠️ Ошибка при расчете коэффициента")

async def back_to_success_theatres(callback: types.CallbackQuery):
    await show_theatres_for_success_coeff(callback.message)
    await callback.answer()

async def back_to_success_spect(callback: types.CallbackQuery):
    theatre_id = int(callback.data.split("_")[3])
    await handle_success_coeff_theatre(callback)
    await callback.answer()

async def calculate_success_ratio(repertoire_id: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    repertoire_info = await conn.fetchrow(
            "SELECT id_theatre FROM repertoire WHERE id_repertoire = $1",
            repertoire_id
        )
    theatre_id = repertoire_info['id_theatre']
    categories = await conn.fetch(
            """SELECT sc.name_category_seat, ct.seats_amount, ct.id_category_theater
               FROM category_theater ct
               JOIN seat_category sc ON ct.id_seat_category = sc.id_seat_category
               WHERE ct.id_theatre = $1""",
            theatre_id
        )
        
    if not categories:
            return []
        
    result = []
    for category in categories:
        sold = await conn.fetchval(
                """SELECT COALESCE(SUM(pp.quantity), 0)
                   FROM position_purchase pp
                   JOIN ticket t ON pp.id_ticket = t.id_ticket
                   JOIN purchase p ON pp.id_purchase = p.id_purchase
                   WHERE t.id_repertoire = $1
                   AND t.id_category_theater = $2
                   AND (p.discount >= 0 OR p.discount IS NULL)""",
                repertoire_id,
                category['id_category_theater']
            )
        total = category['seats_amount']
        ratio = sold / total if total > 0 else 0
            
        result.append({
                'category_name': category['name_category_seat'],
                'sold': sold,
                'total': total,
                'ratio': ratio
        })
        
        return result
    await conn.close()
    



async def process_finance_quarter(callback: types.CallbackQuery):
    try:
        _, start_date_str, end_date_str = callback.data.split('_')
        
        current_year = datetime.now().year
        start_date = datetime.strptime(f"{start_date_str}.{current_year}", "%d.%m.%Y").date()
        end_date = datetime.strptime(f"{end_date_str}.{current_year}", "%d.%m.%Y").date()
        conn = await asyncpg.connect(**DB_CONFIG)
        monthly_data = await conn.fetch(
            '''
            SELECT 
                EXTRACT(MONTH FROM purchase.date_purchase) AS month,
                EXTRACT(YEAR FROM purchase.date_purchase) AS year,
                SUM(CASE WHEN position_purchase.quantity > 0 
                     THEN position_purchase.quantity * position_purchase.price ELSE 0 END) AS revenue,
                SUM(CASE WHEN position_purchase.quantity < 0 
                     THEN position_purchase.quantity * position_purchase.price ELSE 0 END) AS refund,
                SUM(position_purchase.quantity * position_purchase.price) AS profit
            FROM position_purchase
            JOIN purchase ON purchase.id_purchase = position_purchase.id_purchase
            WHERE purchase.date_purchase >= $1 AND purchase.date_purchase <= $2
            GROUP BY EXTRACT(MONTH FROM purchase.date_purchase), EXTRACT(YEAR FROM purchase.date_purchase)
            ORDER BY year, month
            ''',
            start_date, end_date
        )
        
        total_data = await conn.fetchrow(
            '''
            SELECT 
                SUM(CASE WHEN position_purchase.quantity > 0 
                     THEN position_purchase.quantity * position_purchase.price ELSE 0 END) AS total_revenue,
                SUM(CASE WHEN position_purchase.quantity < 0 
                     THEN position_purchase.quantity * position_purchase.price ELSE 0 END) AS total_refund,
                SUM(position_purchase.quantity * position_purchase.price) AS total_profit
            FROM position_purchase
            JOIN purchase ON purchase.id_purchase = position_purchase.id_purchase
            WHERE purchase.date_purchase >= $1 AND purchase.date_purchase <= $2
            ''',
            start_date, end_date
        )
        
        await conn.close()
        
        response = [
            f"📊 <b>Финансовый отчет за период:</b> {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n",
            "┌───────────────────────────────────────"
        ]
        
        month_names = {
            1: "Январь", 2: "Февраль", 3: "Март",
            4: "Апрель", 5: "Май", 6: "Июнь",
            7: "Июль", 8: "Август", 9: "Сентябрь",
            10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        
        data_dict = {(int(record['month']), int(record['year'])): record for record in monthly_data}
        
        current = start_date
        while current <= end_date:
            year = current.year
            month = current.month
            month_name = month_names.get(month, f"Месяц {month}")
            
            month_data = data_dict.get((month, year), {
                'revenue': 0,
                'refund': 0,
                'profit': 0
            })
            
            response.extend([
                f"│ <b>{month_name} {year}</b>",
                f"│ ├─ Выручка: {abs(0.0 if month_data['revenue'] is None else month_data['revenue']):.2f} руб.",
                f"│ ├─ Возвраты: {abs(0.0 if month_data['refund'] is None else month_data['refund']):.2f} руб.",
                f"│ └─ Прибыль: {month_data['profit']:.2f} руб.",
                "├───────────────────────────────────────"
            ])
            
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        response.extend([
            "└─ <b>Итого за период:</b>",
            f"   ├─ Выручка: {abs(0.0 if total_data['total_revenue'] is None else total_data['total_revenue']):.2f} руб.",
            f"   ├─ Возвраты: {abs(0.0 if total_data['total_refund'] is None else total_data['total_refund']):.2f} руб.",
            f"   └─ Прибыль: {total_data['total_profit']:.2f} руб."
        ])
        
        await callback.message.answer("\n".join(response), parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        print(f"Error in process_finance_quarter: {e}")
        await callback.answer()
