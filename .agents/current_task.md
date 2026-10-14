# ТЕХНІЧНЕ ЗАВДАННЯ: Фаза 1. База даних, реляційні моделі та ядро 30-денної програми калістеніки

## 1. Мета та огляд
Створити асинхронну реляційну базу даних на базі SQLAlchemy 2.0 (asyncio + aiosqlite), реалізувати схему моделей для атлетів, вправ з власною вагою, 3 рівнів складності, 30-денного циклу тренувань та щомісячної фіксації ваги. Написати ідемпотентний сід-скрипт (`src/db/seed.py`), який заповнить базу всіма 30 днями та повним каталогом вправ за програмою.

---

## 2. Структура нових файлів

```text
src/
└── db/
    ├── __init__.py
    ├── session.py       # async engine, aiosqlite, WAL режим, init_db()
    ├── models.py        # Реляційні моделі SQLAlchemy 2.0
    └── seed.py          # Сід-скрипт 30-денного циклу та калістенічних вправ
```

---

## 3. Покрокові технічні вимоги

### БЛОК 1. Сесії БД та SQLite WAL конфігурація (`src/db/session.py`)
1. Використовувати `settings.DATABASE_URL` (за замовчуванням `sqlite+aiosqlite:///data/sportbot.db`).
2. Створити `create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)`.
3. Реалізувати слухач з'єднання (`connect`) для активації режиму високої надійності та паралелізму SQLite:
   ```python
   from sqlalchemy import event

   @event.listens_for(engine.sync_engine, "connect")
   def set_sqlite_pragma(dbapi_connection, connection_record):
       cursor = dbapi_connection.cursor()
       cursor.execute("PRAGMA journal_mode=WAL")
       cursor.execute("PRAGMA busy_timeout=5000")
       cursor.execute("PRAGMA synchronous=NORMAL")
       cursor.close()
   ```
4. Надати асинхронний контекстний менеджер/генератор `get_db_session()` через `async_sessionmaker(expire_on_commit=False)`.
5. Функція `init_db()`: створення всіх таблиць (`Base.metadata.create_all`).

### БЛОК 2. Моделі бази даних (`src/db/models.py`)
Всі моделі наслідуються від `DeclarativeBase`. Англійські найменування сутностей:

1. **`User` (таблиця `users`):**
   - `id`: Integer, Primary Key.
   - `telegram_id`: BigInteger, unique, indexed, nullable=False.
   - `username`: String(64), nullable=True.
   - `current_day`: Integer, default=1 (діапазон 1..30).
   - `current_cycle`: Integer, default=1.
   - `difficulty_mode`: String(16), default="medium" ('light', 'medium', 'hard').
   - `created_at`: DateTime(timezone=True), server_default=func.now().
   - `updated_at`: DateTime(timezone=True), onupdate=func.now().

2. **`Exercise` (таблиця `exercises`):**
   - `id`: Integer, Primary Key.
   - `slug`: String(64), unique, indexed (напр: `dips`, `decline_pushups`, `pike_pushups`, `pullups`, `chinups`, `horizontal_rows`, `toes_to_bar`, `l_sit_bars`, `bulgarian_split_squats`, `cossack_squats`, `running_intervals`, `running_zone2`).
   - `name`: String(128) (English, напр: "Parallel Bar Dips").
   - `category`: String(32) ('push', 'pull', 'legs', 'core', 'cardio').
   - `metric_type`: String(16) ('reps', 'seconds', 'minutes').
   - `description`: Text (English: правильна біомеханіка, техніка виконання).
   - `technique_tips`: Text (English: акценти, захист суглобів при 85 кг, депресія лопаток, кут ліктів 45°).

3. **`ExerciseProgression` (таблиця `exercise_progressions`):**
   - `id`: Integer, Primary Key.
   - `exercise_id`: Integer, ForeignKey('exercises.id', ondelete='CASCADE').
   - `difficulty_tier`: String(16) ('light', 'medium', 'hard').
   - `progression_name`: String(128) (напр: 'Straight Bar Dips', 'Archer Push-ups', 'Elevated Pike', 'L-Sit Pull-ups').
   - `target_sets`: Integer (напр. 3 або 4).
   - `target_value`: Integer (кількість повторень, секунд або хвилин).
   - `tempo`: String(16), default="3-1-1" (темп руху для гіпертрофії та безпеки).
   - `rest_seconds`: Integer, default=60 (рекомендований відпочинок між сетами).

4. **`CycleDay` (таблиця `cycle_days`):**
   - `id`: Integer, Primary Key.
   - `day_number`: Integer, unique, indexed (від 1 до 30).
   - `block_type`: String(32) ('A_PUSH', 'B_PULL', 'C_LEGS_RUN', 'REST').
   - `title`: String(128) (напр: 'Day 1: Upper Body Push', 'Day 4: Full Recovery').
   - `focus_areas`: String(128) (напр: 'Chest, Shoulders & Triceps').
   - `is_rest_day`: Boolean, default=False.

