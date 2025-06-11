# Файл: init_db.py
import os
import psycopg2
from dotenv import load_dotenv # Установим эту библиотеку для удобства

# Загружаем переменные из файла .env для локального теста
load_dotenv()

DATABASE_URL = 'postgresql://simple_chess_data_user:rcP0xGV6j3D180vWJOXWCrkmV1n67fgO@dpg-d14r20uuk2gs73ci7q5g-a/simple_chess_data'

if not DATABASE_URL:
    print("Ошибка: Переменная окружения DATABASE_URL не найдена.")
    print("Для локального теста создайте файл .env и добавьте в него DATABASE_URL='...'")
else:
    try:
        print("Подключаемся к базе данных...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("Читаем файл schema.sql...")
        with open('schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("Выполняем SQL-скрипт для создания таблиц...")
        cur.execute(sql_script)

        conn.commit()
        print("Таблицы успешно созданы!")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка: {e}")