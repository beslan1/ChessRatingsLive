# Файл: manual_update.py
from app import update_tournaments_from_fsr, update_ratings, calculate_and_save_achievers_ranking, app_logger

def run_all():
    app_logger.info("НАЧАЛО РУЧНОГО ОБНОВЛЕНИЯ ДАННЫХ...")
    try:
        app_logger.info("--- Этап 1: Обновление турниров ---")
        update_tournaments_from_fsr()
        app_logger.info("--- Этап 1 ЗАВЕРШЕН ---")
    except Exception as e:
        app_logger.error(f"Ошибка на этапе 1 (турниры): {e}", exc_info=True)

    try:
        app_logger.info("--- Этап 2: Обновление рейтингов игроков ---")
        update_ratings()
        app_logger.info("--- Этап 2 ЗАВЕРШЕН ---")
    except Exception as e:
        app_logger.error(f"Ошибка на этапе 2 (рейтинги): {e}", exc_info=True)

    try:
        app_logger.info("--- Этап 3: Расчет рейтинга достижений ---")
        calculate_and_save_achievers_ranking()
        app_logger.info("--- Этап 3 ЗАВЕРШЕН ---")
    except Exception as e:
        app_logger.error(f"Ошибка на этапе 3 (достижения): {e}", exc_info=True)

    app_logger.info("РУЧНОЕ ОБНОВЛЕНИЕ ДАННЫХ ПОЛНОСТЬЮ ЗАВЕРШЕНО.")

if __name__ == '__main__':
    run_all()