# SportBot: Autonomous 30-Day Calisthenics Engine & Telegram Mini App

An autonomous, zero-maintenance personal calisthenics training platform combining an **aiogram 3** Telegram bot, a **FastAPI** asynchronous backend with SQLite (WAL mode), and a high-performance **Telegram Mini App (TMA)** built with React 18, TypeScript, and Tailwind CSS (Clean Athletic Stealth Dark design).

---

## Technical Stack & Architecture

### Backend
- **Python 3.11** with `asyncio` concurrent orchestration.
- **FastAPI & Uvicorn**: High-performance asynchronous REST API serving interactive endpoints and static Mini App assets.
- **SQLAlchemy 2.0 (Async) & aiosqlite**: Asynchronous ORM managing relational schemas with automatic index optimization.
- **SQLite in WAL (Write-Ahead Logging) Mode**: High-concurrency database engine with atomic `PRAGMA wal_checkpoint` lifecycle management.
- **Pydantic v2**: Strict request/response validation and settings management (`src/config.py`).
- **Telegram Bot (aiogram 3.x)**: Full bot lifecycle supporting command routing (`/start`, `/today`, `/progress`, `/guide`, `/settings`, `/admin`), persistent Reply Keyboards, and inline interactive callbacks.

### Frontend (Telegram Mini App)
- **React 18 & TypeScript**: Single Page Application (SPA) built for Telegram WebApp environment.
- **Vite 5**: Fast builds with optimized chunking and asset generation.
- **Tailwind CSS**: Modern Clean Athletic Stealth Dark theme with responsive design for mobile viewports.
- **Telegram WebApp SDK Integration**: Native viewport expansion, theme synchronization, and hardware haptic feedback.
- **Custom Rest Timer HUD**: Floating timer calculated from target epoch timestamp—guaranteed not to freeze or desync when Telegram is minimized or backgrounded.

### Autonomous Workers & Security
- **Reminder Worker (`ReminderWorker`)**: Periodic background process delivering daily 09:00 Telegram reminders with anti-spam deduplication (maximum 1 notification per athlete per calendar day).
- **Hot Backup Worker (`BackupWorker`)**: Daily automated SQLite backups via atomic `VACUUM INTO` and `PRAGMA wal_checkpoint(PASSIVE)` with rolling 7-copy retention.
- **Graceful Shutdown**: Intercepts `SIGINT`/`SIGTERM`, safely completes in-flight requests, stops bot polling, cancels workers, and executes a final WAL truncate checkpoint (`PRAGMA wal_checkpoint(TRUNCATE)`).
- **HMAC-SHA256 Authentication**: Validates Telegram `initData` with cryptographic hash comparison and 24-hour replay protection.
- **Zero Hardcoded Secrets Policy**: All credentials, tokens, and endpoints are loaded exclusively through environment variables.

---

## Key Features

- **Personalized 30-Day Calisthenics Periodization:**
  - **Block A: Push** (Chest, Shoulders, Triceps)
  - **Block B: Pull** (Lats, Upper Back, Biceps, Core)
  - **Block C: Legs & Conditioning** (Quads, Hamstrings, Calves, Zone 2 / Sprint Intervals)
  - **Active Recovery & Joint Mobility** days for CNS recuperation.
- **Telegram Mini App (TMA):**
  - **Workout View:** Smart-collapsible Warm-up and Cool-down accordions, interactive set completion tracking, exercise technique guide, and workout completion submission.
  - **Rest Timer HUD:** Persistent countdown timer with `+15s`, `-15s`, and `Skip` controls plus haptic feedback upon completion.
  - **Calendar View:** Visual 30-day block matrix with day inspection modal, status badges (Completed, Current, Locked).
  - **Progress View:** Cycle completion percentages, bodyweight tracking with monthly logs, and dynamic difficulty adjustment (`light`, `medium`, `hard`).
  - **Guide View:** Technical guide of 12 bodyweight progressions with safety instructions tailored for 85 kg athletes.

---

## Repository Structure

```text
SportBot/
├── Dockerfile                   # Multi-stage production build (Node 20 -> Python 3.11)
├── docker-compose.yml           # Production orchestrator with container healthcheck
├── requirements.txt             # Python production dependencies
├── .env.example                 # Environment configuration template
├── README.md                    # Project documentation
├── src/
│   ├── main.py                  # Concurrent runner (FastAPI, Bot, Workers, Graceful Shutdown)
│   ├── config.py                # Pydantic v2 settings (Zero Hardcoded Secrets)
│   ├── api/                     # FastAPI REST API, auth (Telegram initData), routes, schemas
│   ├── bot/                     # aiogram 3 bot instance, keyboards, handlers, middleware
│   ├── db/                      # SQLAlchemy 2.0 models, aiosqlite engine, and seed data
│   └── services/                # Autonomous background workers (Reminder, Backup)
├── frontend/                    # React 18, Vite, TypeScript, Tailwind CSS Mini App
│   ├── src/
│   │   ├── components/          # WorkoutTab, CalendarTab, ProgressTab, GuideTab, RestTimerHUD
│   │   ├── api.ts               # HTTP client with Telegram initData injection
│   │   ├── types.ts             # TypeScript definitions matching backend schemas
│   │   └── App.tsx              # Root component with Rules of Hooks compliance
└── tests/                       # Automated test suites (API endpoints, bot handlers)
```

---

## Deployment & Production Setup (VPS)

### 1. Prerequisites
- Docker Engine 24.0+ & Docker Compose v2+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Clone and Configure
```bash
git clone https://github.com/RissAR/SportBot.git
cd SportBot

# Copy environment template
cp .env.example .env
```

Edit `.env` and fill in your values:
```ini
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=your_bot_username
ADMIN_IDS=your_telegram_id
WEBAPP_URL=https://your-domain.com
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///data/sportbot.db
CYCLE_DAYS=30
```

### 3. Build & Run
Run the multi-stage build and start the container in the background:
```bash
docker compose up -d --build
```

### 4. Verification & Monitoring
```bash
# Check container status and healthcheck
docker compose ps

# View live application logs
docker compose logs -f sportbot_app

# Inspect database backups
ls -lh ./backups/
```

### 5. Stopping the Service
```bash
# Graceful shutdown (saves state, truncates WAL, and exits cleanly)
docker compose down
```

---

## Local Development & Testing

### 1. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run automated tests
python3 tests/test_api_endpoints.py
python3 tests/test_bot_handlers.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run build
```

### 3. Launching Locally
```bash
python3 -m src.main
```
The FastAPI documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Healthcheck: `http://localhost:8000/health`

---

## Automated Backups & Maintenance

- Database file is persisted on the host at `./data/sportbot.db`.
- Daily hot backups are stored at `./backups/sportbot_backup_YYYYMMDD_HHMMSS.db`.
- Automatic rotation keeps the 7 most recent backups and purges older archives.
