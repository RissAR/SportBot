# SportBot: Autonomous 30-Day Calisthenics Engine & Telegram Mini App

An autonomous, zero-maintenance personal calisthenics training platform combining an **aiogram 3** Telegram bot, a **FastAPI** backend with asynchronous SQLite (WAL mode), and a high-performance **Telegram Mini App (TMA)** built with React 18, TypeScript, and Tailwind CSS (Clean Athletic Stealth Dark design).

---

## Key Features

- **Personalized 30-Day Calisthenics Periodization:**
  - Block A: Push (Pecs, Delts, Triceps)
  - Block B: Pull (Lats, Upper Back, Biceps, Core)
  - Block C: Legs & Conditioning (Quads, Posterior Chain, Zone 2 / Sprint Intervals)
  - Active Rest & Central Nervous System Recovery days
- **Telegram Mini App (TMA):**
  - **Workout View:** Smart-collapsible Warm-up and Cool-down accordions, interactive set completion counters, and exercise technique info modal.
  - **Rest Timer HUD:** Persistent countdown timer calculated via target timestamp (safe against app minimization) with haptic feedback.
  - **Calendar View:** Clean 30-day block grid with inspection modal and progress badges.
  - **Progress View:** Cycle progress, bodyweight tracking with monthly logs, and dynamic difficulty adjustment (`light`, `medium`, `hard`).
  - **Guide View:** Encyclopedia of 12 bodyweight progressions with safety tips tailored for 85 kg athletes.
- **Autonomous Longevity & Hardening:**
  - **Daily Reminder Worker:** Automated 09:00 morning check-in for athletes with incomplete workouts (1 push/day anti-spam protection).
  - **Automated Database Backups:** Hot atomic SQLite `VACUUM INTO` backup service with rolling 7-day retention and WAL checkpoints.
  - **Graceful Shutdown:** Intercepts `SIGINT`/`SIGTERM`, safely completes pending requests, stops polling, and truncates the WAL journal (`PRAGMA wal_checkpoint(TRUNCATE)`).

---

## Architecture Overview

```text
SportBot/
├── Dockerfile                   # Multi-stage production build (Node 20 -> Python 3.11)
├── docker-compose.yml           # Production orchestrator with container healthcheck
├── src/
│   ├── main.py                  # Concurrent runner (FastAPI, Bot, Workers, Graceful Shutdown)
│   ├── config.py                # Pydantic v2 settings (Zero Hardcoded Secrets)
│   ├── api/                     # FastAPI REST API, auth (Telegram initData), and static SPA serving
│   ├── bot/                     # aiogram 3 bot handlers and inline keyboards
│   ├── db/                      # SQLAlchemy 2.0 models, aiosqlite engine, and seed data
│   └── services/                # Autonomous background workers (Reminder, Backup)
└── frontend/                    # React 18, Vite, TypeScript, Tailwind CSS Mini App
```

---

## Deployment & Production Setup (VPS)

### 1. Prerequisites
- Docker Engine 24.0+ & Docker Compose v2+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Clone and Configure
```bash
git clone https://github.com/andriy-dofi/SportBot.git
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
# Check container status and health
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

## Automated Backups & Maintenance

- Database file is persisted on the host at `./data/sportbot.db`.
- Daily hot backups are stored at `./backups/sportbot_backup_YYYYMMDD_HHMMSS.db`.
- Automatic rotation automatically keeps the 7 most recent backups and purges older archives.
