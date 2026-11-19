# DEC Survey — опрос «до и после внедрения DEC»

Веб-опросник для оценки процесса инженерных расчётов: два блока вопросов —
«до внедрения DEC» и «с использованием DEC». Участники не видят результаты,
а администратор смотрит агрегированную статистику по секретной ссылке.

## Возможности

- Два блока вопросов: baseline (до DEC) и результаты (с DEC).
- Участник не видит итоги и не может пройти опрос повторно (signed cookie).
- Админ-страница со статистикой: медианное время «до/после», экономия времени,
  частота ошибок, удобство, CSI, NPS, готовность к подписке.
- Готово к деплою на один хост (Render / PythonAnywhere / VPS).

## Структура

```
dec-survey-demo/
├── app.py            # Flask-приложение и маршруты
├── questions.py      # вопросы (блоки before/after)
├── stats.py          # расчёт метрик
├── db.py             # хранение ответов в SQLite
├── templates/        # form.html, thanks.html, admin.html
├── static/style.css
├── requirements.txt
├── Procfile          # для Render / Heroku
└── .env.example
```

## Локальный запуск

```bash
cd dec-survey-demo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

> Если `python3 -m venv .venv` падает с ошибкой `ensurepip is not available`,
> поставьте пакет `sudo apt install -y python3.10-venv`, либо обойдитесь без
> виртуального окружения:
> ```bash
> pip install --user -r requirements.txt
> python3 app.py
> ```

Откройте `http://127.0.0.1:5000`.

Статистика: `http://127.0.0.1:5000/admin?token=change-me-token`.

## Настройки (переменные окружения)

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `DEC_SECRET_KEY` | ключ для подписи cookie | `dev-secret-change-me` |
| `DEC_ADMIN_TOKEN` | токен доступа к `/admin` | `change-me-token` |
| `DEC_DB_PATH` | путь к файлу SQLite | `data/survey.db` |

Перед публикацией обязательно задайте `DEC_SECRET_KEY` и `DEC_ADMIN_TOKEN`.

## Деплой

### Render

1. Создайте новый Web Service, подключите репозиторий.
2. Build command: `pip install -r requirements.txt`.
3. Start command: `gunicorn app:app`.
4. В разделе Environment добавьте `DEC_SECRET_KEY` и `DEC_ADMIN_TOKEN`.
5. Добавьте Persistent Disk и укажите `DEC_DB_PATH=/var/data/survey.db`,
   иначе база будет пересоздаваться при каждом деплое.

### PythonAnywhere

1. Залейте код, создайте виртуальное окружение и установите зависимости.
2. В веб-табе укажите WSGI-файл вида:

```python
import sys
path = "/home/<user>/dec-survey-demo"
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

### VPS / любой хост

```bash
pip install -r requirements.txt
gunicorn -w 1 -b 0.0.0.0:8000 app:app
```

> При использовании SQLite запускайте один воркер gunicorn (`-w 1`), чтобы
> избежать блокировок на запись.
