"""Интеграционная проверка HTTP API на отдельной временной базе."""
import http.cookiejar
import importlib.util
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("portal_server", ROOT / "server.py")
portal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portal)


class PortalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        portal.DB = Path(cls.tmp.name) / "test.db"
        portal.init_db()
        cls.httpd = portal.ThreadingHTTPServer(("127.0.0.1", 0), portal.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:{}".format(cls.httpd.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    def client(self):
        return build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(self, client, path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        request = Request(self.base + path, data=body, headers={"Content-Type": "application/json"} if body else {})
        try:
            with client.open(request) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_participant_and_admin_flow(self):
        guest, member, admin = self.client(), self.client(), self.client()
        self.assertEqual(401, self.request(guest, "/api/applications")[0])
        details = {"login": "student", "password": "Password123", "email": "student@example.test", "phone": "+79991234567"}
        self.assertEqual(201, self.request(member, "/api/register", details)[0])
        self.assertEqual(409, self.request(member, "/api/register", details)[0])
        self.assertEqual(401, self.request(member, "/api/login", {"login": "student", "password": "wrong"})[0])
        self.assertEqual(200, self.request(member, "/api/login", details)[0])
        self.assertEqual(400, self.request(member, "/api/apply", {"event_id": 1, "room": "выдуманное помещение"})[0])
        self.assertEqual(201, self.request(member, "/api/apply", {"event_id": 1, "payment_method": "Карта", "room": "Онлайн"})[0])
        _, active = self.request(member, "/api/applications")
        self.assertEqual("Онлайн", active[0]["room"])
        self.assertEqual(200, self.request(member, "/api/cancel", {"id": active[0]["id"]})[0])
        self.assertEqual(201, self.request(member, "/api/apply", {"event_id": 3})[0])
        self.assertEqual(409, self.request(member, "/api/apply", {"event_id": 3})[0])
        status, entries = self.request(member, "/api/applications")
        self.assertEqual(200, status)
        application_id = entries[0]["id"]
        self.assertEqual(403, self.request(member, "/api/status", {"id": application_id})[0])
        self.assertEqual(400, self.request(member, "/api/review", {"id": application_id, "rating": 5, "text": "Спасибо"})[0])
        self.assertEqual(200, self.request(admin, "/api/login", {"login": "admin", "password": "Admin12345"})[0])
        self.assertEqual(200, self.request(admin, "/api/status", {"id": application_id})[0])
        self.assertEqual(200, self.request(admin, "/api/status", {"id": application_id})[0])
        self.assertEqual(201, self.request(member, "/api/review", {"id": application_id, "rating": 5, "text": "Спасибо"})[0])
        self.assertEqual(409, self.request(member, "/api/review", {"id": application_id, "rating": 5, "text": "Снова"})[0])
        self.assertEqual(200, self.request(member, "/api/logout", {})[0])
        self.assertEqual(401, self.request(member, "/api/applications")[0])

    def test_migration_preserves_old_application(self):
        original = portal.DB
        old_db = Path(self.tmp.name) / "old.db"
        try:
            with sqlite3.connect(str(old_db)) as db:
                db.executescript("CREATE TABLE users(id INTEGER PRIMARY KEY); CREATE TABLE applications(id INTEGER PRIMARY KEY); INSERT INTO applications VALUES(7);")
            portal.DB = old_db
            portal.init_db()
            with sqlite3.connect(str(old_db)) as db:
                row = db.execute("SELECT id,payment_method,room FROM applications").fetchone()
            self.assertEqual((7, "Бесплатно", "Основной зал"), row)
        finally:
            portal.DB = original

    def test_registration_boundaries(self):
        base = {"email": "student@example.test", "phone": "+79991234567"}
        for login in ("abc", "a" * 32):
            with self.subTest(login_length=len(login)):
                self.assertEqual(login, portal.valid_registration(dict(base, login=login, password="abcdefgh"))[0])
        for login in ("ab", "a" * 33, "студент"):
            with self.subTest(login=login):
                with self.assertRaises(ValueError):
                    portal.valid_registration(dict(base, login=login, password="abcdefgh"))
        for length in (8, 128):
            with self.subTest(password_length=length):
                self.assertEqual(length, len(portal.valid_registration(dict(base, login="student", password="a" * length))[1]))
        for length in (7, 129):
            with self.subTest(password_length=length):
                with self.assertRaises(ValueError):
                    portal.valid_registration(dict(base, login="student", password="a" * length))


if __name__ == "__main__":
    unittest.main()
