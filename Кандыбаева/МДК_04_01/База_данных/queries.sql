-- 1. Товары дороже 10 000 рублей.
SELECT name, price FROM products WHERE price > 10000;
-- 2. Товары категории «Женская обувь».
SELECT p.name FROM products p JOIN categories c ON c.id = p.category_id WHERE c.name = 'Женская обувь';
-- 3. Количество моделей каждого производителя, включая производителей без товаров.
SELECT m.name, COUNT(p.id) AS models FROM manufacturers m LEFT JOIN products p ON p.manufacturer_id = m.id GROUP BY m.id, m.name;
-- 4. Средняя цена по категориям.
SELECT c.name, ROUND(AVG(p.price), 2) AS average_price FROM categories c JOIN products p ON p.category_id = c.id GROUP BY c.id, c.name;
-- 5. Модели с суммарным остатком меньше трёх, включая нулевой остаток.
SELECT p.name, COALESCE(SUM(s.quantity), 0) AS quantity FROM products p LEFT JOIN stock s ON s.product_id = p.id GROUP BY p.id, p.name HAVING COALESCE(SUM(s.quantity), 0) < 3;
-- 6. Товары без заказов за предыдущий календарный месяц.
SELECT p.name, p.price, ROUND(p.price * 0.75, 2) AS discount_price FROM products p WHERE NOT EXISTS (SELECT 1 FROM order_items oi JOIN orders o ON o.id = oi.order_id WHERE oi.product_id = p.id AND o.order_date >= date('now', 'start of month', '-1 month') AND o.order_date < date('now', 'start of month'));
-- 7. Пять самых дорогих заказов и их покупатели.
SELECT o.id, u.full_name, SUM(oi.quantity * oi.unit_price) AS total FROM orders o JOIN users u ON u.id = o.user_id JOIN order_items oi ON oi.order_id = o.id GROUP BY o.id, u.full_name ORDER BY total DESC LIMIT 5;
-- 8. Размеры с положительным остатком, которые ни разу не заказывались.
SELECT DISTINCT z.size FROM sizes z JOIN stock s ON s.size_id = z.id WHERE s.quantity > 0 AND NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.size_id = z.id) ORDER BY z.size;
