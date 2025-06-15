# Файл: init_db.py (Простая версия для SQLite)
import sqlite3
import os

# Определяем имя файла базы данных
DATABASE_FILE = os.path.join(os.path.dirname(__file__), 'chess_ratings.db')

# На всякий случай удаляем старый файл базы данных, чтобы начать с чистого листа
if os.path.exists(DATABASE_FILE):
    os.remove(DATABASE_FILE)
    print(f"Старый файл '{DATABASE_FILE}' удален.")

# SQL-команда для создания таблицы, адаптированная для SQLite
sql_create_table = """
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fsr_id INTEGER UNIQUE NOT NULL,
    fide_id INTEGER,
    full_name TEXT NOT NULL,
    birth_year INTEGER,
    gender TEXT,
    local_title TEXT,
    fsr_official_title TEXT,
    is_classic_champion INTEGER DEFAULT 0,
    is_rapid_champion INTEGER DEFAULT 0,
    is_blitz_champion INTEGER DEFAULT 0,
    is_child INTEGER DEFAULT 0,
    current_fsr_classic_rating INTEGER DEFAULT 0,
    previous_fsr_classic_rating INTEGER DEFAULT 0,
    current_fsr_rapid_rating INTEGER DEFAULT 0,
    previous_fsr_rapid_rating INTEGER DEFAULT 0,
    current_fsr_blitz_rating INTEGER DEFAULT 0,
    previous_fsr_blitz_rating INTEGER DEFAULT 0,
    current_fide_classic_rating INTEGER DEFAULT 0,
    current_fide_rapid_rating INTEGER DEFAULT 0,
    current_fide_blitz_rating INTEGER DEFAULT 0,
    fsr_tournaments_played_count INTEGER DEFAULT 0,
    last_profile_update_at TEXT
);
"""

try:
    print(f"Создаем новую базу данных SQLite в файле '{DATABASE_FILE}'...")
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    print("Создаем таблицу 'players'...")
    cursor.executescript(sql_create_table) # .executescript для выполнения скрипта

    conn.commit()
    print("База данных и таблица успешно созданы!")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"Произошла ошибка при создании базы SQLite: {e}")