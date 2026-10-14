# ТЕХНІЧНЕ ЗАВДАННЯ: Фаза 3. Telegram-бот (Навігація, Меню, Інлайн-каталог вправ та Адмінка)

## 1. Мета та огляд
Розширити Telegram-бот (`aiogram 3`) до повноцінного диспетчера та контролера тренувального процесу `SportBot`.
Реалізувати:
1. Перманентну Reply-клавіатуру (Головне меню) із WebApp кнопкою швидкого запуску Mini App.
2. Щоденний огляд тренування дня (`🗓 Today's Workout`) із виведенням вправ, сетів, темпу (`3-1-1`) та часу відпочинку (60s).
3. Швидку статистику атлета в чаті (`📊 My Progress`).
4. Інтерактивний інлайн-каталог калістенічних вправ (`📖 Exercise Guide`) з категоріями та порадами безпеки для 85 кг.
5. Налаштування складності (`⚙️ Settings`) із можливістю перемикання рівнів (Light / Medium / Hard) прямо в боті.
6. Адмін-панель (`/admin`) із доступом лише для `ADMIN_IDS`.
7. `DbSessionMiddleware` для безпечного автоматичного прокидання сесій бази даних у хендлери та захист від збоїв парсингу через `html.escape()`.

---

## 2. Структура файлів бота

```text
src/bot/
├── __init__.py
├── instance.py          # Ініціалізація Bot, Dispatcher, реєстрація middleware та роутерів
├── middlewares.py       # DbSessionMiddleware (інжектує AsyncSession у хендлери)
├── keyboards.py         # Головне Reply-меню та інтерактивні Inline-клавіатури
└── handlers/
    ├── __init__.py
    ├── base.py          # /start, /help, базове вітання, JIT реєстрація
    ├── workout.py       # Обробник кнопки "Today's Workout"
    ├── progress.py      # Обробник кнопки "My Progress"
    ├── guide.py         # Обробник кнопки "Exercise Guide" та інлайн-навігація
    ├── settings.py      # Обробник кнопки "Settings" та перемикання складності
    └── admin.py         # /admin команда та системні метрики
```

---

## 3. Покрокові технічні вимоги

### БЛОК 1. Middleware та сесії БД (`src/bot/middlewares.py`)
1. Створити `DbSessionMiddleware(BaseMiddleware)`:
   - Відкриває асинхронну сесію через `async_session_maker()`.
   - Додає об'єкт `session: AsyncSession` у `data` події (повідомлення чи callback).
   - Забезпечує гарантоване закриття сесії в блоці `finally: await session.close()`.
2. Зареєструвати `DbSessionMiddleware` у `dp.message.middleware()` та `dp.callback_query.middleware()` у `src/bot/instance.py`.

### БЛОК 2. Клавіатури (`src/bot/keyboards.py`)
1. **Головне Reply-меню (`get_main_reply_keyboard()`):**
   - Рядок 1: `KeyboardButton(text="🔥 Open SportBot", web_app=WebAppInfo(url=settings.get_webapp_url()))`
   - Рядок 2: `KeyboardButton(text="🗓 Today's Workout")`, `KeyboardButton(text="📊 My Progress")`
   - Рядок 3: `KeyboardButton(text="📖 Exercise Guide")`, `KeyboardButton(text="⚙️ Settings")`
   - Параметри: `resize_keyboard=True`, `is_persistent=True`.
2. **Інлайн-клавіатури (`keyboards.py`):**
   - `get_workout_inline_kb()`: кнопка запуску Mini App `🚀 Start in App (web_app)`.
   - `get_guide_categories_kb()`: категорії `[Push]`, `[Pull]`, `[Legs]`, `[Core]`, `[Cardio]`.
   - `get_guide_exercises_kb(category)`: кнопки вправ обраної категорії + `[⬅️ Back to Categories]`.
   - `get_exercise_detail_kb(category)`: кнопка `[⬅️ Back to List]`.
   - `get_settings_kb(current_difficulty)`: інлайн-кнопки `🟢 Light`, `🟡 Medium`, `🔴 Hard` із позначкою активного режиму `(Current)`.

### БЛОК 3. Хендлери (Handlers)

#### 1. Базовий вхід (`src/bot/handlers/base.py`)
- Обробка `/start` та `/help`:
  - JIT реєстрація: перевіряє користувача в БД за `telegram_id`. Якщо новий — створює з `current_day=1`, `current_cycle=1`, `difficulty_mode="medium"`.
  - Формує вітальне повідомлення:
    ```html
    👋 Welcome to <b>SportBot</b>, {escaped_name}!

    Your personal 30-day calisthenics & bodyweight workout companion.
    • <b>Current Cycle:</b> Cycle {cycle} (Day {day}/30)
    • <b>Difficulty:</b> {difficulty}

    Use the menu below to launch the Mini App or explore today's workout.
    ```
  - Відправляє повідомлення з `reply_markup=get_main_reply_keyboard()` та `parse_mode="HTML"`.

