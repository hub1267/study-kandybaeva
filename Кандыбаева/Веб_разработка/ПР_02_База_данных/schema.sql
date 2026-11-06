PRAGMA foreign_keys = ON;
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  login TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('participant', 'admin'))
);
CREATE TABLE events (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  event_date TEXT NOT NULL,
  venue TEXT NOT NULL,
  description TEXT NOT NULL
);
CREATE TABLE statuses (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE applications (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  event_id INTEGER NOT NULL REFERENCES events(id),
  status_id INTEGER NOT NULL REFERENCES statuses(id),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  payment_method TEXT NOT NULL DEFAULT 'Бесплатно',
  room TEXT NOT NULL DEFAULT 'Основной зал',
  UNIQUE (user_id, event_id)
);
CREATE TABLE reviews (
  id INTEGER PRIMARY KEY,
  application_id INTEGER NOT NULL UNIQUE REFERENCES applications(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX applications_user ON applications(user_id);
CREATE INDEX applications_status ON applications(status_id);
INSERT INTO statuses VALUES (1, 'новая'), (2, 'назначено'), (3, 'завершено');
