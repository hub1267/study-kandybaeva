"""Создание базы магазина обуви стандартной библиотекой Python 3.8."""
import logging
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    try:
        script = (ROOT / "schema.sql").read_text(encoding="utf-8")
        with sqlite3.connect(str(ROOT / "shop.db")) as connection:
            connection.executescript(script)
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            logging.info("Созданы таблицы: %s", ", ".join(row[0] for row in tables))
    except (OSError, sqlite3.Error) as error:
        logging.error("Не удалось создать базу: %s", error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
