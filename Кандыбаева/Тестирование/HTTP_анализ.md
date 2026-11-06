# Анализ HTTP-запроса учебного приложения

Выполнил: Бокун Алексей Янович. Группа: 4ИСП9-45.

При работающем локальном сервере выполнена команда:

```sh
curl -i 'http://127.0.0.1:8000/api/login?login=manager'
```

Фактически получен ответ:

```http
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.9.6
Date: Thu, 05 Nov 2026 09:51:53 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 85

{"id": 4, "full_name": "Кузнецов Алексей", "role": "Менеджер"}
```

Метод запроса — GET, адрес — локальный сервер, путь — `/api/login`, параметр `login=manager` передан в URL. Тела запроса нет. Статус 200 означает успешный ответ; сервер сообщает тип содержимого JSON и его длину в байтах. Тело ответа содержит идентификатор, имя и учебную роль пользователя.

## Запрос каталога через Chrome DevTools Protocol

При загрузке портала конференций средствами Chrome DevTools Protocol записан запрос:

- URL: `http://127.0.0.1:8001/api/events`; метод: `GET`; тело запроса отсутствует.
- Заголовок запроса `Referer: http://127.0.0.1:8001/`; браузер — Headless Chrome 157 на macOS.
- Статус ответа: `200 OK`.
- Заголовки ответа: `Content-Type: application/json; charset=utf-8`, `Content-Length: 959`, `Cache-Control: no-store`, `Server: BaseHTTP/0.6 Python/3.9.6`.
- Тело — массив JSON из трёх учебных мероприятий. Каждый объект содержит `id`, `title`, `event_date`, `venue`, `description`.

Данные получены программно через Chrome DevTools Protocol. Скриншот вкладки Network в интерфейсе DevTools отдельно не снимался.