5. **`CycleDayExercise` (таблиця `cycle_day_exercises`):**
   - `id`: Integer, Primary Key.
   - `cycle_day_id`: Integer, ForeignKey('cycle_days.id', ondelete='CASCADE').
   - `exercise_id`: Integer, ForeignKey('exercises.id', ondelete='CASCADE').
   - `order`: Integer, default=1.

6. **`WorkoutLog` (таблиця `workout_logs`):**
   - `id`: Integer, Primary Key.
   - `user_id`: Integer, ForeignKey('users.id', ondelete='CASCADE'), indexed=True.
   - `cycle_number`: Integer.
   - `day_number`: Integer.
   - `difficulty_mode`: String(16).
   - `duration_seconds`: Integer, default=0.
   - `completed_at`: DateTime(timezone=True), server_default=func.now().

7. **`WorkoutExerciseLog` (таблиця `workout_exercise_logs`):**
   - `id`: Integer, Primary Key.
   - `workout_log_id`: Integer, ForeignKey('workout_logs.id', ondelete='CASCADE').
   - `exercise_id`: Integer, ForeignKey('exercises.id').
   - `sets_completed`: Integer.
   - `value_completed`: Integer (фактичні reps / seconds).
   - `is_completed`: Boolean, default=True.

8. **`WeightLog` (таблиця `weight_logs`):**
   - `id`: Integer, Primary Key.
   - `user_id`: Integer, ForeignKey('users.id', ondelete='CASCADE'), indexed=True.
   - `cycle_number`: Integer.
   - `weight_kg`: Float.
   - `logged_at`: DateTime(timezone=True), server_default=func.now().

---

### БЛОК 3. Сід-скрипт 30-денної програми (`src/db/seed.py`)
Реалізувати асинхронну функцію `seed_initial_data()`, яка перевіряє наявність даних і наповнює базу:

1. **12 Базових вправ (`exercises`) із точними описами та порадами:**
   - **Push:**
     - `dips`: Parallel Bar Dips (45° angle, hollow core).
     - `decline_pushups`: Decline Push-ups (feet on 30-50cm bench, upper chest & front delts).
     - `pike_pushups`: Pike Push-ups (L-shape body, triangle push trajectory for shoulders).
   - **Pull & Core:**
     - `pullups`: Pull-ups overhand (active scapular depression, chest to bar).
     - `chinups`: Chin-ups underhand (peak biceps contraction).
     - `horizontal_rows`: Australian Rows (neutral/overhand, protects rotator cuff against heavy pushing).
     - `toes_to_bar`: Hanging Toes-to-Bar (controlled core flexion without swing).
     - `l_sit_bars`: L-Sit on Parallel Bars (isometric core & hip flexor hold, 15-25s).
   - **Legs & Cardio:**
     - `bulgarian_split_squats`: Bulgarian Split Squats (deep single-leg load without spinal compression).
     - `cossack_squats`: Cossack Squats (hip mobility, adductors & knee ligament resilience).
     - `running_intervals`: Interval Running (60s high-intensity sprint + 90s walk recovery).
     - `running_zone2`: Steady Zone 2 Tempo Run (25-30 min nose-breathing aerobic recovery).

2. **Прогресії складності (`exercise_progressions`):**
   - Для кожної вправи заповнити `light`, `medium`, `hard` рівні з відповідними `target_sets`, `target_value` (до 20 повторень для сили/маси згідно з ТЗ), `tempo="3-1-1"` та `rest_seconds=60`.

3. **Генерація 30 Днів Циклу (`cycle_days` та зв'язок `cycle_day_exercises`):**
   - Реалізувати через формулу ротації:
     - `day % 4 == 1` ➔ `A_PUSH` (вправи: dips, decline_pushups, pike_pushups).
     - `day % 4 == 2` ➔ `B_PULL` (вправи: pullups, chinups, horizontal_rows, toes_to_bar, l_sit_bars).
     - `day % 4 == 3` ➔ `C_LEGS_RUN` (вправи: bulgarian_split_squats, cossack_squats + біг: якщо непарний день ніг — `running_intervals`, якщо парний — `running_zone2`).
     - `day % 4 == 0` ➔ `REST` (`is_rest_day=True`, без вправ, заголовок "Full Recovery & Mobility").

4. **Точка виклику:**
   - Додати блок `if __name__ == "__main__": asyncio.run(seed_initial_data())` для запуску через CLI.
   - Інтегрувати виклик `init_db()` та `seed_initial_data()` в подію старту програми у `src/main.py`.

---

## 4. Критерії приймання та перевірки (Acceptance Criteria)
1. **Синтаксис та компіляція:**
   `python3 -m py_compile src/db/session.py src/db/models.py src/db/seed.py src/main.py` проходить без помилок.
2. **Сідінг бази даних:**
   Команда `python3 -m src.db.seed` успішно створює файл бази `data/sportbot.db` і наповнює її.
3. **Цілісність даних:**
   Перевірочний запит підтверджує:
   - 30 записів у `cycle_days` (з них 23 активних, 7 днів `is_rest_day=True`).
   - 12 записів у `exercises`.
   - 36 записів у `exercise_progressions` (по 3 на кожну вправу).
4. **Формат звіту:**
   Надати список модифікованих/створених файлів та єдину команду git:
   `git add . && git commit -m "..." && git push origin main`.
