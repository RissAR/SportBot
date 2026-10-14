# ТЕХНІЧНЕ ЗАВДАННЯ: Фаза 2. Захищений REST API (FastAPI, Telegram HMAC-SHA256, Pydantic v2 та Race Condition Lock)

## 1. Мета та огляд
Створити безпечний REST API бекенд на базі FastAPI, що забезпечує:
1. Криптографічну валідацію `initData` Telegram Mini App (HMAC-SHA256) із захистом від replay-атак та безпечним DEV-фолбеком для локальної розробки.
2. Автоматичне створення профілю атлета (JIT User Provisioning) при першому вході.
3. Ендпоінти отримання щоденного тренування з фіксованими блоками розминки (Warm-up) та заминки (Cool-down).
4. Суворе правило: пройдені дні доступні **лише для перегляду**; завершити можна тільки поточний активний день (`user.current_day`).
5. Захист від подвійного тапу / стану гонитви (`asyncio.Lock` на рівні кожного користувача).
6. Фіксацію щомісячної ваги та перехід на новий 30-денний цикл.
7. Захищені ендпоінти метрик для адміністратора (`ADMIN_IDS`).

---

## 2. Структура файлів API

```text
src/api/
├── __init__.py
├── app.py               # Точка збірки FastAPI, CORS, Anti-Cache, підключення роутерів
├── auth.py              # HMAC-SHA256 валідація Telegram initData, get_current_user, verify_admin
├── schemas.py           # Pydantic v2 моделі запитів та відповідей (Contract First)
└── routes/
    ├── __init__.py
    ├── users.py         # /api/user (профіль, зміна складності)
    ├── cycle.py         # /api/cycle (тренування дня, 30-денний календар, перегляд)
    ├── workout.py       # /api/workout/complete (фіксація тренування з asyncio.Lock)
    ├── weight.py        # /api/weight (фіксація ваги, історія)
    └── admin.py         # /api/admin/metrics (статистика для адміна)
```

---

## 3. Покрокові технічні вимоги

### БЛОК 1. Автентифікація Telegram initData (`src/api/auth.py`)
1. **Алгоритм валідації HMAC-SHA256:**
   - Отримання рядка `init_data` з заголовка `Authorization: tma <init_data>` або `X-Telegram-Init-Data`.
   - Якщо `settings.DEBUG is True` та заголовок відсутній — дозволити емуляцію через заголовок `X-Dev-Telegram-Id` або використання `settings.admin_ids_list[0]`. У продакшені (`DEBUG=False`) відхиляти всі непідписані запити (HTTP 401).
   - Розрахунок `secret_key`:
     `hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()`
   - Парсинг параметрів, сортування ключів за алфавітом (виключаючи `hash`), об'єднання через `\n`.
   - Обчислення контрольного хешу та звірка через `hmac.compare_digest`.
   - Перевірка `auth_date` (запит не старіший за 86400 секунд).
2. **Dependency `get_current_user`:**
   - Витягує `telegram_id`, `username`, `first_name` з розпарсеного `user` JSON.
   - Шукає користувача в базі даних:
     - Якщо знайдено — повертає об'єкт `User`.
     - Якщо користувача немає — атомарно створює нового (`telegram_id`, `username`, `current_day=1`, `current_cycle=1`, `difficulty_mode="medium"`).
3. **Dependency `verify_admin`:**
   - Перевіряє `user.telegram_id in settings.admin_ids_list`. Якщо ні — викликає `HTTPException(status_code=403, detail="Admin access required")`.

---

### БЛОК 2. Контракти даних (Pydantic v2 у `src/api/schemas.py`)
Усі схеми та повідомлення строго англійською мовою:

1. **Користувач:**
   - `UserProfileResponse`: `telegram_id: int`, `username: Optional[str]`, `current_day: int`, `current_cycle: int`, `difficulty_mode: str`, `total_workouts_completed: int`, `latest_weight: Optional[float]`.
   - `DifficultyUpdateRequest`: `difficulty_mode: Literal['light', 'medium', 'hard']`.
2. **Розминка та Заминка (Фіксовані списки):**
   - `WarmupStep`: `order: int`, `title: str`, `duration_seconds: int`, `description: str`.
   - `CooldownStep`: `order: int`, `title: str`, `duration_seconds: int`, `description: str`.
3. **Тренування та Вправи:**
   - `ExerciseDetailResponse`: `id: int`, `slug: str`, `name: str`, `category: str`, `metric_type: str`, `progression_name: str`, `target_sets: int`, `target_value: int`, `tempo: str`, `rest_seconds: int`, `description: str`, `technique_tips: str`.
   - `TodayWorkoutResponse`: `day_number: int`, `cycle_number: int`, `block_type: str`, `title: str`, `focus_areas: str`, `is_rest_day: bool`, `warmup_steps: list[WarmupStep]`, `exercises: list[ExerciseDetailResponse]`, `cooldown_steps: list[CooldownStep]`, `recovery_guidelines: Optional[str]`.
   - `CycleDaySummary`: `day_number: int`, `block_type: str`, `title: str`, `focus_areas: str`, `is_rest_day: bool`, `status: Literal['completed', 'current', 'locked']`.
   - `CycleDaysOverviewResponse`: `cycle_number: int`, `current_day: int`, `days: list[CycleDaySummary]`.