#### 2. Огляд тренування дня (`src/bot/handlers/workout.py`)
- Обробка текстової кнопки `🗓 Today's Workout`:
  - Знаходить користувача та поточний `CycleDay` (`day_number = user.current_day`).
  - **Якщо день відпочинку (`is_rest_day=True`):**
    - Виводить картку: `🌴 DAY {day}/30: FULL RECOVERY & REST`.
    - Рекомендації: гідратація, 8+ годин сну, легка прогулянка 20-30 хв.
  - **Якщо тренувальний день:**
    - Виводить структуровану картку:
      ```html
      ⚡️ <b>DAY {day}/30 // {block_title}</b>
      🎯 <b>Focus:</b> {focus_areas}
      ⏱ <b>Target Duration:</b> 50–55 min

      <b>1. DYNAMIC WARM-UP (8–10 min):</b>
      • Wrists, shoulders, scapula, hips, and knees mobility drills.

      <b>2. MAIN PROTOCOL ({difficulty_tier}):</b>
      1. Parallel Bar Dips — 4 sets × 12 reps (Tempo: 3-1-1, Rest: 60s)
      ...

      <b>3. COOL-DOWN (5–7 min):</b>
      • Chest & lats wall stretch, deep diaphragmatic breathing.
      ```
    - Додає інлайн-кнопку `🚀 Open in Mini App` для переходу до таймера та чекбоксів.

#### 3. Статистика атлета (`src/bot/handlers/progress.py`)
- Обробка текстової кнопки `📊 My Progress`:
  - Агрегує з БД:
    - Поточний цикл і день: `Day {user.current_day} of 30 (Cycle {user.current_cycle})`.
    - Рівень навантаження: `{user.difficulty_mode.upper()}`.
    - Загальна кількість завершених тренувань (з `workout_logs`).
    - Останню зафіксовану вагу (з `weight_logs`).
    - Прогрес-бар поточного циклу (наприклад, `▓▓▓▓░░░░░░ 40%`).
  - Безпечний HTML-вивід.

#### 4. Інлайн-каталог вправ (`src/bot/handlers/guide.py`)
- Обробка текстової кнопки `📖 Exercise Guide`:
  - Відправляє інлайн-меню вибору категорій: `Push`, `Pull`, `Legs`, `Core`, `Cardio`.
- Обробка `callback_data` навігації:
  - `guide_cat:<category>`: виводить список вправ обраної категорії.
  - `guide_ex:<slug>`: виводить повну детальну картку вправи:
    - Назва та категорія.
    - Правильна техніка виконання.
    - 💡 **Safety Tips for 85 kg Bodyweight** (кути ліктів 45°, депресія лопаток, захист попереку при бігу та присіданнях).
    - Прогресії для рівнів `Light`, `Medium`, `Hard`.
  - `guide_home`: повернення до категорій.
  - Редагування повідомлення через `callback.message.edit_text(..., parse_mode="HTML")`.

#### 5. Налаштування складності (`src/bot/handlers/settings.py`)
- Обробка текстової кнопки `⚙️ Settings`:
  - Виводить статус:
    - Поточний рівень складності.
    - Опис режимів (Light: фундамент, Medium: робочий баланс, Hard: максимальна напруга та складні важелі).
  - Інлайн-кнопки перемикання: `🟢 Light`, `🟡 Medium`, `🔴 Hard`.
- Обробка `callback_data` (`set_diff:<mode>`):
  - Оновлює `user.difficulty_mode` у базі даних (`await session.commit()`).
  - Оновлює клавіатуру з позначкою `(Current)`.
  - Викликає `callback.answer("Difficulty updated to {mode}!", show_alert=False)`.

#### 6. Адмін-панель (`src/bot/handlers/admin.py`)
- Обробка команди `/admin`:
  - Перевіряє `message.from_user.id in settings.admin_ids_list`. Якщо ні — ігнорує або відповідає `⛔️ Access denied`.
  - Для адміна:
    - Загальна кількість зареєстрованих користувачів.
    - Загальна кількість залогованих тренувань.
    - Розподіл користувачів за складністю.
    - Інлайн-кнопка `🔄 Refresh Metrics`.

---

### БЛОК 4. Реєстрація у `src/bot/instance.py`
- Підключити всі нові роутери: `base`, `workout`, `progress`, `guide`, `settings`, `admin`.
- Перевірити коректність ініціалізації: якщо `BOT_TOKEN` відсутній або некоректний — бот безпечно логує попередження без аварійної зупинки API.

---

## 4. Критерії приймання та перевірки (Acceptance Criteria)
1. **Синтаксична цілісність:**
   `python3 -m py_compile src/bot/*.py src/bot/handlers/*.py` завершується з кодом 0.
2. **Безпека:**
   Усі динамічні текстові поля проходять через `html.escape()`. Немає вразливості до зламаного HTML.
3. **Функціональність:**
   Створити перевірочний скрипт або тести для валідації генерації клавіатур та формування текстових карток.
4. **Формат звіту:**
   Список модифікованих/створених файлів та єдина команда git:
   `git add . && git commit -m "..." && git push origin main`.
