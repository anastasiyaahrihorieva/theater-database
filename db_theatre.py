import asyncpg
from datetime import datetime
import asyncio

async def main():
    conn = await asyncpg.connect('postgresql://postgres:258147@localhost/theatre_db')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS theatre (
            id_theatre SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        
        CREATE TABLE IF NOT EXISTS spectacle (
            id_spectacle SERIAL PRIMARY KEY,
            name TEXT,
            genre TEXT,
            director TEXT
        );
        
        CREATE TABLE IF NOT EXISTS repertoire (
            id_repertoire SERIAL PRIMARY KEY,
            id_spectacle INT REFERENCES spectacle(id_spectacle),
            id_theatre INT REFERENCES theatre(id_theatre),
            start_date DATE,  
            end_date DATE,
            UNIQUE (id_spectacle, id_theatre, start_date, end_date)
        );
        
        CREATE TABLE IF NOT EXISTS seat_category (
            id_seat_category SERIAL PRIMARY KEY,
            name_category_seat TEXT UNIQUE
        );
        
        CREATE TABLE IF NOT EXISTS category_theater (
            id_category_theater SERIAL PRIMARY KEY,
            id_theatre INT REFERENCES theatre(id_theatre),
            id_seat_category INT REFERENCES seat_category(id_seat_category),
            seats_amount INT,
            UNIQUE (id_theatre, id_seat_category)
        );
        
        CREATE TABLE IF NOT EXISTS ticket (
            id_ticket SERIAL PRIMARY KEY,
            id_repertoire INT REFERENCES repertoire(id_repertoire),
            id_category_theater INT REFERENCES category_theater(id_category_theater),
            price DECIMAL(10, 2),
            UNIQUE (id_repertoire, id_category_theater)
        );
        
        CREATE TABLE IF NOT EXISTS purchase (
            id_purchase SERIAL PRIMARY KEY,
            date_purchase DATE,
            sum_purchase DECIMAL(10, 2),
            discount DECIMAL(10, 2)
        );
        
        CREATE TABLE IF NOT EXISTS position_purchase (
            id_position_purchase SERIAL PRIMARY KEY,
            id_purchase INT REFERENCES purchase(id_purchase),
            id_ticket INT REFERENCES ticket(id_ticket),
            quantity INT,
            price DECIMAL(10, 2)
        );
    ''')

    data = {
        'theatre': [
            ('Мариинский театр',),
            ('Театр драмы имени А.С. Пушкина',),
            ('Большой драматический театр имени Г.А. Товстоногова',),
            ('Театр "Балтийский дом"',),
            ('Театр "Лицей"',)
        ],
        'spectacle': [
            (1, 'Лебединое озеро', 'Балет', 'Мариус Петипа'),
            (2, 'Гамлет', 'Трагедия', 'Юрий Любимов'),
            (3, 'Ревизор', 'Комедия', 'Константин Станиславский'),
            (4, 'Чайка', 'Драма', 'Антон Чехов'),
            (5, 'Ромео и Джульетта', 'Трагедия', 'Франко Дзеффирелли'),
            (6, 'Щелкунчик', 'Балет', 'Пётр Чайковский'),
            (7, 'Вишнёвый сад', 'Драма', 'Анатолий Эфрос'),
            (8, 'Женитьба Фигаро', 'Комедия', 'Пьер Бомарше'),
            (9, 'Кармен', 'Опера', 'Жорж Бизе'),
            (10, 'Король Лир', 'Трагедия', 'Питер Брук')
        ],
        'repertoire': [
            # Мариинский театр
            (1, 1, datetime(2025, 6, 10).date(), datetime(2025, 7, 15).date()),
            (6, 1, datetime(2025, 8, 1).date(), datetime(2025, 9, 20).date()),
            (9, 1, datetime(2025, 6, 20).date(), datetime(2025, 7, 30).date()),
            
            # Театр драмы им. Пушкина
            (2, 2, datetime(2025, 6, 15).date(), datetime(2025, 7, 25).date()),
            (4, 2, datetime(2025, 8, 5).date(), datetime(2025, 9, 25).date()),
            (7, 2, datetime(2025, 7, 10).date(), datetime(2025, 8, 20).date()),
            
            # БДТ им. Товстоногова
            (3, 3, datetime(2025, 6, 5).date(), datetime(2025, 7, 15).date()),
            (5, 3, datetime(2025, 8, 10).date(), datetime(2025, 9, 28).date()),
            (8, 3, datetime(2025, 7, 1).date(), datetime(2025, 8, 15).date()),
            
            # Театр "Балтийский дом"
            (2, 4, datetime(2025, 6, 20).date(), datetime(2025, 7, 31).date()),
            (10, 4, datetime(2025, 8, 15).date(), datetime(2025, 9, 30).date()),
            
            # Театр "Лицей"
            (4, 5, datetime(2025, 6, 25).date(), datetime(2025, 8, 10).date()),
            (7, 5, datetime(2025, 8, 20).date(), datetime(2025, 9, 30).date())
        ],
        'seat_category': [
            ('Партер',),
            ('Балкон',),
            ('Ложа',),
            ('Амфитеатр',)
        ],
        'category_theater': [
            # Мариинский театр
            (1, 1, 300), (1, 2, 200), (1, 3, 50), (1, 4, 150),
            # Театр драмы им. Пушкина
            (2, 1, 250), (2, 2, 180), (2, 3, 40), (2, 4, 120),
            # БДТ им. Товстоногова
            (3, 1, 280), (3, 2, 190), (3, 4, 130),
            # Театр "Балтийский дом"
            (4, 1, 200), (4, 2, 150), (4, 3, 30), (4, 4, 100),
            # Театр "Лицей"
            (5, 1, 120), (5, 2, 80)
        ]
    }

    async with conn.transaction():
        await conn.executemany(
            "INSERT INTO theatre(name) VALUES($1) ON CONFLICT (name) DO NOTHING",
            data['theatre']
        )
        
        await conn.executemany(
            "INSERT INTO spectacle(id_spectacle, name, genre, director) VALUES($1, $2, $3, $4) ON CONFLICT (id_spectacle) DO NOTHING",
            data['spectacle']
        )
        
        await conn.executemany(
            """INSERT INTO repertoire(id_spectacle, id_theatre, start_date, end_date)
            VALUES($1, $2, $3, $4) ON CONFLICT (id_spectacle, id_theatre, start_date, end_date) DO NOTHING""",
            data['repertoire']
        )
        
        await conn.executemany(
            "INSERT INTO seat_category(name_category_seat) VALUES($1) ON CONFLICT (name_category_seat) DO NOTHING",
            data['seat_category']
        )
        
        await conn.executemany(
            """INSERT INTO category_theater(id_theatre, id_seat_category, seats_amount)
            VALUES($1, $2, $3) ON CONFLICT (id_theatre, id_seat_category) DO NOTHING""",
            data['category_theater']
        )
        
        repertoire_theatres = await conn.fetch(
            "SELECT id_repertoire, id_theatre FROM repertoire"
        )
        
        category_mapping = {}
        query = """
            SELECT id_category_theater, id_theatre, id_seat_category 
            FROM category_theater
        """
        async for row in conn.cursor(query):
            if row['id_theatre'] not in category_mapping:
                category_mapping[row['id_theatre']] = {}
            category_mapping[row['id_theatre']][row['id_seat_category']] = row['id_category_theater']
        
        price_rules = {
            1: {1: 5000.00, 2: 3000.00, 3: 8000.00, 4: 4000.00},  # Мариинский
            2: {1: 3500.00, 2: 2000.00, 3: 5000.00, 4: 2500.00},   # Драмы
            3: {1: 4000.00, 2: 2500.00, 4: 3000.00},                # БДТ
            4: {1: 3000.00, 2: 1800.00, 3: 4500.00, 4: 2200.00},   # Балтийский дом
            5: {1: 2000.00, 2: 1200.00}                            # Лицей
        }
        
        ticket_data = []
        for row in repertoire_theatres:
            id_repertoire = row['id_repertoire']
            id_theatre = row['id_theatre']
            
            if id_theatre in category_mapping and id_theatre in price_rules:
                for seat_cat_id, cat_theater_id in category_mapping[id_theatre].items():
                    price = price_rules[id_theatre].get(seat_cat_id, 0)
                    if price > 0:
                        ticket_data.append((id_repertoire, cat_theater_id, price))
        
        if ticket_data:
            await conn.executemany(
                """INSERT INTO ticket(id_repertoire, id_category_theater, price)
                VALUES($1, $2, $3) ON CONFLICT (id_repertoire, id_category_theater) DO NOTHING""",
                ticket_data
            )
            

    print("База данных успешно создана и заполнена")
    await conn.close()

asyncio.run(main())