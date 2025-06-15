from flask import Flask, render_template, jsonify, request
import json
import os
import sqlite3
import pyodbc
import requests
from bs4 import BeautifulSoup, NavigableString
import re
import schedule
import time
import threading
from datetime import datetime, date as datetime_date, timedelta 
import logging
import math 

app = Flask(__name__)
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_that_is_long_and_random')


app.config['TEMPLATES_AUTO_RELOAD'] = True 
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

app_logger = logging.getLogger('ChessRatingsLive')
app_logger.setLevel(logging.INFO)
if app_logger.hasHandlers():
    app_logger.handlers.clear()
handler = logging.FileHandler('update.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app_logger.addHandler(handler)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

BASE_DIR = os.path.dirname(__file__)
JSON_FILE = os.path.join(BASE_DIR, 'players_kbr.json') 
TOURNAMENTS_FILE = os.path.join(BASE_DIR, 'tournaments.json')
DATABASE_FILE = os.path.join(BASE_DIR, 'chess_ratings.db')
LAST_UPDATE_TS_FILE = os.path.join(BASE_DIR, 'last_full_update.timestamp')
PAST_CHAMPIONS_FILE = os.path.join(BASE_DIR, 'past_champions.json')

DP_VALUES = {
    1.00: 800, 0.99: 677, 0.98: 589, 0.97: 538, 0.96: 501, 0.95: 470, 0.94: 444, 0.93: 422, 0.92: 401, 0.91: 383, 0.90: 366,
    0.89: 351, 0.88: 336, 0.87: 322, 0.86: 309, 0.85: 296, 0.84: 284, 0.83: 273, 0.82: 262, 0.81: 251, 0.80: 240,
    0.79: 230, 0.78: 220, 0.77: 211, 0.76: 202, 0.75: 193, 0.74: 184, 0.73: 175, 0.72: 166, 0.71: 158, 0.70: 149,
    0.69: 141, 0.68: 133, 0.67: 125, 0.66: 117, 0.65: 110, 0.64: 102, 0.63: 95, 0.62: 87, 0.61: 80, 0.60: 72,
    0.59: 65, 0.58: 57, 0.57: 50, 0.56: 43, 0.55: 36, 0.54: 29, 0.53: 21, 0.52: 14, 0.51: 7, 0.50: 0,
    0.49: -7, 0.48: -14, 0.47: -21, 0.46: -29, 0.45: -36, 0.44: -43, 0.43: -50, 0.42: -57, 0.41: -65, 0.40: -72,
    0.39: -80, 0.38: -87, 0.37: -95, 0.36: -102, 0.35: -110, 0.34: -117, 0.33: -125, 0.32: -133, 0.31: -141, 0.30: -149,
    0.29: -158, 0.28: -166, 0.27: -175, 0.26: -184, 0.25: -193, 0.24: -202, 0.23: -211, 0.22: -220, 0.21: -230, 0.20: -240,
    0.19: -251, 0.18: -262, 0.17: -273, 0.16: -284, 0.15: -296, 0.14: -309, 0.13: -322, 0.12: -336, 0.11: -351, 0.10: -366,
    0.09: -383, 0.08: -401, 0.07: -422, 0.06: -444, 0.05: -470, 0.04: -501, 0.03: -538, 0.02: -589, 0.01: -677, 0.00: -800
}

# Замените вашу старую функцию get_db_connection на эту
# Замените вашу старую функцию get_db_connection на эту
def get_db_connection():
    # Пытаемся получить данные для подключения к MS SQL из переменных окружения
    db_server = os.environ.get('MSSQL_SERVER')
    db_user = os.environ.get('MSSQL_USER')
    db_password = os.environ.get('MSSQL_PASSWORD')
    db_name = os.environ.get('MSSQL_DATABASE')

    # Проверяем, заданы ли все переменные для MS SQL
    if all([db_server, db_user, db_password, db_name]):
        try:
            # Если да, ПЫТАЕМСЯ подключиться к MS SQL
            app_logger.info(f"Попытка подключения к MS SQL серверу: {db_server}...")
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={db_server};"
                f"DATABASE={db_name};"
                f"UID={db_user};"
                f"PWD={db_password};"
                f"TrustServerCertificate=yes;" # Добавляем для надежности
            )
            conn = pyodbc.connect(conn_str, timeout=5) # Добавляем тайм-аут в 5 секунд
            app_logger.info("Успешное подключение к MS SQL Server.")
            return conn
        except Exception as e:
            # Если подключиться не удалось, логируем ошибку и ПЕРЕХОДИМ ДАЛЬШЕ
            app_logger.warning(f"Не удалось подключиться к MS SQL Server: {e}. Переключаемся на локальную базу SQLite.")
    
    # Этот код выполнится, если переменные для MS SQL не были заданы,
    # ИЛИ если подключение к MS SQL не удалось.
    # Это наш "запасной аэродром".
    try:
        app_logger.info("Подключение к локальной базе SQLite...")
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        app_logger.error(f"Критическая ошибка: не удалось подключиться даже к локальной базе SQLite: {e}")
        return None # Конечная точка, если ничего не работает

def get_dp_for_performance(score_percentage):
    if score_percentage < 0 or score_percentage > 1: return 0 
    p_rounded = round(score_percentage * 100) / 100
    if p_rounded in DP_VALUES: return DP_VALUES[p_rounded]
    if p_rounded > 0.5:
        lower_p = math.floor(p_rounded * 100) / 100
        upper_p = math.ceil(p_rounded * 100) / 100
    else: 
        lower_p = math.ceil(p_rounded * 100) / 100 
        upper_p = math.floor(p_rounded * 100) / 100
    dp_lower = DP_VALUES.get(lower_p)
    dp_upper = DP_VALUES.get(upper_p)
    if dp_lower is None and dp_upper is None: 
        if p_rounded == 0.5: return 0
        return DP_VALUES.get(0.50, 0) if p_rounded > 0.5 else DP_VALUES.get(0.0, -800) if p_rounded < 0.5 else 0
    if dp_lower is None: return dp_upper if dp_upper is not None else 0
    if dp_upper is None: return dp_lower
    if upper_p == lower_p: return dp_lower
    try:
        interpolated_dp = dp_lower + (dp_upper - dp_lower) * (p_rounded - lower_p) / (upper_p - lower_p)
        return int(round(interpolated_dp))
    except ZeroDivisionError: 
        return dp_lower

def load_initial_players(): 
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            players = json.load(f)
        app_logger.info(f"load_initial_players: Успешно загружены данные из {JSON_FILE}: {len(players)} игроков")
        return players
    except FileNotFoundError:
        app_logger.error(f"load_initial_players: Файл {JSON_FILE} не найден")
        return []
    except json.JSONDecodeError:
        app_logger.error(f"load_initial_players: Неверный формат JSON в файле {JSON_FILE}")
        return []

def load_tournaments():
    try:
        if not os.path.exists(TOURNAMENTS_FILE): return []
        with open(TOURNAMENTS_FILE, 'r', encoding='utf-8') as f:
            tournaments = json.load(f)
        app_logger.info(f"Успешно загружены данные из {TOURNAMENTS_FILE}: {len(tournaments)} турниров")
        return tournaments
    except FileNotFoundError:
        app_logger.error(f"Файл {TOURNAMENTS_FILE} не найден. Будет создан новый при обновлении.")
        return []
    except json.JSONDecodeError:
        app_logger.error(f"Неверный формат JSON в файле {TOURNAMENTS_FILE}")
        return []

def save_tournaments(tournaments_data):
    try:
        tournaments_data.sort(
            key=lambda x: datetime.strptime(x.get('date', '01.01.1970').split(' - ')[0].strip(), "%d.%m.%Y"),
            reverse=True
        )
        with open(TOURNAMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tournaments_data, f, ensure_ascii=False, indent=4)
        app_logger.info(f"Данные турниров ({len(tournaments_data)} записей) успешно сохранены в {TOURNAMENTS_FILE}")
    except Exception as e:
        app_logger.error(f"Ошибка при сохранении данных турниров в {TOURNAMENTS_FILE}: {e}")

