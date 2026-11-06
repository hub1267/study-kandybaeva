"""Учебный портал конференций на стандартной библиотеке Python."""
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import date
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
THEME = os.environ.get("PORTAL_THEME", "conference")
DB = Path(os.environ.get("CONFERENCE_DB", str(ROOT / ("conference_tech.db" if THEME == "tech" else "conference.db"))))
SCHEMA = ROOT.parent / "ПР_02_База_данных" / "schema.sql"
STATIC = ROOT / "static"


def connect():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200000).hex()
    return salt + ":" + digest


def init_db():
    with connect() as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'").fetchone():
            columns = {row["name"] for row in db.execute("PRAGMA table_info(applications)")}
            if "payment_method" not in columns:
                db.execute("ALTER TABLE applications ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'Бесплатно'")
            if "room" not in columns:
                db.execute("ALTER TABLE applications ADD COLUMN room TEXT NOT NULL DEFAULT 'Основной зал'")
            return
        db.executescript(SCHEMA.read_text(encoding="utf-8"))
        db.execute("CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        db.execute("INSERT INTO users(login,password_hash,email,phone,role) VALUES (?,?,?,?,?)",
                   ("admin", password_hash("Admin12345"), "admin@example.test", "+79990000000", "admin"))
        events = [
            ("Современные технологии в образовании", "2027-03-12", "Москва, учебный центр", "Практики цифровой трансформации и инструменты для преподавателей."),
            ("Развитие компетенций педагога", "2027-03-20", "Санкт-Петербург, учебный центр", "Методики обучения, профессиональное развитие и обмен опытом."),
            ("Инклюзивное образование: практика и перспективы", "2025-03-27", "Казань, учебный центр", "Обсуждение доступности образования и взаимодействия специалистов."),
        ]
        if THEME == "tech":
            events = [
                ("Разработка веб-приложений", "2027-03-12", "Москва, технопарк", "Практические занятия по созданию веб-сервисов."),
                ("Тестирование и качество ПО", "2027-03-20", "Санкт-Петербург, технопарк", "Встреча специалистов по тестированию программ."),
                ("Базы данных на практике", "2025-03-27", "Казань, технопарк", "Проектирование и сопровождение баз данных."),
            ]
        db.executemany("INSERT INTO events(title,event_date,venue,description) VALUES (?,?,?,?)", events)


