import json
from pathlib import Path

PLAYERS_FILE   = Path("players_kbr.json")
CHAMPIONS_FILE = Path("champions.json")
BACKUP_FILE    = Path("players_kbr_backup.json")

def main():
    players   = json.loads(PLAYERS_FILE.read_text(encoding="utf-8"))
    champions = json.loads(CHAMPIONS_FILE.read_text(encoding="utf-8"))

    # делаем резервную копию на всякий случай
    BACKUP_FILE.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding="utf-8")

    for p in players:
        name = p.get("ФИО")
        p["is_classic_champion"] = name in champions.get("классик", [])
        p["is_rapid_champion"]   = name in champions.get("рапид", [])
        p["is_blitz_champion"]   = name in champions.get("блиц",  [])

    # сохраняем обновлённый JSON
    PLAYERS_FILE.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Флаги чемпионов выставлены! Резервная копия:", BACKUP_FILE)

if __name__ == "__main__":
    main()
