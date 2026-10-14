# ТЕХНІЧНЕ ЗАВДАННЯ: Фаза 4. Telegram Mini App Frontend (Vite + React 18 + Tailwind) та запуск Cloudflare тунелю для ручного тестування

## 1. Мета та огляд
1. Створити повноцінний інтерфейс Telegram Mini App (React 18 + TypeScript + Tailwind CSS) в узгодженій стилістиці (Obsidian Black `#07040d`, Deep Purple, Crimson Red `#ef4444`).
2. Реалізувати 4 основні таби з нижньою навігацією:
   - `🔥 Workout`: екран тренування дня (Розминка, Вправи з підходами, Заминка, плаваючий таймер відпочинку Rest Timer HUD на 60с, кнопка завершення дня).
   - `🗓 Calendar`: 30-денна сітка з кольоровими блоками (Push, Pull, Legs, Rest), бейджами `completed` / `current` / `locked` та переглядом деталей будь-якого дня.
   - `📊 Progress`: аналітика, історія ваги тіла, модалка фіксації щомісячної ваги та модалка фінішу 30-го дня.
   - `📖 Guide`: довідник техніки калістеніки з фільтрами категорій та порадами для ваги 85 кг.
3. Підключити статичну роздачу зібраного фронтенду (`frontend/dist`) через FastAPI на порті `8000`.
4. Запустити локальний сервер та **Cloudflare Tunnel (`cloudflared`)** для надання публічного HTTPS URL, прив'язати його до `WEBAPP_URL` у `.env` та запустити бота для повного ручного тестування користувачем у Telegram на телефоні.

---

## 2. Структура файлів фронтенду

```text
frontend/src/
├── types.ts                     # TypeScript типи відповідей API (Pydantic контракт)
├── api.ts                       # HTTP-клієнт з передачею Telegram initData
├── components/
│   ├── Navigation.tsx           # Нижня панель перемикання 4 табів з Haptics
│   ├── RestTimerHUD.tsx         # Плаваючий таймер відпочинку (60s, +15s, -15s, Skip, вібрація)
│   ├── WorkoutTab.tsx           # Тренування дня: Warmup, Sets counters, Cooldown, Complete button
│   ├── CalendarTab.tsx          # 30-денна сітка, перегляд деталей обраного дня
│   ├── ProgressTab.tsx          # Статистика, фіксація ваги, модалка Milestone Day 30
│   └── GuideTab.tsx             # Бібліотека вправ з фільтрами та порадами техніки
├── App.tsx                      # Головний компонент (Header, активний таб, Navigation, Rules of Hooks)
├── main.tsx
└── index.css
```

---

## 3. Покрокові технічні вимоги

### БЛОК 1. Типізація та API-клієнт (`frontend/src/types.ts`, `frontend/src/api.ts`)
1. **`types.ts`:**
   - Повний опис моделей згідно з контрактами бекенду (`UserProfile`, `TodayWorkout`, `ExerciseDetail`, `WarmupStep`, `CooldownStep`, `CycleDaySummary`, `CycleDaysOverview`, `WeightRecord`, `AdminMetrics`).
2. **`api.ts`:**
   - Базовий URL відносний (`/api`).
   - Автоматичне додавання заголовка:
     `Authorization: tma ${window.Telegram?.WebApp?.initData || ""}`
     або `X-Dev-Telegram-Id: 8607080614` для тестування в браузері.
   - Методи: `fetchUserProfile()`, `updateDifficulty(mode)`, `fetchTodayWorkout()`, `completeWorkout(data)`, `fetchCycleDays()`, `fetchDayDetails(dayNumber)`, `logWeight(weight, cycle)`, `fetchWeightHistory()`.

### БЛОК 2. Компоненти інтерфейсу (Rules of Hooks & Aggressive Style)

1. **`RestTimerHUD.tsx` (Таймер відпочинку):**
   - Розрахунок від мітки часу `targetTime = Date.now() + durationSeconds * 1000`, що захищає від зупинки таймера при згортанні Telegram.
   - Плаваюча панель знизу екрана (вище таб-бару).
   - Кнопки: `+15s`, `-15s`, `Skip`.
   - По завершенні (0s) — виклик вібросигналу `Telegram.WebApp.HapticFeedback.notificationOccurred('success')`.