def valid_registration(data):
    login = str(data.get("login", "")).strip()
    password = str(data.get("password", ""))
    email = str(data.get("email", "")).strip()
    phone = str(data.get("phone", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{3,32}", login):
        raise ValueError("Логин: от 3 до 32 латинских букв, цифр или знаков подчёркивания.")
    if len(password) < 8 or len(password) > 128:
        raise ValueError("Пароль должен содержать от 8 до 128 символов.")
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Введите корректную электронную почту.")
    if not re.fullmatch(r"\+?[0-9 ()-]{10,20}", phone):
        raise ValueError("Введите корректный телефон.")
    return login, password, email, phone


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, extra=None):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)

    def current_user(self, db):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            return None
        token = jar["session"].value if "session" in jar else ""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return db.execute("SELECT u.id,u.login,u.role FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.created_at >= datetime('now','-1 day')", (token_hash,)).fetchone()

    def body(self):
        if self.headers.get_content_type() != "application/json":
            raise ValueError("Ожидается JSON.")
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= 16000:
            raise ValueError("Неверный размер запроса.")
        obj = json.loads(self.rfile.read(size))
        if not isinstance(obj, dict):
            raise ValueError("Ожидается объект JSON.")
        return obj

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            with connect() as db:
                user = self.current_user(db)
                if path == "/api/me":
                    return self.respond(200, dict(user) if user else None)
                if path == "/api/events":
                    return self.respond(200, [dict(row) for row in db.execute("SELECT * FROM events ORDER BY event_date DESC")])
                if path == "/api/applications":
                    if not user:
                        return self.respond(401, {"error": "Войдите в систему."})
                    sql = """SELECT a.id,a.event_id,a.user_id,e.title,e.event_date,e.venue,s.name AS status,
                             a.status_id,a.payment_method,a.room,u.login,r.id AS review_id FROM applications a
                             JOIN events e ON e.id=a.event_id JOIN users u ON u.id=a.user_id
                             JOIN statuses s ON s.id=a.status_id LEFT JOIN reviews r ON r.application_id=a.id"""
                    args = ()
                    if user["role"] != "admin":
                        sql += " WHERE a.user_id=?"
                        args = (user["id"],)
                    return self.respond(200, [dict(row) for row in db.execute(sql + " ORDER BY a.id DESC", args)])
            index = "variant.html" if THEME == "tech" else "index.html"
            file = (STATIC / (index if path == "/" else path.lstrip("/"))).resolve()
            if STATIC.resolve() not in file.parents or not file.is_file():
                return self.respond(404, {"error": "Страница не найдена."})
            body = file.read_bytes()
            content = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                       ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml"}.get(file.suffix, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", content)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (OSError, sqlite3.Error) as error:
            self.respond(500, {"error": "Ошибка сервера."})
            print(error, flush=True)

    def do_POST(self):
        try:
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host"):
                return self.respond(403, {"error": "Недопустимый источник запроса."})
            data = self.body()
            with connect() as db:
                user = self.current_user(db)
                if self.path == "/api/register":
                    login, password, email, phone = valid_registration(data)
                    db.execute("INSERT INTO users(login,password_hash,email,phone,role) VALUES (?,?,?,?,?)",
                               (login, password_hash(password), email, phone, "participant"))
                    return self.respond(201, {"message": "Регистрация завершена. Войдите в систему."})
                if self.path == "/api/login":
                    found = db.execute("SELECT * FROM users WHERE login=?", (str(data.get("login", "")).strip(),)).fetchone()
                    supplied = str(data.get("password", ""))
                    if not found or len(supplied) > 128 or not hmac.compare_digest(found["password_hash"], password_hash(supplied, found["password_hash"].split(":")[0])):
                        return self.respond(401, {"error": "Неверный логин или пароль."})
                    token = secrets.token_urlsafe(32)
                    db.execute("INSERT INTO sessions(token_hash,user_id) VALUES (?,?)", (hashlib.sha256(token.encode()).hexdigest(), found["id"]))
                    return self.respond(200, {"login": found["login"], "role": found["role"]},
                                        {"Set-Cookie": "session=" + token + "; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400"})
                if self.path == "/api/logout":
                    jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
                    token = jar["session"].value if "session" in jar else ""
                    db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
                    return self.respond(200, {"ok": True}, {"Set-Cookie": "session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"})
                if not user:
                    return self.respond(401, {"error": "Войдите в систему."})
                if self.path == "/api/apply":
                    event = db.execute("SELECT id FROM events WHERE id=?", (int(data["event_id"]),)).fetchone()
                    if not event:
                        return self.respond(404, {"error": "Мероприятие не найдено."})
                    payment = data.get("payment_method", "Бесплатно")
                    room = data.get("room", "Основной зал")
                    if payment not in ("Бесплатно", "Карта", "Безналичный расчёт") or room not in ("Основной зал", "Малый зал", "Онлайн"):
                        raise ValueError("Выберите допустимый способ оплаты и помещение.")
                    db.execute("INSERT INTO applications(user_id,event_id,status_id,payment_method,room) VALUES (?,?,1,?,?)", (user["id"], event["id"], payment, room))
                    return self.respond(201, {"message": "Заявка отправлена."})
                if self.path == "/api/cancel":
                    result = db.execute("DELETE FROM applications WHERE id=? AND user_id=? AND status_id=1", (int(data["id"]), user["id"]))
                    if not result.rowcount:
                        raise ValueError("Можно отменить только свою новую заявку.")
                    return self.respond(200, {"message": "Заявка отменена."})
                if self.path == "/api/status":
                    if user["role"] != "admin":
                        return self.respond(403, {"error": "Доступ запрещён."})
                    app = db.execute("SELECT status_id FROM applications WHERE id=?", (int(data["id"]),)).fetchone()
                    if not app or app["status_id"] >= 3:
                        raise ValueError("Нельзя изменить статус заявки.")
                    db.execute("UPDATE applications SET status_id=status_id+1 WHERE id=?", (int(data["id"]),))
                    return self.respond(200, {"message": "Статус обновлён."})
                if self.path == "/api/review":
                    app = db.execute("SELECT a.id,a.status_id,e.event_date FROM applications a JOIN events e ON e.id=a.event_id WHERE a.id=? AND a.user_id=?", (int(data["id"]), user["id"])).fetchone()
                    rating = int(data["rating"])
                    text = str(data.get("text", "")).strip()
                    if not app or app["status_id"] != 3 or app["event_date"] > date.today().isoformat():
                        raise ValueError("Отзыв доступен после завершения заявки и мероприятия.")
                    if not 1 <= rating <= 5 or not 1 <= len(text) <= 2000:
                        raise ValueError("Введите отзыв и оценку от 1 до 5.")
                    db.execute("INSERT INTO reviews(application_id,text,rating) VALUES (?,?,?)", (app["id"], text, rating))
                    return self.respond(201, {"message": "Отзыв сохранён."})
                return self.respond(404, {"error": "Маршрут не найден."})
        except sqlite3.IntegrityError:
            self.respond(409, {"error": "Такая запись уже существует."})
        except ValueError as error:
            self.respond(400, {"error": str(error) or "Проверьте введённые данные."})
        except (TypeError, KeyError):
            self.respond(400, {"error": "Проверьте введённые данные."})
        except sqlite3.Error as error:
            print(error, flush=True)
            self.respond(500, {"error": "Ошибка базы данных."})


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "8001"))
    print("Учебный сервер: http://127.0.0.1:{}".format(port), flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
