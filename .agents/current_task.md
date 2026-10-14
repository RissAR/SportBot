# ТЕХНІЧНЕ ЗАВДАННЯ: Фаза 0. Фундамент, Docker-каркас, Anti-Cache та асинхронний запуск

## 1. Мета та огляд
Створити первинний каркас проекту `SportBot` згідно з архітектурною методологією. Забезпечити паралельний асинхронний запуск FastAPI та aiogram 3, захищений від кешу роутинг для Telegram Mini App, сувору ізоляцію секретів через pydantic-settings та готовність до деплою в Docker.

---

## 2. Структура файлів проекту

Необхідно реалізувати наступну архітектурну структуру:
```text
/home/dofi/Dev/SportBot/
├── .agents/
│   ├── current_task.md
│   └── skills/execute-task/SKILL.md
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── data/                    # Монтується в Docker (для SQLite бази)
├── backups/                 # Для щоденних автобекапів
├── docs/
│   └── ARCHITECTURE_ROADMAP.md
├── src/
│   ├── __init__.py
│   ├── config.py            # Pydantic Settings, Zero Hardcoded Secrets
│   ├── main.py              # Точка входу: паралельний запуск API + Bot
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py           # FastAPI застосунок з Anti-Cache заголовками
│   └── bot/
│       ├── __init__.py
│       └── instance.py      # Ініціалізація aiogram Bot та Dispatcher
└── frontend/                # Скелет Telegram Mini App (Vite + React + Tailwind)
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── App.tsx
        ├── main.tsx
        └── index.css
```

---

## 3. Покрокові технічні вимоги

### БЛОК 1. Залежності та конфігурація (`requirements.txt`, `src/config.py`)
1. **`requirements.txt`:**
   - `fastapi>=0.110.0`
   - `uvicorn[standard]>=0.28.0`
   - `pydantic-settings>=2.2.0`
   - `aiogram>=3.4.0`
   - `sqlalchemy>=2.0.0`
   - `aiosqlite>=0.20.0`
2. **`src/config.py` (Zero Hardcoded Secrets):**
   - Використати `pydantic_settings.BaseSettings`.
   - `BOT_TOKEN: str = ""` (значення виключно з `.env`).
   - `WEBAPP_URL: str = "http://localhost:3000"` (дефолт для локального тестування).
   - Функція версіонування TMA для обходу кешу:
     ```python
     def get_webapp_url(self, version: str = "1.0.0") -> str:
         delimiter = "&" if "?" in self.WEBAPP_URL else "?"
         return f"{self.WEBAPP_URL}{delimiter}v={version}"
     ```
   - `DATABASE_URL: str = "sqlite+aiosqlite:///data/sportbot.db"`
   - `API_HOST: str = "0.0.0.0"`
   - `API_PORT: int = 8000`
   - `DEBUG: bool = False`
   - `CYCLE_DAYS: int = 30` (зафіксована довжина тренувального циклу).

### БЛОК 2. Бекенд API та Anti-Cache (`src/api/app.py`)
1. Створити екземпляр `FastAPI(title="SportBot API", version="1.0.0")`.
2. Додати CORS middleware (дозволити запити для Mini App).
3. Додати `/health` ендпоінт для моніторингу Docker (повертає `{"status": "ok"}`).
4. Реалізувати Middleware або заголовки проти кешування для роутів `/app*`:
   - `Cache-Control: no-cache, no-store, must-revalidate`
   - `Pragma: no-cache`
   - `Expires: 0`
   Це намертво захищає Mini App від проблеми «білого екрана» через старий кеш у Telegram.

### БЛОК 3. Telegram Bot Skeleton (`src/bot/instance.py`)
1. Ініціалізація `Bot(token=settings.BOT_TOKEN)` та `Dispatcher()`.
2. Базовий роутер із командою `/start`:
   - Якщо `BOT_TOKEN` порожній або не заданий — бот логує попередження і коректно пропускає запуск, не крашачи API бекенд.
   - Вітальне повідомлення з інлайн-кнопкою або кнопкою меню, яка веде на `settings.get_webapp_url()`.

### БЛОК 4. Точка входу та паралельний запуск (`src/main.py`)
1. Реалізувати паралельний асинхронний запуск через `asyncio.gather()`:
   - `run_api()` — Uvicorn сервер.
   - `run_bot()` — `dp.start_polling(bot)` (тільки якщо вказано валідний токен).
2. Обробка сигналів `SIGINT` та `SIGTERM` для коректного Graceful Shutdown без витоку ресурсів.

### БЛОК 5. Dockerfile та docker-compose.yml
1. **`Dockerfile`:**
   - Базовий образ `python:3.11-slim`.
   - Створення директорій `/app/data` та `/app/backups`.
   - Встановлення залежностей через `pip install --no-cache-dir -r requirements.txt`.
   - `EXPOSE 8000`.
   - Запуск `python -m src.main`.
2. **`docker-compose.yml`:**
   - Сервіс `sportbot_app`.
   - Монтування томів:
     - `./data:/app/data`
     - `./backups:/app/backups`
   - Порти `8000:8000`.
   - `restart: unless-stopped`.
   - Ротація логів (`max-size: "10m"`, `max-file: "3"`).

### БЛОК 6. Скелет Telegram Mini App (`frontend/`)
1. Налаштувати структуру `frontend` на базі React 18 / Vite / TypeScript / Tailwind CSS.
2. Стилістика (Aggressive Dark Theme):
   - Фони: глибокий обсидіан / темний фіолетовий градієнт (`bg-gradient-to-br from-[#07040d] via-[#100822] to-[#16072b]`).
   - Кнопки: червоний вогняний градієнт (`from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600`).
   - Текст: білий та сріблясто-сірий.
3. Екран-заглушка `App.tsx`:
   - Дотримання **Rules of Hooks** (всі хуки зверху).
   - Заголовок: **SPORTBOT // 30-DAY BODYWEIGHT CYCLE**.
   - Бейджі: «30 Days Cycle», «3 Difficulty Modes: Light / Medium / Hard», «Weight Tracking».
   - Кнопка з тактильним відгуком (Haptic Feedback) при натисканні (якщо запущено всередині Telegram WebApp).

---

## 4. Критерії приймання та верифікація (Acceptance Criteria)
1. **Синтаксична цілісність:**
   `python3 -m py_compile src/config.py src/main.py src/api/app.py src/bot/instance.py` виконується без жодної помилки.
2. **Безпека:**
   У репозиторії відсутні будь-які захардкоджені токени. Файл `.env` залишається в `.gitignore`.
3. **Готовність контейнеризації:**
   Файли `Dockerfile` та `docker-compose.yml` синтаксично валідні.
4. **Формат звіту:**
   Надати список створених файлів та єдину команду для коміту:
   `git add . && git commit -m "..." && git push origin main`.
