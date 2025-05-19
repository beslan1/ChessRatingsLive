import pandas as pd
import json
import os
import logging

# Настройка логирования
logging.basicConfig(
    filename='convert.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Пути к файлам
XLSX_FILE = os.path.join(os.path.dirname(__file__), 'players_kbr.xlsx')
JSON_FILE = os.path.join(os.path.dirname(__file__), 'players_kbr.json')

def convert_xlsx_to_json():
    try:
        # Читаем XLSX-файл
        df = pd.read_excel(XLSX_FILE)
        logging.info(f"Загружен XLSX-файл: {len(df)} записей")

        # Заменяем все NaN на пустую строку ""
        df = df.fillna("")

        # Определяем числовые столбцы
        numeric_columns = ['Код ФШР', 'Код ФИДЕ', 'Год рождения', 'ФШР клс', 'ФИДЕ клс', 'ФШР быс', 'ФИДЕ быс', 'ФШР блиц', 'ФИДЕ блиц']
        
        # Преобразуем числовые столбцы: убираем .0, превращая float в int
        for col in numeric_columns:
            if col in df.columns:
                # Преобразуем в int, если это число, иначе оставляем как есть (например, "")
                df[col] = df[col].apply(lambda x: int(x) if isinstance(x, (int, float)) and x != "" else x)

        # Преобразуем DataFrame в список словарей
        players = df.to_dict('records')

        # Сохраняем в JSON
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=4)
        logging.info(f"Данные успешно сохранены в {JSON_FILE}: {len(players)} игроков")

        print(f"Конвертация завершена: {len(players)} игроков сохранено в {JSON_FILE}")
    except Exception as e:
        logging.error(f"Ошибка при конвертации XLSX в JSON: {e}")
        print(f"Произошла ошибка: {e}")

if __name__ == '__main__':
    convert_xlsx_to_json()