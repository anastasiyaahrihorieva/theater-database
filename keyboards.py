from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types

def get_main_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(*[types.KeyboardButton(text=btn) for btn in [
        "Я пользователь", "Получить отчетность"
    ]])
    return builder.as_markup(resize_keyboard=True)

def get_user_menu_kb():
    builder = ReplyKeyboardBuilder()
    buttons = [
        "Купить билет", 
        "Моя корзина",
        "Мои покупки",
        "Главное меню",
        "Оформить возврат"
    ]
    for btn in buttons:
        builder.button(text=btn)
    builder.adjust(2, repeat=True)
    return builder.as_markup(resize_keyboard=True)

def get_report_menu_kb():
    builder = ReplyKeyboardBuilder()
    for btn in ["Репертуары театров", "Проданные билеты", "Коэффициент пустых продаж", "Коэффициент успешности", "Главное меню", "Финансовый отчет"]:
        builder.row(types.KeyboardButton(text=btn))
    
    return builder.as_markup(resize_keyboard=True)

def buy_ticket_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="Сначала выбрать театр"))
    builder.row(types.KeyboardButton(text="Сначала выбрать спектакль"))
    builder.row(types.KeyboardButton(text="Главное меню"))
    return builder.as_markup(resize_keyboard=True)
    
def theatres_kb(theatres: list):
    builder = InlineKeyboardBuilder()
    for theatre in theatres:
        builder.button(
            text=theatre['name'],
            callback_data=f"theatre_{theatre['id_theatre']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def choose_theatres_kb(theatres: list):
    builder = InlineKeyboardBuilder()
    for theatre in theatres:
        builder.button(
            text=theatre['name'],
            callback_data=f"choosetheatre_{theatre['id_theatre']}"
        )
    builder.adjust(1)
    return builder.as_markup()

async def theatres_sold_kb(theatres):
    builder = InlineKeyboardBuilder()
    for theatre in theatres:
        builder.button(
            text=theatre['name'],
            callback_data=f"theatresold_{theatre['id_theatre']}"
        )
    builder.adjust(1)
    return builder.as_markup()


def spectacles_choosing(spectacles):
    builder = InlineKeyboardBuilder()
    for spect in spectacles:
        builder.button(
            text=f"{spect['name']}",
            callback_data=f"spectacleschoosing_{spect['id_spectacle']}"
        )
    builder.adjust(2)
    return builder.as_markup()

def theatres_for_spect_kb(theatres, spectacle_id):
    builder = InlineKeyboardBuilder()
    for theatre in theatres:
        builder.button(
            text=theatre['name'],
            callback_data=f"spectheatre_{theatre['id_theatre']}_{spectacle_id}"  
        )
    builder.adjust(1)
    return builder.as_markup()

def spectacles_for_theatre_kb(spectacles):
    builder = InlineKeyboardBuilder()
    for spect in spectacles:
        builder.button(
            text=f"{spect['name']}",
            callback_data=f"spectacle_{spect['id_spectacle']}"
        )
    builder.adjust(1)
    return builder.as_markup()

