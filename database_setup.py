import sqlite3
import os
import json
from datetime import datetime # Убедитесь, что datetime импортирован

# Определение путей к файлам (аналогично app.py)
BASE_DIR = os.path.dirname(__file__)
DATABASE_NAME = os.path.join(BASE_DIR, 'chess_ratings.db')
JSON_FILE = os.path.join(BASE_DIR, 'players_kbr.json')
RATINGS_FILE = os.path.join(BASE_DIR, 'ratings_history.json')

# --- Функции для работы с БД (аналогично app.py, но для setup) ---
def create_connection():
    """Создает соединение с базой данных SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        # print(f"SQLite DB [{DATABASE_NAME}] подключена, версия: {sqlite3.version}") # Можно раскомментировать для отладки
    except sqlite3.Error as e:
        print(f"Ошибка подключения к SQLite DB: {e}")
    return conn

def create_table(conn, create_table_sql):
    """Создает таблицу по SQL-запросу."""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(f"Ошибка при создании таблицы: {e}")

# --- Функции для загрузки JSON (адаптированы для setup-скрипта) ---
def _load_json_data_for_setup(file_path, description):
    """Вспомогательная функция для загрузки JSON данных в setup-скрипте."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Успешно загружены данные из {description} ({file_path}): {len(data)} записей")
        return data
    except FileNotFoundError:
        print(f"Файл {description} ({file_path}) не найден")
        return []
    except json.JSONDecodeError:
        print(f"Неверный формат JSON в файле {description} ({file_path})")
        return []
    except Exception as e:
        print(f"Непредвиденная ошибка при загрузке {description} ({file_path}): {e}")
        return []