# ✅ НАЧАЛО: НОВАЯ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ДЛЯ ОПРЕДЕЛЕНИЯ "ЗВЕЗДНОСТИ"
def get_tournament_tier(tournament):
    """
    Определяет "звездный" рейтинг турнира (от 1 до 5) на основе его силы.
    
    Аргументы:
    tournament (dict): Словарь с информацией о турнире. Должен содержать
                       ключи 'name' и 'results'.

    Возвращает:
    int: Количество звезд (от 1 до 5).
    """
    results = tournament.get("results", [])
    name_lower = tournament.get("name", "").lower()

    # Если у турнира нет детальных результатов, по умолчанию даем 1 звезду
    if not results:
        return 1

    # Считаем средний рейтинг топ-15 участников для оценки силы
    sorted_by_rating = sorted(results, key=lambda p: p.get("initial_rating", 0), reverse=True)
    top_15_ratings = [p.get("initial_rating", 0) for p in sorted_by_rating[:15] if p.get("initial_rating", 0) > 0]
    avg_rating_top_15 = round(sum(top_15_ratings) / len(top_15_ratings) if top_15_ratings else 0)

    # --- Логика присвоения звезд на основе рейтинга ---
    tier = 1 # По умолчанию 1 звезда
    if avg_rating_top_15 > 2000:
        tier = 5
    elif avg_rating_top_15 > 1800:
        tier = 4
    elif avg_rating_top_15 > 1650:
        tier = 3
    elif avg_rating_top_15 > 1400:
        tier = 2

    # --- Особое правило: повышаем статус для ключевых турниров ---
    is_championship = ('чемпионат кбр' in name_lower or 
                       'первенство кбр' in name_lower or 
                       ('финал' in name_lower and 'кубк' in name_lower))
    
    # Если это важный турнир и его рейтинг звезд ниже 3, принудительно повышаем до 3.
    if is_championship and tier < 3:
        return 3

    return tier
# КОНЕЦ: НОВАЯ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ

def parse_rating_from_text(text_value): 
    if not isinstance(text_value, str): return 0
    match_with_prefix = re.search(r':\s*(\d+)', text_value)
    if match_with_prefix: return int(match_with_prefix.group(1))
    cleaned_text = text_value.strip()
    if cleaned_text.isdigit(): return int(cleaned_text)
    if cleaned_text.lower() == 'б/р' or cleaned_text == '—' or cleaned_text == '-': return 0
    match_digits_only = re.search(r'(\d+)', cleaned_text)
    if match_digits_only: return int(match_digits_only.group(1))
    return 0

def find_panel_by_title_text(soup_instance, title_text): 
    panel_title_element = soup_instance.find("h3", class_="panel-title", string=re.compile(r"^\s*" + re.escape(title_text) + r"\s*$", re.IGNORECASE))
    if panel_title_element:
        current_element = panel_title_element
        for _ in range(4): 
            parent = current_element.find_parent()
            if not parent: break
            if parent.name == 'div' and 'panel' in parent.get('class', []): return parent
            current_element = parent
        if panel_title_element.parent and 'panel-heading' in panel_title_element.parent.get('class', []):
            if panel_title_element.parent.parent: return panel_title_element.parent.parent
        app_logger.warning(f"Не удалось найти стандартный родительский '.panel' для заголовка '{title_text}'. Возвращаем родителя h3.")
        return panel_title_element.parent 
    app_logger.warning(f"Заголовок панели '{title_text}' не найден.")
    return None

