import json
import os

# --- НАСТРОЙКИ ---
TOURNAMENTS_FILE = os.path.join(os.path.dirname(__file__), 'tournaments.json')
MAJOR_KEYWORDS = ["чемпионат", "первенство", "кубок"]
EXCLUSION_KEYWORDS = ["школ", "гимназий", "лицеев", "городской", "отборочный"]
# -----------------

def classify_tournaments():
    print("--- Запуск классификации турниров ---")
    try:
        with open(TOURNAMENTS_FILE, 'r', encoding='utf-8') as f:
            tournaments = json.load(f)
    except FileNotFoundError:
        print(f"ОШИБКА: Файл {TOURNAMENTS_FILE} не найден.")
        return

    print(f"Найдено {len(tournaments)} турниров для анализа.\n")

    count_major = 0
    count_regular = 0

    for tournament in tournaments:
        name_lower = tournament.get("name", "").lower()

        # Логика определения "крупного" турнира
        is_major = False
        if any(key in name_lower for key in MAJOR_KEYWORDS):
            if not any(ex_key in name_lower for ex_key in EXCLUSION_KEYWORDS):
                is_major = True

        if is_major:
            print(f"[ КРУПНЫЙ ] {tournament.get('name')}")
            count_major += 1
        else:
            print(f"[ Обычный  ] {tournament.get('name')}")
            count_regular += 1

    print("\n--- Классификация завершена ---")
    print(f"Всего крупных турниров: {count_major}")
    print(f"Всего обычных турниров: {count_regular}")

if __name__ == '__main__':
    classify_tournaments()