# Файл: populate_all_results.py
import time
import json
from app import (
    load_tournaments, 
    save_tournaments, 
    scrape_tournament_results, 
    calculate_player_tournament_stats,
    generate_tournament_highlights,
    get_db_connection,
    app_logger
)

def populate_all():
    app_logger.info("НАЧАЛО ПОЛНОЙ ЗАГРУЗКИ РЕЗУЛЬТАТОВ ВСЕХ ТУРНИРОВ...")
    
    # Загружаем текущий список турниров
    tournaments = load_tournaments()
    total_tournaments = len(tournaments)
    app_logger.info(f"Найдено {total_tournaments} турниров для проверки.")

    # Получаем данные по игрокам для расчета хайлайтов
    conn_players = get_db_connection()
    if not conn_players:
        app_logger.error("Не удалось подключиться к базе данных. Прерывание.")
        return
        
    cursor_players = conn_players.cursor()
    cursor_players.execute("SELECT fsr_id, birth_year, gender FROM players")
    # Преобразуем данные в словарь для быстрого доступа
    all_db_players_info = {str(row[0]): {'birth_year': row[1], 'gender': row[2]} for row in cursor_players.fetchall()}
    conn_players.close()
    
    updated_count = 0
    for i, tournament in enumerate(tournaments):
        # Проверяем, есть ли уже детальные результаты
        if tournament.get("results") and len(tournament.get("results")) > 0:
            print(f"({i+1}/{total_tournaments}) Пропуск турнира '{tournament['name']}', так как результаты уже есть.")
            continue

        fsr_link = tournament.get('fsr_link')
        if not fsr_link:
            print(f"({i+1}/{total_tournaments}) Пропуск турнира '{tournament['name']}', так как нет ссылки.")
            continue

        print(f"({i+1}/{total_tournaments}) Загрузка данных для турнира: {tournament['name']}...")
        
        try:
            # Скачиваем результаты
            scraped_results = scrape_tournament_results(fsr_link)
            
            if scraped_results:
                # Рассчитываем доп. статистику и хайлайты (как это делает API)
                results_with_stats = calculate_player_tournament_stats(scraped_results)
                tournament_highlights = generate_tournament_highlights(results_with_stats, all_db_players_info)
                
                # Сохраняем в наш объект турнира
                tournament['results'] = results_with_stats
                tournament['highlights'] = tournament_highlights
                updated_count += 1
                print(f"---> Успешно загружено {len(scraped_results)} результатов.")
            else:
                print("---> Не удалось загрузить результаты.")

        except Exception as e:
            app_logger.error(f"Произошла ошибка при обработке турнира {tournament.get('name')}: {e}", exc_info=True)

        # Сохраняем прогресс каждые 5 турниров, чтобы не потерять данные
        if (i + 1) % 5 == 0:
            print(f"Сохранение промежуточного прогресса... Обработано {i+1} турниров.")
            save_tournaments(tournaments)

        # Пауза, чтобы не перегружать сайт ФШР
        time.sleep(2)

    # Финальное сохранение
    print("Финальное сохранение всех данных...")
    save_tournaments(tournaments)
    app_logger.info(f"ПОЛНАЯ ЗАГРУЗКА ЗАВЕРШЕНА. Обновлены результаты для {updated_count} турниров.")


if __name__ == '__main__':
    populate_all()