def initialize_database():
    """Создает все необходимые таблицы в базе данных."""
    conn = create_connection()

    if conn is not None:
        print(f"Инициализация таблиц в базе данных [{DATABASE_NAME}]...")
        # Таблица игроков
        sql_create_players_table = """
        CREATE TABLE IF NOT EXISTS players (
            fsr_id INTEGER PRIMARY KEY,
            fide_id TEXT,
            full_name TEXT NOT NULL,
            birth_year INTEGER,
            gender TEXT CHECK(gender IN ('male', 'female')),
            local_title TEXT,
            fsr_official_title TEXT,
            is_classic_champion INTEGER DEFAULT 0 CHECK(is_classic_champion IN (0, 1)),
            is_rapid_champion INTEGER DEFAULT 0 CHECK(is_rapid_champion IN (0, 1)),
            is_blitz_champion INTEGER DEFAULT 0 CHECK(is_blitz_champion IN (0, 1)),
            is_child INTEGER DEFAULT 0 CHECK(is_child IN (0,1)),
            current_fsr_classic_rating INTEGER DEFAULT 0,
            previous_fsr_classic_rating INTEGER DEFAULT 0,
            current_fsr_rapid_rating INTEGER DEFAULT 0,
            current_fsr_blitz_rating INTEGER DEFAULT 0,
            current_fide_classic_rating INTEGER DEFAULT 0,
            current_fide_rapid_rating INTEGER DEFAULT 0,
            current_fide_blitz_rating INTEGER DEFAULT 0,
            fsr_tournaments_played_count INTEGER DEFAULT 0,
            last_profile_update_at TEXT
        );
        """
        create_table(conn, sql_create_players_table)
        print("Таблица 'players' проверена/создана.")

        # Таблица турниров
        sql_create_tournaments_table = """
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fsr_tournament_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            date_str TEXT,
            start_date TEXT,
            end_date TEXT,
            fsr_link TEXT UNIQUE,
            game_type TEXT,
            organization TEXT,
            highlights_json TEXT,
            last_results_parsed_at TEXT
        );
        """
        create_table(conn, sql_create_tournaments_table)
        print("Таблица 'tournaments' проверена/создана.")

        # Таблица результатов игроков в турнирах
        sql_create_tournament_player_results_table = """
        CREATE TABLE IF NOT EXISTS tournament_player_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_db_id INTEGER NOT NULL,
            player_fsr_id INTEGER NOT NULL,
            seeding_number INTEGER,
            place_str TEXT,
            points REAL,
            initial_rating INTEGER,
            new_rating INTEGER,
            rating_change INTEGER DEFAULT 0,
            avg_opponent_rating_fsr INTEGER,
            calculated_performance_rating INTEGER,
            norm_achieved TEXT,
            white_score REAL DEFAULT 0.0,
            white_games INTEGER DEFAULT 0,
            black_score REAL DEFAULT 0.0,
            black_games INTEGER DEFAULT 0,
            FOREIGN KEY (tournament_db_id) REFERENCES tournaments (id) ON DELETE CASCADE,
            FOREIGN KEY (player_fsr_id) REFERENCES players (fsr_id) ON DELETE CASCADE,
            UNIQUE (tournament_db_id, player_fsr_id)
        );
        """
        create_table(conn, sql_create_tournament_player_results_table)
        print("Таблица 'tournament_player_results' проверена/создана.")

        # Таблица партий в турнирах
        sql_create_tournament_games_table = """
        CREATE TABLE IF NOT EXISTS tournament_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tpr_id INTEGER NOT NULL, 
            round_number INTEGER,
            opponent_seeding_number INTEGER,
            opponent_initial_rating INTEGER,
            player_color TEXT CHECK(player_color IN ('white', 'black', 'unknown')),
            score_achieved REAL CHECK(score_achieved IN (0.0, 0.5, 1.0)),
            is_bye INTEGER DEFAULT 0 CHECK(is_bye IN (0,1)),
            FOREIGN KEY (tpr_id) REFERENCES tournament_player_results (id) ON DELETE CASCADE
        );
        """
        create_table(conn, sql_create_tournament_games_table)
        print("Таблица 'tournament_games' проверена/создана.")
        
        # Таблица для системной информации
        sql_create_system_info_table = """
        CREATE TABLE IF NOT EXISTS system_info (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
        create_table(conn, sql_create_system_info_table)
        print("Таблица 'system_info' проверена/создана.")

        conn.close()
        print(f"Инициализация таблиц базы данных [{DATABASE_NAME}] завершена.")
    else:
        print("Ошибка! Не удалось создать соединение с базой данных для инициализации таблиц.")

def migrate_players_to_db():
    print("Начало миграции данных игроков в SQLite...")
    conn = create_connection()
    if conn is None:
        print("Миграция: Не удалось подключиться к БД.")
        return

    cursor = conn.cursor()

    initial_players_data = _load_json_data_for_setup(JSON_FILE, "players_kbr.json")
    ratings_history_data = _load_json_data_for_setup(RATINGS_FILE, "ratings_history.json")

    ratings_map = {str(p.get('id', p.get('Код ФШР'))): p for p in ratings_history_data if p.get('id') or p.get('Код ФШР')}

    migrated_count = 0
    skipped_count = 0
    current_year = datetime.now().year

    for p_initial in initial_players_data:
        fsr_id_str = str(p_initial.get("Код ФШР"))
        if not fsr_id_str or not fsr_id_str.isdigit():
            print(f"Миграция: Пропущен игрок из players_kbr.json без валидного 'Код ФШР': {p_initial.get('ФИО')}")
            skipped_count += 1
            continue
        fsr_id_int = int(fsr_id_str)
        
        rating_entry = ratings_map.get(fsr_id_str, {})

        age = 0
        is_child_bool = False
        birth_year_initial_str = p_initial.get('Год рождения')
        birth_year_val = None
        if birth_year_initial_str and str(birth_year_initial_str).strip().isdigit():
            birth_year_val = int(birth_year_initial_str)
            if 1900 <= birth_year_val <= current_year:
                age = current_year - birth_year_val
                if age <= 18: # Обычно дети до 18 включительно
                    is_child_bool = True
        
        current_fsr_classic = int(rating_entry.get('rating', 0))
        change_val_classic = rating_entry.get('change_value_classic', 0)
        # Убедимся, что change_val_classic это число, если нет, то 0
        try:
            change_val_classic_int = int(change_val_classic)
        except (ValueError, TypeError):
            change_val_classic_int = 0
            
        previous_fsr_classic = current_fsr_classic - change_val_classic_int

        player_db_entry_values = (
            fsr_id_int,
            str(rating_entry.get('fide_id_fsr', p_initial.get('Код ФИДЕ', ''))),
            rating_entry.get('name_fsr', p_initial.get('ФИО', 'Не указано')),
            birth_year_val, # Может быть None
            'female' if p_initial.get('Пол', 'М') == 'Ж' else 'male',
            p_initial.get('Разряд'),
            rating_entry.get('title_fsr'),
            1 if p_initial.get('is_classic_champion', False) else 0,
            1 if p_initial.get('is_rapid_champion', False) else 0,
            1 if p_initial.get('is_blitz_champion', False) else 0,
            1 if is_child_bool else 0,
            current_fsr_classic,
            previous_fsr_classic,
            int(rating_entry.get('rapid_rating', 0)),
            int(rating_entry.get('blitz_rating', 0)),
            int(rating_entry.get('fide_rating', 0)),
            int(rating_entry.get('fide_rapid', 0)),
            int(rating_entry.get('fide_blitz', 0)),
            int(rating_entry.get('tournamentsPlayed', 0)),
            rating_entry.get('last_updated', datetime.now().isoformat())
        )

        columns = [
            'fsr_id', 'fide_id', 'full_name', 'birth_year', 'gender', 'local_title', 
            'fsr_official_title', 'is_classic_champion', 'is_rapid_champion', 'is_blitz_champion', 'is_child',
            'current_fsr_classic_rating', 'previous_fsr_classic_rating', 
            'current_fsr_rapid_rating', 'current_fsr_blitz_rating',
            'current_fide_classic_rating', 'current_fide_rapid_rating', 'current_fide_blitz_rating',
            'fsr_tournaments_played_count', 'last_profile_update_at'
        ]
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT OR REPLACE INTO players ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            cursor.execute(sql, player_db_entry_values)
            migrated_count += 1
        except sqlite3.Error as e:
            print(f"Ошибка SQLite при вставке игрока ID {fsr_id_int}: {e}")
            # print(f"Данные: {player_db_entry_values}") # Для детальной отладки
            skipped_count += 1

    conn.commit()
    conn.close()
    print(f"Миграция игроков завершена. Перенесено: {migrated_count}, пропущено из-за ошибок/отсутствия ID: {skipped_count}.")


if __name__ == '__main__':
    print("--- Запуск инициализации базы данных ---")
    initialize_database()
    print("\n--- Запуск миграции данных игроков ---")
    migrate_players_to_db()
    print("\n--- Все операции setup завершены ---")