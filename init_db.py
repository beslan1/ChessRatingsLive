# Файл: init_db.py (версия для pyodbc)
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

db_server = os.environ.get('MSSQL_SERVER')
db_user = os.environ.get('MSSQL_USER')
db_password = os.environ.get('MSSQL_PASSWORD')
db_name = os.environ.get('MSSQL_DATABASE')

if not all([db_server, db_user, db_password, db_name]):
    print("Ошибка: Не найдены все необходимые переменные окружения для MS SQL.")
else:
    try:
        print(f"Подключаемся к MS SQL серверу: {db_server} через pyodbc...")
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={db_server};"
            f"DATABASE={db_name};"
            f"UID={db_user};"
            f"PWD={db_password};"
        )
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()

        print("Читаем файл schema.sql...")
        with open('schema.sql', 'r', encoding='utf-8') as f:
            # ODBC драйвер обычно хорошо работает с многокомандными скриптами
            sql_script = f.read()

        print("Выполняем SQL-скрипт для создания таблиц...")
        cursor.execute(sql_script)

        print("Таблицы успешно созданы!")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка: {e}")