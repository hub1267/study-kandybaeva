-- Учебные примеры, а не данные из экзаменационных файлов импорта.
INSERT INTO categories VALUES (1, 'Женская обувь'), (2, 'Мужская обувь');
INSERT INTO manufacturers VALUES (1, 'Север'), (2, 'Город');
INSERT INTO products VALUES
  (1, 'Ботинки', 1, 1, 12000, NULL), (2, 'Кроссовки', 2, 2, 7500, NULL),
  (3, 'Туфли', 1, 2, 15000, NULL);
INSERT INTO sizes VALUES (1, 37), (2, 40), (3, 42);
INSERT INTO stock VALUES (1, 1, 1, 2), (2, 2, 2, 8), (3, 3, 3, 1);
INSERT INTO users VALUES (1, 'Иванова Анна', 'ivanova', 'Покупатель'),
  (2, 'Петров Иван', 'petrov', 'Покупатель'),
  (3, 'Сидорова Мария', 'sidorova', 'Покупатель'),
  (4, 'Кузнецов Алексей', 'manager', 'Менеджер'),
  (5, 'Смирнова Елена', 'admin', 'Администратор');
INSERT INTO orders VALUES (1, 1, date('now', 'start of month', '-1 month', '+5 days'));
INSERT INTO order_items VALUES (1, 1, 2, 2, 2, 7500);