4. **Завершення тренування:**
   - `WorkoutExerciseInput`: `exercise_id: int`, `sets_completed: int`, `value_completed: int`, `is_completed: bool`.
   - `WorkoutCompleteRequest`: `day_number: int`, `cycle_number: int`, `duration_seconds: int`, `difficulty_mode: str`, `exercises: list[WorkoutExerciseInput]`.
   - `WorkoutCompleteResponse`: `success: bool`, `message: str`, `cycle_completed: bool`, `next_day: int`, `next_cycle: int`.
5. **Вага та Метрики:**
   - `WeightLogRequest`: `weight_kg: float`, `cycle_number: int`.
   - `WeightLogResponse`: `id: int`, `weight_kg: float`, `cycle_number: int`, `logged_at: str`, `is_cycle_reset: bool`.
   - `WeightHistoryResponse`: `history: list[dict]`.
   - `AdminMetricsResponse`: `total_athletes: int`, `total_workouts_completed: int`, `difficulty_distribution: dict[str, int]`, `active_cycles_distribution: dict[int, int]`.

---

### БЛОК 3. Маршрутизація та бізнес-правила (Routers)

#### 1. `src/api/routes/users.py`
- `GET /api/user/me`: повертає `UserProfileResponse`.
- `PATCH /api/user/difficulty`: валідує новий режим, оновлює `user.difficulty_mode`, повертає оновлений профіль.

#### 2. `src/api/routes/cycle.py`
- `GET /api/cycle/today`:
  - Знаходить `CycleDay` для `user.current_day`.
  - Якщо `is_rest_day is True`: повертає `exercises=[]`, наповнені `recovery_guidelines` (гідратація, сон 8+ годин, легка прогулянка 20-30 хв).
  - Якщо тренувальний день: підтягує вправи через `CycleDayExercise`, вибирає прогресію відповідно до `user.difficulty_mode`, повертає повну структуру з 5 кроками розминки (Wrists, Shoulders, Scapula, Hips, Knees) та 4 кроками заминки (Chest, Lats, Cat-cow, Diaphragm).
- `GET /api/cycle/days`:
  - Повертає статус для кожного з 30 днів:
    - `day_number < user.current_day` ➔ `status = 'completed'`
    - `day_number == user.current_day` ➔ `status = 'current'`
    - `day_number > user.current_day` ➔ `status = 'locked'`
- `GET /api/cycle/days/{day_number}`:
  - Дозволяє переглянути деталі будь-якого дня (включаючи минулі). Лише для ознайомлення.

#### 3. `src/api/routes/workout.py` (Race Condition Protection)
- `POST /api/workout/complete`:
  - **Критична перевірка:** `if req.day_number != user.current_day:` ➔ викликати `HTTPException(400, "Only the current day workout can be completed. Past days are view-only.")`.
  - Застосувати блокування `asyncio.Lock` по `user.id` (наприклад, через словник блокувань `user_locks = defaultdict(asyncio.Lock)`).
  - Перевірити, чи немає вже запису `WorkoutLog` для `(user.id, user.current_cycle, req.day_number)`.
  - Зберегти `WorkoutLog` та детальні `WorkoutExerciseLog`.
  - Логіка переходу днів:
    - Якщо `user.current_day < 30`:
      `user.current_day += 1`
      `cycle_completed = False`
    - Якщо `user.current_day == 30`:
      `cycle_completed = True` (день залишається 30 до фіксації ваги).
  - Зберегти транзакцію (`db.commit()`), повернути `WorkoutCompleteResponse`.

#### 4. `src/api/routes/weight.py`
- `POST /api/weight`:
  - Зберігає `WeightLog(user_id=user.id, weight_kg=req.weight_kg, cycle_number=req.cycle_number)`.
  - Якщо `user.current_day == 30`:
    - Скидає `user.current_day = 1`.
    - Збільшує `user.current_cycle += 1`.
    - `is_cycle_reset = True`.
  - Повертає `WeightLogResponse`.
- `GET /api/weight/history`: повертає всі записи ваги користувача, впорядковані за часом.

#### 5. `src/api/routes/admin.py`
- `GET /api/admin/metrics`:
  - Захищено `Depends(verify_admin)`.
  - Агрегує підрахунок користувачів, логів тренувань, розподілу за складністю.

---

### БЛОК 4. Реєстрація у `src/api/app.py`
- Підключити всі роутери через `app.include_router(..., prefix="/api")`.
- Зберегти роботу Anti-Cache middleware для роутів `/app*` та CORS.
- Додати обробку глобальних винятків для повернення чистих JSON-помилок.

---

## 4. Критерії приймання та верифікація (Acceptance Criteria)
1. **Синтаксична цілісність:**
   `python3 -m py_compile src/api/auth.py src/api/schemas.py src/api/routes/*.py src/api/app.py` завершується з кодом 0.
2. **Тестування API:**
   Створити та виконати тестовий скрипт (наприклад, `tests/test_api_endpoints.py`), який перевіряє:
   - `GET /api/user/me` повертає профіль (включаючи створення нового користувача JIT).
   - `GET /api/cycle/today` повертає тренування дня 1 із кроками Warm-up, вправами та Cool-down.
   - `POST /api/workout/complete` успішно фіксує День 1 і переводить `user.current_day` на День 2.
   - Спроба завершити вже пройдений День 1 повертає `400 Bad Request`.
   - `POST /api/weight` успішно записує вагу.
3. **Безпека:**
   Жодних токенів у репозиторії. Неавторизований запит без `initData` при `DEBUG=False` повертає 401.
4. **Формат звіту:**
   Список створених/модифікованих файлів та єдина команда git:
   `git add . && git commit -m "..." && git push origin main`.