def scrape_individual_fsr_profile(player_id): 
    url = f"https://ratings.ruchess.ru/people/{player_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    scraped_data = {'rating': 0, 'rapid_rating': 0, 'blitz_rating': 0, 'fide_rating': 0, 'fide_rapid': 0, 'fide_blitz': 0, 'tournamentsPlayed': 0, 'name_fsr': None, 'fide_id_fsr': None, 'title_fsr': None}
    try:
        app_logger.info(f"Запрос на {url} для игрока {player_id}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        name_header = soup.select_one("div.page-header > h1")
        if name_header:
            small_tag = name_header.find("small")
            if small_tag: small_tag.decompose() 
            scraped_data['name_fsr'] = name_header.get_text(strip=True)
        fide_panel = find_panel_by_title_text(soup, "Данные FIDE")
        if fide_panel:
            list_items_fide = fide_panel.select("ul.list-group > li.list-group-item")
            for item in list_items_fide:
                strong_label_tag = item.find("strong")
                if not strong_label_tag: continue
                label_text = strong_label_tag.get_text(strip=True)
                if "FIDE ID:" in label_text:
                    link = item.find("a")
                    if link: scraped_data['fide_id_fsr'] = link.get_text(strip=True)
                elif "Звания:" in label_text:
                    title_text_node = strong_label_tag.next_sibling
                    if title_text_node and isinstance(title_text_node, NavigableString):
                        title_candidate = title_text_node.strip()
                        if title_candidate : scraped_data['title_fsr'] = title_candidate
                elif "Рейтинги:" in label_text:
                    std_element = item.select_one("span.text-primary")
                    if std_element: scraped_data['fide_rating'] = parse_rating_from_text(std_element.get_text())
                    rpd_element = item.select_one("span.text-success")
                    if rpd_element: scraped_data['fide_rapid'] = parse_rating_from_text(rpd_element.get_text())
                    blz_element = item.select_one("span.text-danger")
                    if blz_element: scraped_data['fide_blitz'] = parse_rating_from_text(blz_element.get_text())
        fsr_panel = find_panel_by_title_text(soup, "Текущий рейтинг")
        if fsr_panel:
            fsr_rating_elements = fsr_panel.select("ul.list-group > li.list-group-item")
            for item_element in fsr_rating_elements:
                label_element = item_element.select_one("strong > span.text-primary, strong > span.text-success, strong > span.text-danger")
                if not label_element: continue
                label_text = label_element.get_text(strip=True).lower()
                rating_value = 0
                first_b_tag = item_element.find("b")
                if first_b_tag: rating_value = parse_rating_from_text(first_b_tag.get_text())
                else:
                    item_full_text = item_element.get_text(separator=" ", strip=True)
                    match_fsr_val = re.search(r'рейтинг:\s*(\d+)', item_full_text, re.IGNORECASE)
                    if match_fsr_val: rating_value = int(match_fsr_val.group(1))
                if "классические" in label_text: scraped_data['rating'] = rating_value
                elif "быстрые" in label_text: scraped_data['rapid_rating'] = rating_value
                elif "блиц" in label_text: scraped_data['blitz_rating'] = rating_value
        tournaments_selector = "body > div > div:nth-child(3) > div > div > div.list-group > a:nth-child(6) > strong" 
        tournaments_element = soup.select_one(tournaments_selector)
        if tournaments_element:
            text_content = tournaments_element.get_text(strip=True)
            match = re.search(r'\((\d+)\)', text_content) 
            if match: scraped_data['tournamentsPlayed'] = int(match.group(1))
        time.sleep(1) 
        return scraped_data
    except Exception as e:
        app_logger.error(f"Общая ошибка при парсинге профиля игрока {player_id} ({url}): {e}", exc_info=True)
        return None

# ✅ НАЧАЛО: САМАЯ ФИНАЛЬНАЯ И УМНАЯ ВЕРСИЯ ПАРСЕРА
def scrape_official_tournaments(region_id_filter=7):
    app_logger.info(f"Начало парсинга ВСЕХ турниров для региона {region_id_filter}.")
    base_fsr_url = "https://ratings.ruchess.ru"
    tournaments_page_url = f"{base_fsr_url}/tournaments"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    parsed_tournaments_list = []
    page = 1
    
    while True:
        app_logger.info(f"Парсинг страницы {page}...")
        params = {"tournaments_reports_grid[region_id][]": str(region_id_filter), "page": str(page)}
        
        try:
            response = requests.get(tournaments_page_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.select_one("table.table.table-hover.table-condensed")
            
            if not table:
                app_logger.warning(f"Таблица на странице {page} не найдена. Остановка.")
                break

            rows = table.find("tbody").find_all("tr") if table.find("tbody") else []
            app_logger.info(f"Найдено {len(rows)} строк на странице {page}.")

            if not rows:
                app_logger.info(f"Парсер завершил работу (страница {page} пуста).")
                break

            for row in rows:
                # ... (логика парсинга строки без изменений) ...
                tournament_data = {}
                try:
                    title_cell = row.select_one("td.title a")
                    if not title_cell or not title_cell.get('href'): continue
                    tournament_data['name'] = title_cell.get_text(strip=True)
                    relative_link = title_cell['href']
                    tournament_data['fsr_link'] = requests.compat.urljoin(base_fsr_url, relative_link)
                    match_id = re.search(r'/tournaments/(\d+)', relative_link)
                    tournament_data['id'] = int(match_id.group(1)) if match_id else abs(hash(tournament_data['name'] + relative_link)) % (10**9)
                    start_date_str = row.select_one("td.start_date").get_text(strip=True) if row.select_one("td.start_date") else ""
                    end_date_str = row.select_one("td.end_date").get_text(strip=True) if row.select_one("td.end_date") else ""
                    tournament_data['date'] = f"{start_date_str} - {end_date_str}" if start_date_str and end_date_str and start_date_str != end_date_str else start_date_str
                    control_cell = row.select_one("td.chess_type span.label")
                    game_type_text = "unknown"
                    if control_cell:
                        control_text_raw = control_cell.get_text(strip=True).lower()
                        if "классические" in control_text_raw: game_type_text = "classic"
                        elif "быстрые" in control_text_raw: game_type_text = "rapid"
                        elif "блиц" in control_text_raw: game_type_text = "blitz"
                    tournament_data['game_type'] = game_type_text
                    tournament_data['organization'] = "РШФ КБР"
                    tournament_data['results'] = []
                    parsed_tournaments_list.append(tournament_data)
                except Exception as e:
                    app_logger.error(f"Ошибка парсинга строки турнира: {row.get_text(strip=True, separator=' ')}. Ошибка: {e}", exc_info=True)

            # ✅ УМНАЯ ПРОВЕРКА НА ОКОНЧАНИЕ СТРАНИЦ
            stop_after_this_page = False
            pagination_items = soup.select("ul.pagination > li")
            if pagination_items:
                # Последний элемент в навигации - это обычно кнопка "Следующая >"
                last_button = pagination_items[-1]
                # Если у нее есть класс 'disabled', значит, мы на последней странице
                if 'disabled' in last_button.get('class', []):
                    app_logger.info("Обнаружена последняя страница пагинации. Завершаем после этой страницы.")
                    stop_after_this_page = True
            
            if stop_after_this_page:
                break # Выходим из цикла

            time.sleep(1)
            page += 1

        except Exception as e:
            app_logger.error(f"Непредвиденная ошибка при парсинге страницы {page}: {e}", exc_info=True)
            break
            
    app_logger.info(f"Сбор всех турниров завершен. Всего собрано: {len(parsed_tournaments_list)}")
    return parsed_tournaments_list
# КОНЕЦ: ФИНАЛЬНАЯ И УМНАЯ ВЕРСИЯ
def update_tournaments_from_fsr():
    app_logger.info(f"Начало полного обновления списка турниров КБР: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    all_new_tournaments = scrape_official_tournaments()
    
    if all_new_tournaments:
        existing_tournaments = load_tournaments()
        existing_ids = {t['id'] for t in existing_tournaments if 'id' in t}
        new_tournaments_added_list = [t for t in all_new_tournaments if t.get('id') and t['id'] not in existing_ids]
        
        if new_tournaments_added_list:
            combined_tournaments = existing_tournaments + new_tournaments_added_list
            save_tournaments(combined_tournaments) 
            app_logger.info(f"Добавлено {len(new_tournaments_added_list)} новых турниров. Всего теперь: {len(combined_tournaments)}")
        else:
            app_logger.info("Новых турниров не найдено для добавления.")
    else:
        app_logger.warning("Не удалось получить турниры с ФШР для обновления.")

#
# ЗАМЕНИТЕ ВАШУ СТАРУЮ ФУНКЦИЮ scrape_tournament_results НА ЭТУ ВЕРСИЮ
#
def scrape_tournament_results(tournament_url):
    app_logger.info(f"Начало парсинга ВСЕХ ДАННЫХ турнира по URL: {tournament_url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    parsed_player_results = []
    seeding_to_initial_rating = {}

    try:
        response = requests.get(tournament_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.select_one("table.table-bordered.table-condensed")
        if not table:
            table = soup.select_one("table.table")
            if not table:
                app_logger.error(f"Не найдена таблица с результатами на странице: {tournament_url}")
                return []

        html_headers_th = table.select("thead th")
        column_indices = {}
        round_column_indices = []

        for i, th in enumerate(html_headers_th):
            text = th.get_text(strip=True).lower()
            if re.match(r"^(№|#)$", text) and 'start_num' not in column_indices : column_indices['start_num'] = i
            elif 'фед' in text and 'federation' not in column_indices: column_indices['federation'] = i
            elif ('имя участника' in text or 'участник' in text or 'name' in text or 'фио' in text) and 'name' not in column_indices: column_indices['name'] = i
            elif ('rнач' in text or 'r ст' in text or 'стартовый' in text) and 'initial_rating' not in column_indices: column_indices['initial_rating'] = i
            elif text.isdigit(): round_column_indices.append(i) # Для круговиков, где заголовок - просто номер тура/соперника
            elif ('очки' in text or 'рез.' in text or 'итог' in text) and 'points' not in column_indices: column_indices['points'] = i
            elif ('место' in text or 'м-о' in text or re.match(r"^м$", text)) and 'place' not in column_indices: column_indices['place'] = i
            elif 'rср' in text and 'avg_opponent_rating' not in column_indices: column_indices['avg_opponent_rating'] = i
            elif ('rнов' in text or '+/-' in text) and 'new_rating_combined' not in column_indices: column_indices['new_rating_combined'] = i
            elif 'нор' in text and 'norm' not in column_indices: column_indices['norm'] = i
        
        if not round_column_indices:
             for i, th in enumerate(html_headers_th):
                text = th.get_text(strip=True).lower()
                if 'тур' in text and text.split(' ')[-1].isdigit(): round_column_indices.append(i)


        if 'start_num' not in column_indices and 'place' in column_indices :
            column_indices['start_num'] = column_indices['place']
        elif 'start_num' not in column_indices:
            app_logger.warning(f"Не удалось определить колонку с номером жеребьевки/местом для {tournament_url}")
            if html_headers_th and html_headers_th[0].get_text(strip=True).isdigit(): column_indices['start_num'] = 0

        app_logger.info(f"Определены индексы колонок для {tournament_url}: {column_indices}, туры: {round_column_indices}")

        if 'name' not in column_indices or 'initial_rating' not in column_indices:
            app_logger.error(f"Не удалось определить ключевые колонки (имя, нач. рейтинг) для {tournament_url}. Парсинг невозможен.")
            return []
            
        rows = table.select("tbody tr")
        if not rows:
            header_row_count = len(table.select("thead tr"))
            rows = table.select("tr")[header_row_count:]

        app_logger.info(f"Найдено {len(rows)} строк с результатами в таблице турнира {tournament_url}.")

        temp_player_data_for_lookup = []
        for row_idx, row in enumerate(rows):
            cols = row.find_all("td")
            min_cols_needed = max(column_indices.get('name', 0), column_indices.get('initial_rating', 0), column_indices.get('start_num', 0))

            if not cols or len(cols) <= min_cols_needed:
                continue
            
            try:
                seeding_num_text = cols[column_indices['start_num']].get_text(strip=True) if 'start_num' in column_indices else str(row_idx + 1)
                seeding_num = int(seeding_num_text) if seeding_num_text.isdigit() else (row_idx + 1)
                initial_rating_text = cols[column_indices['initial_rating']].get_text(strip=True)
                initial_rating = int(initial_rating_text) if initial_rating_text.isdigit() else 0
                seeding_to_initial_rating[seeding_num] = initial_rating
                temp_player_data_for_lookup.append({'seeding_num': seeding_num, 'cols': cols, 'original_row_idx': row_idx})
            except Exception as e:
                app_logger.error(f"Ошибка при первом проходе по строке {row_idx+1} для {tournament_url}: {e}")

        for player_data_entry in temp_player_data_for_lookup:
            cols = player_data_entry['cols']
            current_seeding_num = player_data_entry['seeding_num']
            row_idx = player_data_entry['original_row_idx']
            
            try:
                final_place = cols[column_indices['place']].get_text(strip=True) if 'place' in column_indices else str(row_idx + 1)
                name_cell = cols[column_indices['name']]
                player_name = name_cell.get_text(strip=True)
                player_id_fsr = None
                if name_cell.find('a') and name_cell.find('a').get('href'):
                    match = re.search(r'/people/(\d+)', name_cell.find('a')['href'])
                    if match: player_id_fsr = int(match.group(1))

                points_str = cols[column_indices['points']].get_text(strip=True).replace(',', '.') if 'points' in column_indices else "0"
                points = float(points_str) if re.match(r"^-?\d+(?:\.\d+)?$", points_str) else 0.0
                initial_rating = seeding_to_initial_rating.get(current_seeding_num, 0)
                avg_opponent_rating_val = 0
                if 'avg_opponent_rating' in column_indices and column_indices['avg_opponent_rating'] < len(cols):
                    avg_opp_text = cols[column_indices['avg_opponent_rating']].get_text(strip=True)
                    if avg_opp_text.isdigit(): avg_opponent_rating_val = int(avg_opp_text)

                new_rating_val, rating_change_val = 0, 0
                if 'new_rating_combined' in column_indices and column_indices['new_rating_combined'] < len(cols):
                    new_rating_cell_text = cols[column_indices['new_rating_combined']].get_text(strip=True)
                    change_span = cols[column_indices['new_rating_combined']].select_one("span.rating-delta")
                    if change_span:
                        change_text_from_span = change_span.get_text(strip=True).replace('+', '').replace('−', '-')
                        try: rating_change_val = int(float(change_text_from_span))
                        except ValueError: rating_change_val = 0
                    
                    new_rating_match = re.match(r'^\s*(\d+)', new_rating_cell_text)
                    if new_rating_match:
                        try: new_rating_val = int(new_rating_match.group(1))
                        except ValueError: pass
                
                if new_rating_val == 0 and initial_rating > 0:
                    new_rating_val = initial_rating + rating_change_val

                norm_val = cols[column_indices['norm']].get_text(strip=True) if 'norm' in column_indices and column_indices['norm'] < len(cols) else ""
                games_played_details = []
                
                for tour_col_idx in round_column_indices:
                    if tour_col_idx >= len(cols): continue

                    game_text = cols[tour_col_idx].get_text(strip=True).replace(',', '.')
                    
                    swiss_match = re.match(r"(\d+)\s*([чЧбБwWbB])\s*([10½]|0.5|1.0|0.0)", game_text)
                    round_robin_match = game_text in ['1', '0', '½', '0.5', '1.0', '0.0']
                    bye_or_forfeit_match = game_text.strip() in ['+', '-']

                    if swiss_match:
                        opp_seeding_num = int(swiss_match.group(1))
                        color_char = swiss_match.group(2).lower()
                        result_char = swiss_match.group(3)
                        player_color = "white" if color_char in ['б', 'w'] else "black"
                        score = 1.0 if result_char in ['1', '1.0'] else 0.5 if result_char in ['½', '0.5'] else 0.0
                        opponent_rating = seeding_to_initial_rating.get(opp_seeding_num)
                        games_played_details.append({"opponent_seeding_num": opp_seeding_num, "opponent_rating": opponent_rating, "player_color": player_color, "score": score, "is_bye": False, "result_str": game_text})
                    
                    elif round_robin_match:
                        header_text = html_headers_th[tour_col_idx].get_text(strip=True)
                        opp_seeding_num_from_header = int(header_text) if header_text.isdigit() else None
                        if opp_seeding_num_from_header:
                            score = 1.0 if game_text in ['1', '1.0'] else 0.5 if game_text in ['½', '0.5'] else 0.0
                            opponent_rating = seeding_to_initial_rating.get(opp_seeding_num_from_header)
                            games_played_details.append({"opponent_seeding_num": opp_seeding_num_from_header, "opponent_rating": opponent_rating, "player_color": "unknown", "score": score, "is_bye": False, "result_str": game_text})
                        else:
                            games_played_details.append({"opponent_seeding_num": None, "opponent_rating": None, "player_color": "unknown", "score": 0.0, "is_bye": True, "result_str": game_text})

                    elif bye_or_forfeit_match:
                        score = 1.0 if game_text.strip() == '+' else 0.0
                        is_bye = game_text.strip() == '+'
                        games_played_details.append({"opponent_seeding_num": None, "opponent_rating": None, "player_color": "unknown", "score": score, "is_bye": is_bye, "result_str": game_text})

                    elif game_text and game_text.strip().lower() not in ['x', 'х']:
                        app_logger.warning(f"Не удалось распознать формат тура '{game_text}' для {player_name} в {tournament_url}")

                parsed_player_results.append({"place": final_place, "name": player_name, "player_id": player_id_fsr, "seeding_number": current_seeding_num, "points": str(points), "initial_rating": initial_rating, "avg_opponent_rating_fsr": avg_opponent_rating_val, "new_rating": new_rating_val if new_rating_val > 0 else ('—' if initial_rating == 0 and rating_change_val == 0 else initial_rating + rating_change_val), "rating_change": rating_change_val, "norm": norm_val, "games_played": games_played_details})
            except Exception as e:
                app_logger.error(f"Общая ошибка парсинга данных игрока ({player_name if 'player_name' in locals() else 'N/A'}, строка {row_idx+1}): {e}", exc_info=True)
        
        app_logger.info(f"Успешно спарсено {len(parsed_player_results)} детальных результатов для турнира {tournament_url}")
        return parsed_player_results
    except Exception as e:
        app_logger.error(f"Непредвиденная ошибка при парсинге результатов турнира {tournament_url}: {e}", exc_info=True)
        return []

def calculate_player_tournament_stats(player_data_list):
    if not player_data_list: return []
    for player in player_data_list:
        games = player.get("games_played", [])
        player["performance_rating"] = 0 
        player["white_score"] = 0.0
        player["white_games"] = 0
        player["black_score"] = 0.0
        player["black_games"] = 0
        if not games: continue
        rated_opponents_ratings = []
        score_against_rated_opponents = 0.0
        games_against_rated_opponents = 0
        for game in games:
            if game.get("is_bye"): continue
            if game.get("player_color") == "white":
                player["white_games"] += 1
                player["white_score"] += game.get("score", 0.0)
            elif game.get("player_color") == "black":
                player["black_games"] += 1
                player["black_score"] += game.get("score", 0.0)
            opponent_rating = game.get("opponent_rating")
            if opponent_rating is not None and opponent_rating > 0: 
                rated_opponents_ratings.append(opponent_rating)
                score_against_rated_opponents += game.get("score", 0.0)
                games_against_rated_opponents += 1
        if games_against_rated_opponents > 0:
            avg_opponent_rating_from_fsr = player.get("avg_opponent_rating_fsr", 0)
            if avg_opponent_rating_from_fsr > 0:
                current_avg_opp_rating = avg_opponent_rating_from_fsr
                app_logger.debug(f"Используем Rср={current_avg_opp_rating} от ФШР для {player.get('name')}")
            elif rated_opponents_ratings:
                current_avg_opp_rating = sum(rated_opponents_ratings) / games_against_rated_opponents
                app_logger.debug(f"Рассчитан Rср={current_avg_opp_rating} для {player.get('name')}")
            else: 
                current_avg_opp_rating = player.get("initial_rating", 1500) 
                app_logger.debug(f"Нет Rср и оцененных соперников для {player.get('name')}, используем {current_avg_opp_rating}")

            score_percentage = score_against_rated_opponents / games_against_rated_opponents
            dp = get_dp_for_performance(score_percentage)
            player["performance_rating"] = int(round(current_avg_opp_rating + dp))
        else:
            player["performance_rating"] = 0 
    return player_data_list

def generate_tournament_highlights(player_data_list_with_stats, all_players_from_db_dict_for_age):
    highlights = {"max_rating_gain_player": None, "highest_performance_player": None, "best_white_player": None, "best_black_player": None, "avg_tournament_rating": 0, "avg_participant_age": 0, "draw_percentage": 0.0, "youngest_player": None, "oldest_player": None, "top_3_finishers": [], "biggest_upset": None}
    if not player_data_list_with_stats: return highlights
    max_gain = -float('inf'); player_max_gain = None
    max_rp = -float('inf'); player_max_rp = None
    min_age_val = float('inf'); player_min_age = None
    max_age_val = -float('inf'); player_max_age = None
    total_initial_rating_sum = 0
    rated_participants_count_for_avg = 0
    total_age_sum = 0
    aged_participants_count_for_avg = 0
    total_draws_in_tournament = 0.0 
    total_games_count_for_draw_pct = 0.0 
    biggest_upset_diff = -1
    upset_details = None

    for p_data in player_data_list_with_stats:
        if p_data.get("initial_rating", 0) > 0:
            total_initial_rating_sum += p_data["initial_rating"]
            rated_participants_count_for_avg += 1
        
        player_fsr_id_str = str(p_data.get("player_id"))
        player_age = None
        if player_fsr_id_str and player_fsr_id_str in all_players_from_db_dict_for_age:
            birth_year = all_players_from_db_dict_for_age[player_fsr_id_str].get('birth_year')
            if birth_year:
                try:
                    player_age = datetime.now().year - int(birth_year)
                    total_age_sum += player_age
                    aged_participants_count_for_avg +=1
                    if player_age < min_age_val: min_age_val = player_age; player_min_age = {"name": p_data.get("name"), "age": player_age, "initial_rating": p_data.get("initial_rating")}
                    if player_age > max_age_val: max_age_val = player_age; player_max_age = {"name": p_data.get("name"), "age": player_age, "initial_rating": p_data.get("initial_rating")}
                except Exception as e:
                    app_logger.warning(f"Ошибка расчета возраста для игрока ID ФШР {player_fsr_id_str} с годом рождения {birth_year}: {e}")

        current_gain = p_data.get("rating_change", -float('inf'))
        if current_gain > max_gain :
            max_gain = current_gain
            player_max_gain = {"name": p_data.get("name"), "change": current_gain, "initial_rating": p_data.get("initial_rating")}
        
        current_rp = p_data.get("performance_rating", -float('inf'))
        if current_rp > max_rp:
            max_rp = current_rp
            player_max_rp = {"name": p_data.get("name"), "performance": current_rp, "initial_rating": p_data.get("initial_rating")}

        for game in p_data.get("games_played", []):
            if game.get("is_bye") or game.get("opponent_rating") is None: continue
            total_games_count_for_draw_pct += 0.5 
            if game.get("score") == 0.5:
                total_draws_in_tournament += 0.5 
            
            if game.get("score") == 1.0:
                player_initial_rating = p_data.get("initial_rating", 0)
                opponent_initial_rating = game.get("opponent_rating", 0)
                if player_initial_rating > 0 and opponent_initial_rating > 0 :
                    rating_diff = opponent_initial_rating - player_initial_rating
                    if rating_diff > biggest_upset_diff:
                        biggest_upset_diff = rating_diff
                        upset_details = {"upset_player_name": p_data.get("name"), "upset_player_rating": player_initial_rating, "defeated_opponent_seeding_num": game.get("opponent_seeding_num"), "defeated_opponent_rating": opponent_initial_rating, "rating_difference": rating_diff, "upset_player_gender": p_data.get("gender")}

    if player_max_gain: highlights["max_rating_gain_player"] = player_max_gain
    if player_max_rp: highlights["highest_performance_player"] = player_max_rp
    if player_min_age: highlights["youngest_player"] = player_min_age
    if player_max_age: highlights["oldest_player"] = player_max_age
    if rated_participants_count_for_avg > 0: highlights["avg_tournament_rating"] = round(total_initial_rating_sum / rated_participants_count_for_avg)
    if aged_participants_count_for_avg > 0: highlights["avg_participant_age"] = round(total_age_sum / aged_participants_count_for_avg)
    if total_games_count_for_draw_pct > 0 : highlights["draw_percentage"] = round((total_draws_in_tournament / total_games_count_for_draw_pct) * 100, 1)
    else: highlights["draw_percentage"] = 0.0
    if upset_details: highlights["biggest_upset"] = upset_details
    def sort_key_place(player):
        place_str = str(player.get("place", "9999"))
        match = re.match(r"(\d+)", place_str)
        return int(match.group(1)) if match else 9999
    sorted_by_place = sorted(player_data_list_with_stats, key=sort_key_place)
    highlights["top_3_finishers"] = [{"name": p.get("name"), "place": p.get("place"), "points": p.get("points"), "initial_rating": p.get("initial_rating")} for p in sorted_by_place[:3]]
    best_w_player = None; max_w_pct = -1.0
    for p in player_data_list_with_stats:
        if p.get("white_games", 0) >= 3:
            pct = p.get("white_score", 0) / p["white_games"]
            if pct > max_w_pct: max_w_pct = pct; best_w_player = p
            elif pct == max_w_pct and p.get("white_score",0) > (best_w_player.get("white_score",0) if best_w_player else -1): best_w_player = p
    if best_w_player: highlights["best_white_player"] = {"name": best_w_player.get("name"), "score": best_w_player.get("white_score"), "games": best_w_player.get("white_games"), "percentage": round(max_w_pct * 100, 1)}
    best_b_player = None; max_b_pct = -1.0
    for p in player_data_list_with_stats:
        if p.get("black_games", 0) >= 3:
            pct = p.get("black_score", 0) / p["black_games"]
            if pct > max_b_pct: max_b_pct = pct; best_b_player = p
            elif pct == max_b_pct and p.get("black_score",0) > (best_b_player.get("black_score",0) if best_b_player else -1): best_b_player = p
    if best_b_player: highlights["best_black_player"] = {"name": best_b_player.get("name"), "score": best_b_player.get("black_score"), "games": best_b_player.get("black_games"), "percentage": round(max_b_pct * 100, 1)}
    app_logger.info(f"DEBUG_HIGHLIGHTS: Финальный объект highlights для турнира ID {player_data_list_with_stats[0].get('tournament_id_debug_ref', 'N/A') if player_data_list_with_stats else 'N/A'}: {highlights}")
    return highlights

def update_ratings():
    app_logger.info(f"ЗАПУСК ОБНОВЛЕНИЯ ДАННЫХ ИГРОКОВ КБР (БД): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    initial_kbr_players = load_initial_players() 
    if not initial_kbr_players:
        app_logger.warning("Список игроков КБР (players_kbr.json) пуст. Обновление отменено.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    updated_count = 0
    db_players_current_state = {}
    try:
        cursor.execute("SELECT fsr_id, current_fsr_classic_rating, current_fsr_rapid_rating, current_fsr_blitz_rating FROM players")
        for row in cursor.fetchall():
            db_players_current_state[str(row['fsr_id'])] = {'current_fsr_classic_rating': row['current_fsr_classic_rating'], 'current_fsr_rapid_rating': row['current_fsr_rapid_rating'], 'current_fsr_blitz_rating': row['current_fsr_blitz_rating']}
    except sqlite3.Error as e:
        app_logger.error(f"Ошибка чтения текущих рейтингов из БД в update_ratings: {e}")
        conn.close()
        return

    for p_initial in initial_kbr_players:
        fsr_id_str = str(p_initial.get('Код ФШР'))
        if not fsr_id_str or not fsr_id_str.isdigit():
            app_logger.warning(f"update_ratings: Некорректный или отсутствующий 'Код ФШР' для {p_initial.get('ФИО')} в players_kbr.json. Пропуск.")
            continue
        
        fsr_id_int = int(fsr_id_str)
        scraped_data = scrape_individual_fsr_profile(fsr_id_int)

        if scraped_data:
            player_in_db = db_players_current_state.get(fsr_id_str)
            prev_classic = player_in_db['current_fsr_classic_rating'] if player_in_db and player_in_db.get('current_fsr_classic_rating') is not None else 0
            prev_rapid = player_in_db['current_fsr_rapid_rating'] if player_in_db and player_in_db.get('current_fsr_rapid_rating') is not None else 0
            prev_blitz = player_in_db['current_fsr_blitz_rating'] if player_in_db and player_in_db.get('current_fsr_blitz_rating') is not None else 0
            data_to_update_or_insert = {'fide_id': scraped_data.get('fide_id_fsr', p_initial.get('Код ФИДЕ')), 'full_name': scraped_data.get('name_fsr', p_initial.get('ФИО')), 'fsr_official_title': scraped_data.get('title_fsr'), 'current_fsr_classic_rating': scraped_data.get('rating', 0), 'previous_fsr_classic_rating': prev_classic, 'current_fsr_rapid_rating': scraped_data.get('rapid_rating', 0), 'previous_fsr_rapid_rating': prev_rapid, 'current_fsr_blitz_rating': scraped_data.get('blitz_rating', 0), 'previous_fsr_blitz_rating': prev_blitz, 'current_fide_classic_rating': scraped_data.get('fide_rating', 0), 'current_fide_rapid_rating': scraped_data.get('fide_rapid', 0), 'current_fide_blitz_rating': scraped_data.get('fide_blitz', 0), 'fsr_tournaments_played_count': scraped_data.get('tournamentsPlayed', 0), 'last_profile_update_at': datetime.now().isoformat()}
            
            if player_in_db:
                set_clause_parts = [f"{key} = ?" for key in data_to_update_or_insert.keys()]
                current_values = list(data_to_update_or_insert.values())
                sql_update = f"UPDATE players SET {', '.join(set_clause_parts)} WHERE fsr_id = ?"
                current_values.append(fsr_id_int)
                try:
                    cursor.execute(sql_update, tuple(current_values))
                    updated_count += 1
                except sqlite3.Error as e:
                    app_logger.error(f"Ошибка обновления игрока ID {fsr_id_int} в БД: {e}")
            else: 
                data_to_update_or_insert['fsr_id'] = fsr_id_int
                data_to_update_or_insert['birth_year'] = p_initial.get('Год рождения')
                data_to_update_or_insert['gender'] = 'female' if p_initial.get('Пол', 'М') == 'Ж' else 'male'
                data_to_update_or_insert['local_title'] = p_initial.get('Разряд')
                data_to_update_or_insert['is_classic_champion'] = 1 if p_initial.get('is_classic_champion', False) else 0
                data_to_update_or_insert['is_rapid_champion'] = 1 if p_initial.get('is_rapid_champion', False) else 0
                data_to_update_or_insert['is_blitz_champion'] = 1 if p_initial.get('is_blitz_champion', False) else 0
                data_to_update_or_insert['previous_fsr_rapid_rating'] = 0 
                data_to_update_or_insert['previous_fsr_blitz_rating'] = 0 
                current_year = datetime.now().year
                age_for_child_check = 0
                if data_to_update_or_insert['birth_year'] and str(data_to_update_or_insert['birth_year']).strip().isdigit():
                    birth_y = int(data_to_update_or_insert['birth_year'])
                    if 1900 <= birth_y <= current_year: age_for_child_check = current_year - birth_y
                data_to_update_or_insert['is_child'] = 1 if (age_for_child_check > 0 and age_for_child_check <= 18) else 0
                cols_for_insert = list(data_to_update_or_insert.keys())
                vals_for_insert = [data_to_update_or_insert[k] for k in cols_for_insert]
                placeholders = ', '.join(['?'] * len(cols_for_insert))
                sql_insert = f"INSERT INTO players ({', '.join(cols_for_insert)}) VALUES ({placeholders})"
                try:
                    cursor.execute(sql_insert, tuple(vals_for_insert))
                    updated_count+=1
                except sqlite3.Error as e:
                    app_logger.error(f"Ошибка вставки нового игрока ID {fsr_id_int} в БД при обновлении: {e}")
        else:
            app_logger.warning(f"Не удалось получить данные с ФШР для игрока ID {fsr_id_int} ({p_initial.get('ФИО')})")

    conn.commit()
    conn.close()
    app_logger.info(f"Обновление рейтингов игроков в БД завершено. Затронуто записей: {updated_count}")

def load_players():
    app_logger.info("Загрузка игроков из базы данных SQLite...")
    conn = get_db_connection() 
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT fsr_id, fide_id, full_name, birth_year, gender, local_title, fsr_official_title, is_classic_champion, is_rapid_champion, is_blitz_champion, is_child, current_fsr_classic_rating, previous_fsr_classic_rating, current_fsr_rapid_rating, previous_fsr_rapid_rating, current_fsr_blitz_rating, previous_fsr_blitz_rating, current_fide_classic_rating, current_fide_rapid_rating, current_fide_blitz_rating, fsr_tournaments_played_count, last_profile_update_at FROM players")
        db_players = cursor.fetchall() 
    except sqlite3.Error as e:
        app_logger.error(f"Ошибка чтения игроков из БД: {e}", exc_info=True)
        db_players = [] 
    finally:
        conn.close()

    transformed_players = []
    current_year = datetime.now().year

    for p_db in db_players: 
        try:
            age_val_str = '—'
            age_for_child_check = 0 
            if p_db['birth_year']: 
                try:
                    birth_year_int = int(p_db['birth_year'])
                    if 1900 <= birth_year_int <= current_year:
                        age_num = current_year - birth_year_int
                        age_val_str = str(age_num)
                        age_for_child_check = age_num
                except (ValueError, TypeError):
                    app_logger.warning(f"Некорректный год рождения для игрока ID {p_db['fsr_id']}: {p_db['birth_year']}")
            
            is_child_bool = bool(p_db['is_child']) if p_db['is_child'] is not None else (age_for_child_check > 0 and age_for_child_check <= 18)

            def calculate_change(current, previous):
                current_val = current if current is not None else 0
                previous_val = previous if previous is not None else 0
                try:
                    current_r_str = str(current_val)
                    prev_r_str = str(previous_val)
                    current_r = int(current_r_str) if current_r_str.strip().lstrip('-+').isdigit() else 0
                    prev_r = int(prev_r_str) if prev_r_str.strip().lstrip('-+').isdigit() else 0
                    return current_r - prev_r
                except (ValueError, TypeError):
                    return 0
            
            change_classic_val = calculate_change(p_db['current_fsr_classic_rating'], p_db['previous_fsr_classic_rating'])
            change_rapid_val = calculate_change(p_db['current_fsr_rapid_rating'], p_db['previous_fsr_rapid_rating'])
            change_blitz_val = calculate_change(p_db['current_fsr_blitz_rating'], p_db['previous_fsr_blitz_rating'])
            
            title_display = p_db['local_title']
            if not title_display and p_db['fsr_official_title']:
                title_display = p_db['fsr_official_title']
            if not title_display:
                title_display = '—'

            player_data = {'id': str(p_db['fsr_id']), 'fide_id': str(p_db['fide_id']) if p_db['fide_id'] else '—', 'name': p_db['full_name'], 'rating': str(p_db['current_fsr_classic_rating'] if p_db['current_fsr_classic_rating'] !=0 else '—'), 'rapid_rating': str(p_db['current_fsr_rapid_rating'] if p_db['current_fsr_rapid_rating'] !=0 else '—'), 'blitz_rating': str(p_db['current_fsr_blitz_rating'] if p_db['current_fsr_blitz_rating'] !=0 else '—'), 'fide_rating': str(p_db['current_fide_classic_rating'] if p_db['current_fide_classic_rating'] !=0 else '—'), 'fide_rapid': str(p_db['current_fide_rapid_rating'] if p_db['current_fide_rapid_rating'] !=0 else '—'), 'fide_blitz': str(p_db['current_fide_blitz_rating'] if p_db['current_fide_blitz_rating'] !=0 else '—'), 'age': age_val_str, 'gender': p_db['gender'], 'isChild': is_child_bool, 'change_classic_value': change_classic_val, 'change_rapid_value': change_rapid_val, 'change_blitz_value': change_blitz_val, 'tournamentsPlayed': p_db['fsr_tournaments_played_count'] if p_db['fsr_tournaments_played_count'] is not None else 0, 'title': title_display, 'is_classic_champion': bool(p_db['is_classic_champion']), 'is_rapid_champion': bool(p_db['is_rapid_champion']), 'is_blitz_champion': bool(p_db['is_blitz_champion'])}
            transformed_players.append(player_data)
        except Exception as e:
            app_logger.error(f"Ошибка обработки игрока из БД с fsr_id {p_db['fsr_id'] if p_db else 'UNKNOWN'}: {e}", exc_info=True)
            
    app_logger.info(f"Функция load_players (из БД) вернула {len(transformed_players)} игроков с новыми полями изменений")
    return transformed_players

@app.route('/')
def index():
    return render_template('index.html', theme='theme-art') 

@app.route('/api/players')
def get_players_api():
    try:
        players_data = load_players()
        return jsonify(players_data)
    except Exception as e:
        app_logger.error(f"Ошибка в /api/players: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/tournaments')
def get_tournaments_api():
    try:
        all_tournaments = load_tournaments()
        # Проходим по каждому турниру, чтобы добавить ему "звездный" рейтинг
        for t in all_tournaments:
            # Если у турнира есть результаты, мы можем посчитать его "звездность"
            if "results" in t and len(t.get("results", [])) > 0:
                # ВЫЗЫВАЕМ ВАШУ СУЩЕСТВУЮЩУЮ ФУНКЦИЮ
                t['tier'] = get_tournament_tier(t) 
            else:
                # Если результатов нет, даем 1 звезду по умолчанию
                t['tier'] = 1
        
        return jsonify(all_tournaments)
    except Exception as e:
        app_logger.error(f"Ошибка в /api/tournaments: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/tournament/<int:tournament_id>')
def get_tournament_results_api(tournament_id):
    tournaments_data = load_tournaments()
    tournament_to_return = None
    tournament_index_found = -1

    for i, t_info in enumerate(tournaments_data):
        if t_info.get('id') == tournament_id:
            tournament_to_return = t_info
            tournament_index_found = i
            break
    
    if tournament_to_return:
        results_are_detailed_and_calculated = False
        if tournament_to_return.get('results') and len(tournament_to_return.get('results', [])) > 0:
            first_result = tournament_to_return['results'][0]
            if 'games_played' in first_result and 'performance_rating' in first_result and 'highlights' in tournament_to_return:
                results_are_detailed_and_calculated = True
                app_logger.info(f"Найдены детальные результаты и хайлайты в кэше для турнира ID {tournament_id}")

        if not results_are_detailed_and_calculated:
            app_logger.info(f"Детальные результаты/статистика для турнира ID {tournament_id} ('{tournament_to_return.get('name')}') отсутствуют или не полны. Запускаем парсер и расчет...")
            tournament_link = tournament_to_return.get('fsr_link')
            if tournament_link:
                scraped_results_raw = scrape_tournament_results(tournament_link) 
                
                if scraped_results_raw:
                    conn_players = get_db_connection()
                    cursor_players = conn_players.cursor()
                    cursor_players.execute("SELECT fsr_id, birth_year, gender FROM players")
                    all_db_players_info = {str(row['fsr_id']): {'birth_year': row['birth_year'], 'gender': row['gender']} for row in cursor_players.fetchall()}
                    conn_players.close()
                    
                    current_year_for_age_calc = datetime.now().year
                    for res_player in scraped_results_raw:
                        player_main_db_info = all_db_players_info.get(str(res_player.get("player_id")))
                        if player_main_db_info:
                            res_player['gender'] = player_main_db_info.get('gender')
                            if player_main_db_info.get('birth_year'):
                                try:
                                    birth_year = int(player_main_db_info['birth_year'])
                                    if 1900 <= birth_year <= current_year_for_age_calc:
                                        res_player['age_val_num'] = current_year_for_age_calc - birth_year
                                    else:
                                        res_player['age_val_num'] = None
                                except (ValueError, TypeError):
                                    res_player['age_val_num'] = None
                            else:
                                res_player['age_val_num'] = None
                        else:
                            res_player['gender'] = None
                            res_player['age_val_num'] = None
                        res_player['tournament_id_debug_ref'] = tournament_to_return.get('id')

                    results_with_stats = calculate_player_tournament_stats(scraped_results_raw)
                    tournament_highlights = generate_tournament_highlights(results_with_stats, all_db_players_info) 
                    
                    tournaments_data[tournament_index_found]['results'] = results_with_stats
                    tournaments_data[tournament_index_found]['highlights'] = tournament_highlights
                    
                    # Переприсваиваем обновленные данные для возврата
                    tournament_to_return = tournaments_data[tournament_index_found]
                    
                    save_tournaments(tournaments_data) 
                    app_logger.info(f"Детальные результаты и статистика для турнира ID {tournament_id} спарсены, рассчитаны и сохранены.")
                else: 
                    app_logger.warning(f"Парсер не вернул результатов для турнира ID {tournament_id} по ссылке {tournament_link}.")
                    tournament_to_return['results'] = [] 
                    tournament_to_return['highlights'] = generate_tournament_highlights([], {}) 

        # ✅ ИСПРАВЛЕНИЕ ЗДЕСЬ:
        # Убедимся, что у турнира есть "звездность" перед отправкой на фронтенд.
        # Это сработает и для данных из кэша, и для только что спарсенных.
        tournament_to_return['tier'] = get_tournament_tier(tournament_to_return)

        return jsonify(tournament_to_return)
    else: 
        return jsonify({"error": "Tournament not found"}), 404

@app.route('/api/compare')
def compare_players_api():
    player1_id = request.args.get('player1_id')
    player2_id = request.args.get('player2_id')

    if not player1_id or not player2_id:
        return jsonify({"error": "Требуется указать ID обоих игроков"}), 400

    # --- НАЧАЛО ИЗМЕНЕНИЯ ---
    # Загружаем данные о достижениях, чтобы взять оттуда сырые очки
    try:
        with open(ACHIEVERS_FILE, 'r', encoding='utf-8') as f:
            all_achievers = json.load(f)
        # Превращаем список в словарь для быстрого поиска
        achievers_map = {str(p['id']): p for p in all_achievers}
    except (FileNotFoundError, json.JSONDecodeError):
        achievers_map = {}
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    players_data_list = load_players()
    players_data_map = {p['id']: p for p in players_data_list}
    player1_profile = players_data_map.get(player1_id)
    player2_profile = players_data_map.get(player2_id)

    if not player1_profile or not player2_profile:
        return jsonify({"error": "Один или оба игрока не найдены в базе данных"}), 404

    # Добавляем сырые очки в профили игроков
    player1_achievements = achievers_map.get(player1_id, {})
    player2_achievements = achievers_map.get(player2_id, {})
    player1_profile['raw_points'] = player1_achievements.get('raw_points', 0)
    player2_profile['raw_points'] = player2_achievements.get('raw_points', 0)

    # ... (остальная часть функции без изменений: подсчет личных встреч, медалей и т.д.) ...
    head_to_head = {"player1_wins": 0, "player2_wins": 0, "draws": 0}
    prizes_player1 = {"gold": 0, "silver": 0, "bronze": 0}
    prizes_player2 = {"gold": 0, "silver": 0, "bronze": 0}
    all_tournaments = load_tournaments()
    for tournament in all_tournaments:
        results = tournament.get("results", [])
        if not results: continue

        p1_in_tournament = any(str(p.get("player_id")) == player1_id for p in results)
        p2_in_tournament = any(str(p.get("player_id")) == player2_id for p in results)

        if p1_in_tournament and p2_in_tournament:
            fsr_id_to_seeding_num = {str(p.get("player_id")): p.get("seeding_number") for p in results if p.get("player_id")}
            player1_seeding_num = fsr_id_to_seeding_num.get(player1_id)
            player2_seeding_num = fsr_id_to_seeding_num.get(player2_id)
            if player1_seeding_num and player2_seeding_num:
                for p_res in results:
                    if str(p_res.get("player_id")) == player1_id:
                        for game in p_res.get("games_played", []):
                            if game.get("opponent_seeding_num") == player2_seeding_num:
                                score = game.get("score", 0.0)
                                if score == 1.0: head_to_head["player1_wins"] += 1
                                elif score == 0.0: head_to_head["player2_wins"] += 1
                                else: head_to_head["draws"] += 1

        for p_res in results:
            place_str = str(p_res.get("place", "0")).strip()
            current_player_id = str(p_res.get("player_id"))
            if place_str == "1":
                if current_player_id == player1_id: prizes_player1["gold"] += 1
                elif current_player_id == player2_id: prizes_player2["gold"] += 1
            elif place_str == "2":
                if current_player_id == player1_id: prizes_player1["silver"] += 1
                elif current_player_id == player2_id: prizes_player2["silver"] += 1
            elif place_str == "3":
                if current_player_id == player1_id: prizes_player1["bronze"] += 1
                elif current_player_id == player2_id: prizes_player2["bronze"] += 1

    def calculate_overall(player_profile):
        classic_r = int(player_profile['rating']) if str(player_profile['rating']).isdigit() else 0
        rapid_r = int(player_profile['rapid_rating']) if str(player_profile['rapid_rating']).isdigit() else 0
        blitz_r = int(player_profile['blitz_rating']) if str(player_profile['blitz_rating']).isdigit() else 0
        if not any([classic_r, rapid_r, blitz_r]): return 0
        if classic_r == 0: classic_r = (rapid_r + blitz_r) / 2 if rapid_r or blitz_r else 0
        if rapid_r == 0: rapid_r = (classic_r + blitz_r) / 2 if classic_r or blitz_r else 0
        if blitz_r == 0: blitz_r = (classic_r + rapid_r) / 2 if classic_r or rapid_r else 0
        overall = (classic_r * 0.5) + (rapid_r * 0.3) + (blitz_r * 0.2)
        return round(overall)

    player1_profile['overall_rating'] = calculate_overall(player1_profile)
    player2_profile['overall_rating'] = calculate_overall(player2_profile)
    player1_profile['achievements_score'] = (prizes_player1["gold"] * 3) + (prizes_player1["silver"] * 2) + (prizes_player1["bronze"] * 1)
    player2_profile['achievements_score'] = (prizes_player2["gold"] * 3) + (prizes_player2["silver"] * 2) + (prizes_player2["bronze"] * 1)

    return jsonify({"player1": player1_profile, "player2": player2_profile, "head_to_head": head_to_head, "prizes_player1": prizes_player1, "prizes_player2": prizes_player2})
# ✅ НАЧАЛО: НОВЫЙ МАРШРУТ ДЛЯ ТОП-10 ИГРОКОВ
# ✅ НАЧАЛО: ИСПРАВЛЕННАЯ ВЕРСИЯ ТОП-10
# ✅ НАЧАЛО: НОВЫЙ МАРШРУТ ДЛЯ ТОП-10 С ВЗВЕШЕННЫМИ ОЧКАМИ
@app.route('/api/top-achievers')
def get_top_achievers():
    try:
        if not os.path.exists(ACHIEVERS_FILE):
            # Если файла нет, на всякий случай запускаем расчет
            calculate_and_save_achievers_ranking()
        
        with open(ACHIEVERS_FILE, 'r', encoding='utf-8') as f:
            all_achievers = json.load(f)
        
        # Отдаем только первые 10
        return jsonify(all_achievers[:10])
    except Exception as e:
        app_logger.error(f"Ошибка в /api/top-achievers: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    except Exception as e:
        app_logger.error(f"Ошибка в /api/top-achievers: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Добавьте это в начало файла, где у вас определены другие константы
ACHIEVERS_FILE = os.path.join(BASE_DIR, 'achievers_ranking.json')

@app.route('/api/past-champions')
def get_past_champions():
    try:
        if not os.path.exists(PAST_CHAMPIONS_FILE):
            return jsonify([]) # Возвращаем пустой список, если файл не найден

        with open(PAST_CHAMPIONS_FILE, 'r', encoding='utf-8') as f:
            past_champions = json.load(f)

        return jsonify(past_champions)
    except Exception as e:
        app_logger.error(f"Ошибка в /api/past-champions: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/all-achievers')
def get_all_achievers():
    try:
        if not os.path.exists(ACHIEVERS_FILE):
            return jsonify([]) # Возвращаем пустой список, если файл еще не создан
        
        with open(ACHIEVERS_FILE, 'r', encoding='utf-8') as f:
            all_achievers = json.load(f)
        
        return jsonify(all_achievers)
    except Exception as e:
        app_logger.error(f"Ошибка в /api/all-achievers: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Эту функцию можно добавить после функции get_top_achievers
# ЗАМЕНИТЕ ВАШУ СТАРУЮ ФУНКЦИЮ calculate_and_save_achievers_ranking НА ЭТУ
def calculate_and_save_achievers_ranking():
    """
    Рассчитывает полный рейтинг достижений всех игроков и сохраняет его в JSON-файл.
    Теперь считает и "сырые" очки, и "зачетные" (взвешенные).
    """
    app_logger.info("Начало полного пересчета рейтинга достижений...")
    try:
        tournaments = load_tournaments()
        players_list = load_players()
        players_map = {p['id']: p['name'] for p in players_list}
        player_stats = {}

        # Коэффициенты, основанные на силе ("звездности") турнира
        points_multiplier_by_tier = {
            5: 2.5, # 5 звезд
            4: 2.0, # 4 звезды
            3: 1.5, # 3 звезды
            2: 1.2, # 2 звезды
            1: 1.0  # 1 звезда
        }

        for tournament in tournaments:
            results = tournament.get("results", [])
            if not results: continue

            tier = get_tournament_tier(tournament)
            multiplier = points_multiplier_by_tier.get(tier, 1.0)

            for res in results:
                player_id = str(res.get("player_id"))
                if not player_id or player_id not in players_map: continue

                # Инициализируем статистику для нового игрока
                if player_id not in player_stats:
                    full_name = players_map.get(player_id, "Неизвестный игрок")
                    player_stats[player_id] = {
                        'id': player_id, 
                        'name': full_name, 
                        'gold': 0, 'silver': 0, 'bronze': 0, 
                        'points': 0.0, # Здесь будут взвешенные очки
                        'raw_points': 0.0 # Здесь будут "сырые" очки
                    }

                # Суммируем "сырые" очки
                try:
                    game_points = float(res.get("points", 0))
                    player_stats[player_id]['raw_points'] += game_points
                except (ValueError, TypeError):
                    pass # Игнорируем, если очки - не число

                # Суммируем "взвешенные" очки
                player_stats[player_id]['points'] += (game_points * multiplier)

                # Считаем медали, как и раньше
                place = str(res.get("place", "0")).strip()
                if place == "1":
                    player_stats[player_id]['gold'] += 1
                elif place == "2":
                    player_stats[player_id]['silver'] += 1
                elif place == "3":
                    player_stats[player_id]['bronze'] += 1

        # Округляем очки до 2 знаков после запятой
        for stats in player_stats.values():
            stats['points'] = round(stats['points'], 2)
            stats['raw_points'] = round(stats['raw_points'], 2)

        achievers_list = list(player_stats.values())
        # Сортируем по взвешенным очкам, затем по золоту, серебру, бронзе
        sorted_achievers = sorted(
            achievers_list, 
            key=lambda p: (p['points'], p['gold'], p['silver'], p['bronze']), 
            reverse=True
        )

        with open(ACHIEVERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted_achievers, f, ensure_ascii=False, indent=4)

        app_logger.info(f"Рейтинг достижений успешно рассчитан и сохранен в {ACHIEVERS_FILE}. Всего игроков: {len(sorted_achievers)}")

    except Exception as e:
        app_logger.error(f"Ошибка при расчете и сохранении рейтинга достижений: {e}", exc_info=True)
def record_successful_update():
    try:
        with open(LAST_UPDATE_TS_FILE, 'w') as f: f.write(datetime.now().isoformat())
        app_logger.info(f"Время последнего успешного полного обновления записано в {LAST_UPDATE_TS_FILE}")
    except Exception as e: app_logger.error(f"Ошибка записи времени последнего обновления в {LAST_UPDATE_TS_FILE}: {e}")

def should_run_initial_full_update():
    if not os.path.exists(LAST_UPDATE_TS_FILE):
        app_logger.info(f"Файл {LAST_UPDATE_TS_FILE} не найден. Требуется первоначальное полное обновление.")
        return True
    try:
        with open(LAST_UPDATE_TS_FILE, 'r') as f: last_update_str = f.read().strip()
        if not last_update_str:
            app_logger.info(f"Файл {LAST_UPDATE_TS_FILE} пуст. Требуется первоначальное полное обновление.")
            return True
        last_update_dt = datetime.fromisoformat(last_update_str)
        if datetime.now() - last_update_dt > timedelta(hours=23):
            app_logger.info(f"Прошло более 23 часов с последнего полного обновления ({last_update_dt}). Требуется обновление.")
            return True
        app_logger.info(f"Полное обновление при старте не требуется. Последнее было: {last_update_dt}.")
        return False
    except Exception as e:
        app_logger.error(f"Ошибка чтения/обработки времени из {LAST_UPDATE_TS_FILE}: {e}. Запускаем обновление для безопасности.")
        return True 

def scheduled_update_ratings_task_wrapper():
    app_logger.info("Плановый запуск update_ratings...")
    try:
        update_ratings()
        app_logger.info("Плановый запуск update_ratings успешно завершен.")
    except Exception as e:
        app_logger.error(f"Ошибка в плановом запуске update_ratings: {e}", exc_info=True)

def scheduled_update_tournaments_task_wrapper():
    app_logger.info("Плановый запуск update_tournaments_from_fsr...")
    try:
        update_tournaments_from_fsr()
        app_logger.info("Плановый запуск update_tournaments_from_fsr успешно завершен.")
    except Exception as e:
        app_logger.error(f"Ошибка в плановом запуске update_tournaments_from_fsr: {e}", exc_info=True)

def run_scheduler():
    app_logger.info("Планировщик запущен.")
    schedule.every().day.at("07:00").do(scheduled_update_tournaments_task_wrapper) 
    schedule.every().day.at("07:10").do(scheduled_update_ratings_task_wrapper) 
    schedule.every().day.at("07:40").do(record_successful_update) 
    schedule.every().day.at("07:20").do(calculate_and_save_achievers_ranking)
    schedule.every().day.at("07:40").do(record_successful_update)
    def initial_run():
        time.sleep(10) 
        if should_run_initial_full_update():
            app_logger.info("Запускаем первоначальный/устаревший полный набор фоновых задач...")
            all_tasks_successful = True
            try:
                update_tournaments_from_fsr()
            except Exception as e:
                all_tasks_successful = False
                app_logger.error(f"Ошибка при первоначальном запуске update_tournaments_from_fsr: {e}", exc_info=True)
            
            time.sleep(5) 
            
            try:
                update_ratings()
            except Exception as e:
                all_tasks_successful = False
                app_logger.error(f"Ошибка при первоначальном запуске update_ratings: {e}", exc_info=True)
            
            if all_tasks_successful:
                app_logger.info("Первоначальный/устаревший полный набор фоновых задач УСПЕШНО завершен.")
                record_successful_update()
            else:
                app_logger.warning("Первоначальный/устаревший полный набор фоновых задач завершен С ОШИБКАМИ. Метка времени не обновлена.")
        else:
            app_logger.info("Пропуск первоначального/устаревшего полного обновления данных (данные актуальны).")

    initial_thread = threading.Thread(target=initial_run)
    initial_thread.start()

    while True:
        schedule.run_pending()
        time.sleep(60) 

if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app_logger.info(f"Flask приложение запускается на host 0.0.0.0, port {port}")
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
    