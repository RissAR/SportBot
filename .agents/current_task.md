# ТЕХНІЧНЕ ЗАВДАННЯ: Фаза 5. Автономність, Автобекапи, Фоновий воркер сповіщень та Продакшен-деплой (Hardening & Longevity)

## 1. Мета та огляд
Забезпечити 100% автономність системи `SportBot` для багаторічної безперебійної роботи на сервері (Zero-Maintenance):
1. **Фоновий воркер щоденних нагадувань (`ReminderWorker`):** Автоматичний щоденний пуш у Telegram атлетам, які ще не завершили поточне тренування, із захистом від повторного спаму (не більше 1 пуша на день).
2. **Автоматичні щоденні бекапи SQLite (`BackupWorker`):** Нативний гарячий бекап через `VACUUM INTO` у `/app/backups` із ротацією (зберігаються останні 7 копій) та періодичний скид журналу `wal_checkpoint`.
3. **Мультистейдж `Dockerfile` (All-in-One):** Єдиний Docker-образ, що самостійно збирає фронтенд на базі Node 20 та запускає бекенд на Python 3.11. Розгортання зводиться до єдиної команди: `docker compose up -d --build`.
4. **Docker Healthcheck та Graceful Shutdown:** Самовідновлення контейнера при зависанні та коректне закриття з'єднань із базою даних при `SIGTERM` / `SIGINT`.
5. **Документація з експлуатації (`README.md`):** Чітка інструкція розгортання та керування проектом.

---

## 2. Структура нових та оновлюваних файлів

```text
/home/dofi/Dev/SportBot/
├── Dockerfile                   # Оновлений мультистейдж білд (Node 20 -> Python 3.11)
├── docker-compose.yml           # Healthcheck, ліміти логів, restart: unless-stopped
├── README.md                    # Інструкція з деплою та архітектури
└── src/
    ├── main.py                  # Інтеграція фонових воркерів та Graceful Shutdown
    └── services/
        ├── __init__.py
        ├── reminder.py          # Щоденні сповіщення атлетів з перевіркою стріку
        └── backup.py            # Гарячі бекапи SQLite, ротація 7 днів, wal_checkpoint
```

---

## 3. Покрокові технічні вимоги

### БЛОК 1. Щоденний фоновий воркер нагадувань (`src/services/reminder.py`)
1. Створити функцію `run_reminder_worker(bot: Bot, check_interval_seconds: int = 3600)`:
   - Працює як нескінченний асинхронний цикл (`while True: await asyncio.sleep(...)`).
   - Раз на годину перевіряє поточну годину (за замовчуванням о 09:00 локального часу або щоранку).
   - Шукає користувачів у базі даних, у яких:
     - Сьогодні ще **немає завершеного тренування** у `workout_logs` для поточного дня `user.current_day`.
     - Нагадування сьогодні ще **не надсилалося** (ведення словника в пам'яті `notified_today: set[tuple[int, str]]` або перевірка дати, щоб виключити спам).
   - Формує дружнє повідомлення англійською мовою з безпечним екрануванням:
     ```html
     🌅 <b>Good morning, {name}!</b>

     Today is <b>Day {current_day} of 30</b>: <b>{day_title}</b>.
     🎯 <b>Focus:</b> {focus_areas}

     Stay disciplined and conquer your session!
     ```
   - Додає інлайн-кнопку: `🚀 Open Today's Workout` (`web_app=WebAppInfo(url=settings.get_webapp_url())`).
   - Безпечно обробляє помилки (якщо користувач заблокував бота — логує попередження без аварійної зупинки воркера).
   - Підтримує `asyncio.CancelledError` для коректної зупинки.

---

### БЛОК 2. Модуль автобекапів та ротації бази (`src/services/backup.py`)
1. Створити функцію `create_db_backup(backup_dir: str = "backups", max_backups: int = 7)`:
   - Створює директорію `backup_dir`, якщо вона відсутня.
   - Генерує ім'я файлу з часовою міткою: `sportbot_backup_YYYYMMDD_HHMMSS.db`.
   - Виконує **гарячий атомарний бекап** через сесію SQLAlchemy:
     ```python
     await session.execute(text(f"VACUUM INTO '{backup_path}'"))
     await session.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
     ```
   - **Ротація бекапів:**
     - Знаходить усі файли `sportbot_backup_*.db` у папці `backup_dir`.
     - Сортує за датою створення.
     - Якщо кількість перевищує `max_backups` (7) — автоматично видаляє найстаріші копії (`os.remove()`).
2. Створити фоновий процес `run_backup_worker(interval_seconds: int = 86400)`:
   - Запускається кожні 24 години (наприклад, щоночі о 03:00).
   - Логує успішне створення бекапу та кількість збережених копій.

---

### БЛОК 3. Інтеграція та Graceful Shutdown (`src/main.py`)
1. У функції `main()` зареєструвати паралельний запуск усіх сервісів через `asyncio.gather`:
   - `run_api(server)`
   - `run_bot()` (якщо налаштовано токен)
   - `run_reminder_worker(bot)` (якщо бот активний)
   - `run_backup_worker()`
2. Обробка сигналів `SIGINT` та `SIGTERM`:
   - Ініціювати завершення `server.should_exit = True`.
   - Зупинити polling бота `dp.stop_polling()`.
   - Скасувати фонові воркери (`task.cancel()`).
   - Фінальний скид WAL-журналу: `PRAGMA wal_checkpoint(TRUNCATE)` перед закриттям процесу.
   - Чистий вихід із кодом 0.

---

### БЛОК 4. Мультистейдж `Dockerfile` (All-in-One Build)
Оновити `Dockerfile` для повної автоматизації розгортання:
```dockerfile
# Stage 1: Build Frontend (Vite + React)
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app/data /app/backups /app/frontend/dist

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY --from=frontend-builder /frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["python", "-m", "src.main"]
```

---

### БЛОК 5. Захист та Healthcheck у `docker-compose.yml`
Оновити `docker-compose.yml`:
- Додати блок `healthcheck`:
  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 15s
  ```
- Політика перезапуску: `restart: unless-stopped`.
- Монтування томів:
  - `./data:/app/data` (збереження БД)
  - `./backups:/app/backups` (доступ до автобекапів з хоста)
- Ротація логів: `max-size: "10m"`, `max-file: "3"`.

---

### БЛОК 6. Документація розгортання (`README.md`)
Створити лаконічний, професійний `README.md`:
1. Опис проекту (SportBot: 30-Day Calisthenics Engine + TMA).
2. Архітектура (FastAPI, SQLite WAL, aiogram 3, React 18, Tailwind).
3. Покрокове розгортання на VPS:
   - Клонування репозиторію.
   - Створення `.env` на базі `.env.example`.
   - Запуск: `docker compose up -d --build`.
   - Моніторинг логів: `docker compose logs -f`.
   - Перевірка бекапів у `./backups`.

---

## 4. Критерії приймання та перевірки (Acceptance Criteria)
1. **Синтаксис та компіляція:**
   `python3 -m py_compile src/services/*.py src/main.py` завершується з кодом 0.
2. **Бекап-тест:**
   Тестовий запуск `create_db_backup()` створює валідний `.db` файл у `backups/` та підтверджує роботу ротації.
3. **Мультистейдж перевірка:**
   `Dockerfile` синтаксично валідний і містить як збірку `frontend`, так і запуск `python`.
4. **Готовність до деплою:**
   `docker-compose.yml` валідний за структурою, містить надійний healthcheck та ротацію логів.
5. **Формат звіту:**
   Список модифікованих файлів та єдина команда git:
   `git add . && git commit -m "..." && git push origin main`.
