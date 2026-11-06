"""Учебное приложение магазина обуви. Запуск: python3 server.py."""
import json
import mimetypes
import sqlite3
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT.parent / "База_данных" / "shop.db"
STATIC = ROOT / "static"


def connect():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


class Handler(BaseHTTPRequestHandler):
    def json_response(self, status, value):
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        try:
            with connect() as db:
                if parsed.path == "/api/login":
                    user = db.execute("SELECT id, full_name, role FROM users WHERE login=?", (params.get("login", [""])[0],)).fetchone()
                    return self.json_response(200, dict(user)) if user else self.json_response(404, {"error": "Пользователь не найден"})
                if parsed.path == "/api/orders":
                    rows = db.execute("SELECT o.id, o.order_date, u.full_name FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC").fetchall()
                    return self.json_response(200, [dict(row) for row in rows])
                if parsed.path == "/api/order":
                    order_id = int(params.get("id", ["0"])[0])
                    rows = db.execute("SELECT oi.id, p.name, s.size, oi.quantity, oi.unit_price, oi.quantity*oi.unit_price AS total FROM order_items oi JOIN products p ON p.id=oi.product_id JOIN sizes s ON s.id=oi.size_id WHERE oi.order_id=?", (order_id,)).fetchall()
                    return self.json_response(200, [dict(row) for row in rows])
            file = (STATIC / ("index.html" if parsed.path == "/" else parsed.path.lstrip("/"))).resolve()
            if STATIC.resolve() not in file.parents or not file.is_file():
                return self.json_response(404, {"error": "Файл не найден"})
            body = file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(str(file))[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, sqlite3.Error, OSError) as error:
            self.json_response(400, {"error": str(error)})

    def do_POST(self):
        if self.path != "/api/order/update":
            return self.json_response(404, {"error": "Маршрут не найден"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 10000:
                raise ValueError("Неверный размер запроса")
            data = json.loads(self.rfile.read(length))
            order_id = int(data["id"])
            order_date = date.fromisoformat(data["date"]).isoformat()
            removed = [int(item) for item in data.get("removed", [])]
            if len(set(removed)) != len(removed):
                raise ValueError("Повтор позиции")
            with connect() as db:
                if not db.execute("SELECT 1 FROM orders WHERE id=?", (order_id,)).fetchone():
                    raise ValueError("Заказ не найден")
                for item_id in removed:
                    item = db.execute("SELECT product_id, size_id, quantity FROM order_items WHERE id=? AND order_id=?", (item_id, order_id)).fetchone()
                    if item is None:
                        raise ValueError("Позиция не найдена")
                    db.execute("INSERT INTO stock(product_id,size_id,quantity) VALUES (?,?,?) ON CONFLICT(product_id,size_id) DO UPDATE SET quantity=quantity+excluded.quantity", tuple(item))
                    db.execute("DELETE FROM order_items WHERE id=?", (item_id,))
                db.execute("UPDATE orders SET order_date=? WHERE id=?", (order_date, order_id))
            self.json_response(200, {"ok": True})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError, sqlite3.Error) as error:
            self.json_response(400, {"error": str(error)})


if __name__ == "__main__":
    print("http://127.0.0.1:8000", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
