from configuration import DB_CONFIG
import asyncpg
import random
import asyncio
import time

async def run_benchmarks():
    pool = await asyncpg.create_pool(**DB_CONFIG)
    test_sizes = [1000, 10000, 100000]
    
    try:
        for size in test_sizes:
            #print(f"\n=== ТЕСТИРОВАНИЕ ДЛЯ {size} ЗАПИСЕЙ ===")
            await prepare_test_data(pool, size)
            await run_search_tests(pool, size)
            await run_insert_tests(pool, size)
            await run_update_tests(pool, size)
            await run_delete_tests(pool, size)
    finally:
        await pool.close()

async def prepare_test_data(pool, size):
    await pool.execute("TRUNCATE theatre CASCADE")
    data = [(f"Театр {i}",) for i in range(size)]
    await pool.executemany("INSERT INTO theatre (name) VALUES ($1)", data)

async def test_pk_search(pool, size):
    total_time = 0
    for _ in range(100):
        start = time.time() 
        await pool.fetchrow("SELECT * FROM theatre WHERE id_theatre = $1",size-1)  
        elapsed_time = time.time() - start
        total_time += elapsed_time

    average_time = total_time / 100 
    return average_time

async def test_name_search(pool, size):
    start = time.time()
    theatres = await pool.fetch("SELECT * FROM theatre")
    target_name = f"Театр {size - 7}"
    
    for theatre in theatres:
        if theatre['name'] == target_name:
            break  
    return time.time() - start

async def test_like_search(pool, size):
    start = time.time()
    search_pattern = f"%Театр {size}%"
    for _ in range(10):
        await pool.fetch(f"SELECT * FROM theatre WHERE name LIKE $1 LIMIT 100", search_pattern)
    return (time.time() - start) / 10

async def run_search_tests(pool, size):
    pk_time = await test_pk_search(pool, size)
    name_time = await test_name_search(pool, size)
    like_time = await test_like_search(pool, size)
    #print(f"Поиск по ID: {pk_time:.6f}")
    #print(f"Поиск по имени: {name_time:.6f}")
    #print(f"Поиск по маске: {like_time:.6f}")

async def test_single_insert(pool, size):
    start = time.time()
    
    for i in range(100):
        await pool.execute("INSERT INTO theatre (name) VALUES ($1)", f"Театр {size} {i}")
    
    return (time.time() - start) / 100
import random
import time

async def test_bulk_insert(pool, size):
    data = [(f"Пакетный театр {i}",) for i in range(size-1)]
    start = time.time()
    await pool.executemany("INSERT INTO theatre (name) VALUES ($1)", data)
    return time.time() - start

async def run_insert_tests(pool, size):
    single_time = await test_single_insert(pool, size)
    bulk_time = await test_bulk_insert(pool, size)
    #print(f"Одиночная вставка: {single_time:.6f}")
    #print(f"Пакетная вставка: {bulk_time:.6f}")

async def test_pk_update(pool, size):
    start = time.time()
    for i in range(100):
        await pool.execute("UPDATE theatre SET name = $1 WHERE id_theatre = $2", 
                           f"Обновлено {i}", random.randint(1, size))
    return (time.time() - start) / 100

async def test_name_update(pool, size):
    start = time.time()
    for i in range(100):
        await pool.execute("UPDATE theatre SET name = $1 WHERE name = $2", 
                           f"Обновлено2 {i}", f"Театр {random.randint(0, size - 1)}")
    return (time.time() - start) / 100

async def run_update_tests(pool, size):
    pk_time = await test_pk_update(pool, size)
    name_time = await test_name_update(pool, size)
    #print(f"Обновление по ID: {pk_time:.6f}")
    #print(f"Обновление по имени: {name_time:.6f}")

async def test_pk_delete(pool, size):
    start = time.time()
    await pool.execute("DELETE FROM theatre WHERE id_theatre = $1", size - 10)
    return time.time() - start

async def test_name_delete(pool, size):
    start = time.time()
    for i in range(100):
        await pool.execute("DELETE FROM theatre WHERE name = $1", f"Театр {9*i}")
    return (time.time() - start) / 100

async def test_group_delete(pool, size):
    await pool.executemany("INSERT INTO theatre (name) VALUES ($1)", 
                           [(f"Восстановленный {i}",) for i in range(100)])
    start = time.time()
    await pool.execute("DELETE FROM theatre WHERE name LIKE 'Восстановленный%'")
    return time.time() - start

async def run_delete_tests(pool, size):
    pk_time = await test_pk_delete(pool, size)
    name_time = await test_name_delete(pool, size)
    group_time = await test_group_delete(pool, size)
    #print(f"Удаление по ID: {pk_time:.6f}")
    #print(f"Удаление по имени: {name_time:.6f}")
    #print(f"Удаление группы: {group_time:.6f}")

if __name__ == "__main__":
    asyncio.run(run_benchmarks())