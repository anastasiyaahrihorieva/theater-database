from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from handlers import *
import asyncpg
from configuration import BOT_TOKEN, DB_CONFIG
import asyncio

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot=bot)
    pool = await asyncpg.create_pool(**DB_CONFIG)

    message_handlers = {
        cmd_start: [Command('start')],
        user_menu: [F.text == "Я пользователь"],
        handle_buy_ticket_menu: [F.text == "Купить билет"],
        show_purchases: [F.text == "Мои покупки"],
        show_cart: [F.text == "Моя корзина"],
        return_to_main_menu_text: [F.text == "Главное меню"],
        choose_spectacle: [F.text == "Сначала выбрать спектакль"],
        choose_theatre: [F.text == "Сначала выбрать театр"],
        show_report_menu: [F.text == "Получить отчетность"],
        show_theatres: [F.text == "Репертуары театров"],
        show_theatres_sold: [F.text == "Проданные билеты"],
        show_finance_date: [F.text == "Финансовый отчет"],
        show_theatres_for_empty_coeff: [F.text == "Коэффициент пустых продаж"],
        show_theatres_for_success_coeff: [F.text == "Коэффициент успешности"],
        show_refund_menu: [F.text == "Оформить возврат"]
    }

    for handler, filters in message_handlers.items():
        dp.message.register(handler, *filters)

    callback_handlers = {
        process_finance_quarter: [F.data.startswith("finance_")],
        choose_theatre_info: [F.data.startswith("choosetheatre_")],
        choose_spectacle_date: [F.data.startswith("spectacle_")],
        show_ticket_options: [F.data.startswith("date_")],
        add_to_cart: [F.data.startswith("addtocart_")],
        choose_spectacle_date2: [F.data.startswith("spectheatre_")],
        handle_date_selection: [F.data.startswith("spec_date_")],
        show_theatre_info: [F.data.startswith("theatre_")],
        show_theatre_repertoire: [F.data.startswith("theatre_")],
        handle_spectacle_choosing: [F.data.startswith("spectacleschoosing_")],
        show_ticket_options: [F.data.startswith("ticketoptions_")],
        process_payment: [F.data == "process_payment"],
        back_to_theatres: [F.data.startswith("back_to_theatres_")],
        process_refund: [F.data.startswith("refund_")],
        confirm_refund: [F.data.startswith("confirm_refund_"), F.data == "cancel_refund"],
        show_theatre_sold_info: [F.data.startswith("theatresold_")],
        show_spectacle_stats: [F.data.startswith("spectstats_")],
        show_date_stats: [F.data.startswith("datestats_")],
        handle_empty_coeff_theatre: [F.data.startswith("ratio_theatre_")],
        handle_empty_coeff_spectacle: [F.data.startswith("ratio_spect_")],
        handle_empty_coeff_date: [F.data.startswith("ratio_date_")],
        back_to_ratio_theatres: [F.data == "back_to_ratio_theatres"],
        back_to_ratio_spect: [F.data.startswith("back_to_ratio_spect_")],
        handle_theatre_choice: [F.data.startswith("ratio_")],
        handle_success_coeff_theatre: [F.data.startswith("success_theatre_")],
        handle_success_coeff_spectacle: [F.data.startswith("success_spect_")],
        handle_success_coeff_date: [F.data.startswith("success_date_")],
        back_to_success_theatres: [F.data == "back_to_success_theatres"],
        back_to_success_spect: [F.data.startswith("back_to_success_spect_")]
    }

    for handler, filters in callback_handlers.items():
        dp.callback_query.register(handler, *filters)

    await dp.start_polling(bot)
    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())