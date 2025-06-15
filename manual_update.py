# Файл: manual_update.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
from app import update_ratings, calculate_and_save_achievers_ranking, app_logger

def run_all():
    app_logger.info("НАЧАЛО РУЧНОГО ОБНОВЛЕНИЯ ДАННЫХ...")

    # Мы УБРАЛИ отсюда вызов update_tournaments_from_fsr(), 
    # чтобы он не перезатирал наш полный tournaments.json

    try:
        # Сразу переходим к обновлению рейтингов игроков в нашей БД
        app_logger.info("--- Этап 1: Обновление рейтингов игроков ---")
        update_ratings()
        app_logger.info("--- Этап 1 ЗАВЕРШЕН ---")
    except Exception as e:
        app_logger.error(f"Ошибка на этапе 1 (рейтинги): {e}", exc_info=True)

    try:
        # А затем к расчету достижений на основе ПОЛНЫХ данных из tournaments.json
        app_logger.info("--- Этап 2: Расчет рейтинга достижений ---")
        calculate_and_save_achievers_ranking()
        app_logger.info("--- Этап 2 ЗАВЕРШЕН ---")
    except Exception as e:
        app_logger.error(f"Ошибка на этапе 2 (достижения): {e}", exc_info=True)

    app_logger.info("РУЧНОЕ ОБНОВЛЕНИЕ ДАННЫХ ПОЛНОСТЬЮ ЗАВЕРШЕНО.")

if __name__ == '__main__':
    run_all()