2. **`WorkoutTab.tsx` (Головне тренування):**
   - **Якщо день відпочинку (`is_rest_day = true`):**
     - Візуальна картка «🌴 REST & RECOVERY DAY».
     - Поради щодо сну, гідратації та відновлення м'язів.
   - **Якщо тренувальний день:**
     - Шапка: назва блоку (напр. `BLOCK A: PUSH`), фокусні м'язи (`Chest, Shoulders & Triceps`), орієнтовний час `50–55 min`.
     - **Секція 1: Dynamic Warm-up (8–10 min):**
       - 5 пунктів мобільності (Wrists, Shoulders, Scapular, Hips, Knees).
       - Чекбокс `[✓ Warm-up Completed]`.
     - **Секція 2: Main Calisthenics Protocol:**
       - Картки вправ за програмою поточного дня.
       - Відображення темпу `Tempo: 3-1-1`, рекомендованого відпочинку `Rest: 60s`, підказки щодо біомеханіки.
       - Інтерактивні кнопки сетів: `[Set 1: 12 reps ✓]`, `[Set 2: 12 reps ✓]`, `[Set 3: 12 reps ✓]`, `[Set 4: 12 reps ✓]`.
       - При натисканні на сет: вібрація `impactOccurred('medium')` та запуск Rest Timer HUD.
       - Стан підходів дублюється в `localStorage` (захист від втрати даних при згортанні додатка).
     - **Секція 3: Cool-down & Stretching (5–7 min):**
       - 4 вправи на розтяжку та нормалізацію дихання.
     - **Кнопка фіксації тренування:**
       - Велика червона кнопка: `🔥 COMPLETE WORKOUT (DAY X)`.
       - Відправка запиту на `POST /api/workout/complete`.
       - При успіху — переведення на наступний день та оновлення стейту.

3. **`CalendarTab.tsx` (30-денний календар):**
   - Сітка 30 днів (по 4 дні в блок: Push, Pull, Legs, Rest).
   - Візуальні бейджи: `Completed ✓`, `Current ●` (червоне пульсуюче світіння), `Locked 🔒`.
   - Модальне вікно перегляду будь-якого дня (вправи, сети, повторення — виключно для ознайомлення).

4. **`ProgressTab.tsx` (Прогрес і вага):**
   - Загальний прогрес циклу (Day X / 30, відсоток).
   - Блок ваги тіла: остання вага, історія замірів, кнопка `⚖️ Log Bodyweight` (модалка з інпутом ваги).
   - **Модалка Milestone Day 30:** якщо День 30 пройдено — святковий банер фінішу 30 днів, обов'язкове поле внесення ваги та кнопка `🚀 Start Next 30-Day Cycle`.

5. **`GuideTab.tsx` (Довідник вправ):**
   - Фільтри: `All`, `Push`, `Pull`, `Legs`, `Core`, `Cardio`.
   - Детальні картки всіх 12 вправ калістеніки з порадами безпеки для атлетів вагою 85 кг.

6. **`Navigation.tsx` та `App.tsx`:**
   - Нижня панель навігації (`Workout`, `Calendar`, `Progress`, `Guide`) з іконками та підсвіткою.
   - Відступ знизу `pb-24` для уникнення перекриття кнопок.
   - Дотримання **Rules of Hooks** (всі хуки зверху).

---

### БЛОК 3. Збірка та інтеграція в FastAPI (`src/api/app.py`)
1. Додати підтримку роздачі зібраного фронтенду:
   ```python
   import os
   from fastapi.staticfiles import StaticFiles

   frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
   if os.path.exists(frontend_dist):
       app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
   ```
2. Команда збірки: `cd frontend && npm run build`.

---

### БЛОК 4. Запуск Cloudflare тунелю та фонового сервера для ручного тестування
1. Зібрати фронтенд: `cd frontend && npm run build`.
2. Запустити `cloudflared` тунель на порт `8000`:
   `cloudflared tunnel --url http://localhost:8000`
3. Отримати публічний HTTPS URL (наприклад: `https://xxxx.trycloudflare.com`).
4. Оновити `WEBAPP_URL=https://xxxx.trycloudflare.com` у `.env` (або експортувати в оточення).
5. Запустити спільний процес бекенду та бота: `python3 -m src.main`.
6. Надати користувачеві чіткий звіт:
   - Публічне посилання тунелю.
   - Підтвердження, що бот слухає оновлення.
   - Інструкція для ручного тестування в Telegram.

---

## 4. Критерії приймання та перевірки (Acceptance Criteria)
1. **Збірка фронтенду:**
   `npm run build` у `frontend/` збирає проєкт без TypeScript або Rollup помилок.
2. **Інтегрована роздача:**
   `curl http://localhost:8000/` повертає `index.html` Mini App, а `curl http://localhost:8000/api/cycle/today` повертає JSON API.
3. **Хуки та стиль:**
   Rules of Hooks суворо дотримані. Дизайн відповідає узгодженій темній чорно-фіолетовій палітрі з червоними акцентами.
4. **Cloudflare Tunnel & Live Bot:**
   Сервер та тунель активні, бот відповідає на команду `/start`, кнопка `🔥 Open SportBot` відкриває повноцінний Mini App через HTTPS.
5. **Формат звіту:**
   Список модифікованих файлів, активний HTTPS URL тунелю та єдина команда git:
   `git add . && git commit -m "..." && git push origin main`.
