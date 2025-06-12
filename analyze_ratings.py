import json
import os

TOURNAMENTS_FILE = os.path.join(os.path.dirname(__file__), 'tournaments.json')

def analyze_tournament_strength():
    print("--- Запуск анализатора силы турниров ---")
    try:
        with open(TOURNAMENTS_FILE, 'r', encoding='utf-8') as f:
            tournaments = json.load(f)
    except FileNotFoundError:
        print(f"ОШИБКА: Файл {TOURNAMENTS_FILE} не найден.")
        return

    tournament_stats = []

    for tournament in tournaments:
        results = tournament.get("results", [])
        if not results:
            continue

        name = tournament.get("name", "Без названия")
        total_participants = len(results)

        # Считаем общий средний рейтинг
        all_ratings = [p.get("initial_rating", 0) for p in results if p.get("initial_rating", 0) > 0]
        overall_avg_rating = round(sum(all_ratings) / len(all_ratings) if all_ratings else 0)

        # Считаем средний рейтинг топ-15
        sorted_by_rating = sorted(results, key=lambda p: p.get("initial_rating", 0), reverse=True)
        top_15_ratings = [p.get("initial_rating", 0) for p in sorted_by_rating[:15] if p.get("initial_rating", 0) > 0]
        avg_rating_top_15 = round(sum(top_15_ratings) / len(top_15_ratings) if top_15_ratings else 0)

        tournament_stats.append({
            "name": name,
            "avg_top_15": avg_rating_top_15,
            "participants": total_participants,
            "overall_avg": overall_avg_rating
        })

    # Сортируем турниры по главному показателю - среднему рейтингу топ-15
    sorted_stats = sorted(tournament_stats, key=lambda x: x['avg_top_15'], reverse=True)

    print("\n--- Анализ турниров (отсортировано по силе топ-15) ---\n")
    for stat in sorted_stats:
        print(f"AvgTop15: {stat['avg_top_15']:<5} | Участ.: {stat['participants']:<4} | Общ.Avg: {stat['overall_avg']:<5} | {stat['name']}")
    
    print("\n--- Анализ завершен ---")

if __name__ == '__main__':
    analyze_tournament_strength()