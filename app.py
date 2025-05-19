from flask import Flask, render_template, jsonify
import json
import os
import requests
from bs4 import BeautifulSoup
import schedule
import time
import threading
from datetime import datetime
import logging

app = Flask(__name__)

# Настройка логирования для приложения
app_logger = logging.getLogger('ChessRatingsLive')
app_logger.setLevel(logging.INFO)
handler = logging.FileHandler('update.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app_logger.addHandler(handler)

# Отключаем стандартный логгер Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Путь к файлам
JSON_FILE = os.path.join(os.path.dirname(__file__), 'players_kbr.json')
RATINGS_FILE = os.path.join(os.path.dirname(__file__), 'ratings_history.json')

def load_initial_players():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            players = json.load(f)
        app_logger.info("Успешно загружены начальные данные из {}".format(JSON_FILE))
        return players
    except FileNotFoundError:
        app_logger.error("Файл {} не найден".format(JSON_FILE))
        return []
    except json.JSONDecodeError:
        app_logger.error("Неверный формат JSON в файле {}".format(JSON_FILE))
        return []

def load_ratings_history():
    if not os.path.exists(RATINGS_FILE):
        with open(RATINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        app_logger.info("Создан новый файл {}".format(RATINGS_FILE))
        return []

    try:
        with open(RATINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ratings_history = []
        for player in data:
            if isinstance(player, dict) and 'id' in player:
                ratings_history.append(player)
            else:
                app_logger.warning("Пропущена некорректная запись в ratings_history: {}".format(player))
        app_logger.info("Успешно загружены данные из {}".format(RATINGS_FILE))
        return ratings_history
    except json.JSONDecodeError:
        app_logger.error("Неверный формат JSON в файле {}".format(RATINGS_FILE))
        return []

def save_ratings_history(ratings):
    try:
        with open(RATINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(ratings, f, ensure_ascii=False, indent=4)
        app_logger.info("Данные успешно сохранены в {}".format(RATINGS_FILE))
    except Exception as e:
        app_logger.error("Ошибка при сохранении данных в {}: {}".format(RATINGS_FILE, e))

def fetch_fshr_ratings(game_type):
    url_map = {
        'classic': 'https://ratings.ruchess.ru/people?game_type=classic',
        'rapid': 'https://ratings.ruchess.ru/people?game_type=rapid',
        'blitz': 'https://ratings.ruchess.ru/people?game_type=blitz'
    }
    url = url_map.get(game_type)
    if not url:
        app_logger.error(f"Неверный тип игры: {game_type}")
        return []

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        players_data = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Пропускаем заголовок
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 8:  # Ожидаем, что таблица содержит все рейтинги
                    player_id = int(cols[0].text.strip())
                    name = cols[1].text.strip()
                    rating = int(cols[2].text.strip()) if cols[2].text.strip().isdigit() else 0
                    fide_rating = int(cols[5].text.strip()) if cols[5].text.strip().isdigit() else 0
                    if game_type == 'classic':
                        players_data.append({
                            'id': player_id,
                            'name': name,
                            'rating': rating,
                            'fide_rating': fide_rating
                        })
                    elif game_type == 'rapid':
                        players_data.append({
                            'id': player_id,
                            'name': name,
                            'rapid_rating': rating,
                            'fide_rapid': fide_rating
                        })
                    elif game_type == 'blitz':
                        players_data.append({
                            'id': player_id,
                            'name': name,
                            'blitz_rating': rating,
                            'fide_blitz': fide_rating
                        })
        app_logger.info(f"Успешно загружены данные с сайта ФШР ({game_type}): {len(players_data)} игроков")
        return players_data
    except Exception as e:
        app_logger.error(f"Ошибка при загрузке данных с ФШР ({game_type}): {e}")
        return []

def update_ratings():
    app_logger.info("Начало обновления данных: {}".format(datetime.now()))

    # Парсим все типы рейтингов
    fshr_classic = fetch_fshr_ratings('classic')
    fshr_rapid = fetch_fshr_ratings('rapid')
    fshr_blitz = fetch_fshr_ratings('blitz')

    if not (fshr_classic or fshr_rapid or fshr_blitz):
        app_logger.warning("Не удалось загрузить данные с ФШР")
        return

    ratings_history = load_ratings_history()
    ratings_dict = {player['id']: player for player in ratings_history}

    # Обновляем ФШР Классика и FIDE Standard
    for player in fshr_classic:
        player_id = player['id']
        new_rating = player['rating']
        new_fide_rating = player['fide_rating']
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if player_id in ratings_dict:
            last_rating = ratings_dict[player_id].get('rating', new_rating)
            last_fide_rating = ratings_dict[player_id].get('fide_rating', new_fide_rating)
            ratings_dict[player_id].update({
                'rating': new_rating,
                'fide_rating': new_fide_rating,
                'last_rating': last_rating,
                'last_fide_rating': last_fide_rating,
                'last_updated': current_time
            })
            app_logger.info(f"Обновлен рейтинг игрока {player_id}: ФШР Классика {last_rating} -> {new_rating}, FIDE Standard {last_fide_rating} -> {new_fide_rating}")
        else:
            ratings_dict[player_id] = {
                'id': player_id,
                'name': player['name'],
                'rating': new_rating,
                'fide_rating': new_fide_rating,
                'last_rating': new_rating,
                'last_fide_rating': new_fide_rating,
                'last_updated': current_time,
                'rapid_rating': 0,
                'fide_rapid': 0,
                'blitz_rating': 0,
                'fide_blitz': 0
            }
            app_logger.info(f"Добавлен новый игрок {player_id} с рейтингом ФШР Классика {new_rating}, FIDE Standard {new_fide_rating}")

    # Обновляем ФШР Быстрые и FIDE Rapid
    for player in fshr_rapid:
        player_id = player['id']
        new_rapid_rating = player['rapid_rating']
        new_fide_rapid = player['fide_rapid']
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if player_id in ratings_dict:
            ratings_dict[player_id].update({
                'rapid_rating': new_rapid_rating,
                'fide_rapid': new_fide_rapid,
                'last_updated': current_time
            })
            app_logger.info(f"Обновлен рейтинг игрока {player_id}: ФШР Быстрые -> {new_rapid_rating}, FIDE Rapid -> {new_fide_rapid}")
        else:
            ratings_dict[player_id] = {
                'id': player_id,
                'name': player['name'],
                'rating': 0,
                'fide_rating': 0,
                'rapid_rating': new_rapid_rating,
                'fide_rapid': new_fide_rapid,
                'blitz_rating': 0,
                'fide_blitz': 0,
                'last_updated': current_time
            }
            app_logger.info(f"Добавлен новый игрок {player_id} с рейтингом ФШР Быстрые {new_rapid_rating}, FIDE Rapid {new_fide_rapid}")

    # Обновляем ФШР Блиц и FIDE Blitz
    for player in fshr_blitz:
        player_id = player['id']
        new_blitz_rating = player['blitz_rating']
        new_fide_blitz = player['fide_blitz']
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if player_id in ratings_dict:
            ratings_dict[player_id].update({
                'blitz_rating': new_blitz_rating,
                'fide_blitz': new_fide_blitz,
                'last_updated': current_time
            })
            app_logger.info(f"Обновлен рейтинг игрока {player_id}: ФШР Блиц -> {new_blitz_rating}, FIDE Blitz -> {new_fide_blitz}")
        else:
            ratings_dict[player_id] = {
                'id': player_id,
                'name': player['name'],
                'rating': 0,
                'fide_rating': 0,
                'rapid_rating': 0,
                'fide_rapid': 0,
                'blitz_rating': new_blitz_rating,
                'fide_blitz': new_fide_blitz,
                'last_updated': current_time
            }
            app_logger.info(f"Добавлен новый игрок {player_id} с рейтингом ФШР Блиц {new_blitz_rating}, FIDE Blitz {new_fide_blitz}")

    updated_ratings = list(ratings_dict.values())
    save_ratings_history(updated_ratings)
    app_logger.info("Обновление данных завершено")

def load_players():
    json_players = load_initial_players()
    ratings_history = load_ratings_history()
    ratings_dict = {player['id']: player for player in ratings_history}

    transformed_players = []
    for player in json_players:
        try:
            birth_year = player.get('Год рождения', 2000)
            if birth_year is None:
                app_logger.warning("Год рождения отсутствует для игрока {}".format(player.get('ФИО', 'Неизвестный')))
                birth_year = 2000
            try:
                if isinstance(birth_year, (int, float)):
                    birth_year = int(birth_year)
                elif isinstance(birth_year, str) and birth_year.strip() and birth_year.isdigit():
                    birth_year = int(birth_year)
                else:
                    app_logger.warning("Некорректный Год рождения для игрока {}: {}".format(
                        player.get('ФИО', 'Неизвестный'), birth_year))
                    birth_year = 2000
            except (ValueError, TypeError):
                app_logger.warning("Некорректный Год рождения для игрока {}: {}".format(
                    player.get('ФИО', 'Неизвестный'), birth_year))
                birth_year = 2000
            age = 2025 - birth_year

            player_id = player.get('Код ФШР', 0)
            if not isinstance(player_id, (int, float)):
                player_id = 0

            rating_data = ratings_dict.get(player_id, {})
            rating = rating_data.get('rating', player.get('ФШР клс', '—'))
            rapid_rating = rating_data.get('rapid_rating', player.get('ФШР быс', '—'))
            blitz_rating = rating_data.get('blitz_rating', player.get('ФШР блиц', '—'))
            fide_rating = rating_data.get('fide_rating', player.get('ФИДЕ клс', '—'))
            fide_rapid = rating_data.get('fide_rapid', player.get('ФИДЕ быс', '—'))
            fide_blitz = rating_data.get('fide_blitz', player.get('ФИДЕ блиц', '—'))

            last_rating = rating_data.get('last_rating', rating)
            rating = str(rating) if rating is not None else '—'
            rapid_rating = str(rapid_rating) if rapid_rating is not None else '—'
            blitz_rating = str(blitz_rating) if blitz_rating is not None else '—'
            fide_rating = str(fide_rating) if fide_rating is not None else '—'
            fide_rapid = str(fide_rapid) if fide_rapid is not None else '—'
            fide_blitz = str(fide_blitz) if fide_blitz is not None else '—'
            last_rating = str(last_rating) if last_rating is not None else rating

            try:
                rating_int = int(rating) if rating.isdigit() else 0
                last_rating_int = int(last_rating) if last_rating.isdigit() else 0
                change_value = rating_int - last_rating_int
                change = f"+{change_value}" if change_value > 0 else str(change_value)
            except Exception as e:
                app_logger.error("Ошибка вычисления change для игрока {}: {}".format(player_id, e))
                change = "0"

            transformed_player = {
                'id': player_id,
                'fide_id': player.get('Код ФИДЕ', 0) if isinstance(player.get('Код ФИДЕ', 0), (int, float)) else 0,
                'name': str(player.get('ФИО', 'Не указано')),
                'rating': rating,
                'fide_rating': fide_rating,
                'rapid_rating': rapid_rating,
                'fide_rapid': fide_rapid,
                'blitz_rating': blitz_rating,
                'fide_blitz': fide_blitz,
                'age': age,
                'gender': 'female' if player.get('Пол', 'М') == 'Ж' else 'male',
                'isChild': age <= 18,
                'change': change,
                'online': player.get('online', False) if isinstance(player.get('online'), bool) else False,
                'tournamentsPlayed': player.get('tournamentsPlayed', 0) if isinstance(player.get('tournamentsPlayed', 0), int) else 0,
                'bestResult': str(player.get('bestResult', '—')),
                'lastTournaments': player.get('lastTournaments', []) if isinstance(player.get('lastTournaments', []), list) else [],
                'title': str(player.get('Разряд', '')) if player.get('Разряд') is not None else '',
                'is_classic_champion': player.get('is_classic_champion', False),
                'is_rapid_champion': player.get('is_rapid_champion', False),
                'is_blitz_champion': player.get('is_blitz_champion', False)
            }
            
            # Отладка: логируем данные Шомахова
            if transformed_player['name'] == "Шомахов Резиуан":
                app_logger.info(f"Данные Шомахова: {transformed_player}")

            transformed_players.append(transformed_player)
        except Exception as e:
            app_logger.error("Ошибка обработки игрока {}: {}".format(player.get('ФИО', 'Неизвестный'), e))
            continue

    app_logger.info("Загружено {} игроков для API".format(len(transformed_players)))
    return transformed_players

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players')
def get_players():
    try:
        players = load_players()
        return jsonify(players)
    except Exception as e:
        app_logger.error("Ошибка в /api/players: {}".format(str(e)))
        return jsonify({"error": "Internal server error"}), 500

def run_scheduler():
    schedule.every().day.at("07:00").do(update_ratings)
    schedule.every().day.at("19:00").do(update_ratings)

    app_logger.info("Планировщик запущен")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    app_logger.info("Запуск приложения")
    update_ratings()

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    app.run(debug=True)