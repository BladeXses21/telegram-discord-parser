# TG Discord Interface

## Опис

Цей проект реалізує програму, яка автоматично взаємодіє з платформами Telegram та Discord. Вона забезпечує можливість пересилання повідомлень між заданими каналами та серверами.

## Функціонал

- Передача повідомлень між Telegram каналами та Discord серверами.
- Інтерфейс користувача для зміни налаштувань у реальному часі з використанням PyQt5.
- Можливість змінювати конфігураційні дані, такі як API ID, API Hash, Discord Token та інші.

## Вимоги

- Python 3.13.1
- Віртуальне середовище (рекомендується для ізоляції залежностей)

## Встановлення

1. **Клонування репозиторію:**

   ```bash
   git clone <URL вашого репозиторію>
   cd <назва папки з проектом>
   ```

2. **Створення та активація віртуального середовища:**

   - **Windows:**
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **Linux/macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Встановлення залежностей:**

   ```bash
   pip install -r requirements.txt
   ```

## Налаштування

### Отримання необхідних даних

- **Discord Token:** 
  1. У браузері скористайтеся клавішею F12, щоб викликати інструменти розробника. Якщо мова йде про клієнт Discord, то комбінація виглядає як Ctrl + Shift + I.
  2. У цьому вікні перейдіть на вкладку «Network».
  3. Напишіть будь-яке повідмолення у будь-який канал в discord.
  4. Після цього у консолі розробника в активності з`явиться новий елемент "message".
  5. Нажміть на цей елемент та відкрийте в ньому вкладку "Headers".
  6. В ньому потрібно знайти назву "Authorization" - це і є Ваш TOKEN. (не передавайте його нікому)

- **Target Discord Guild ID:**
  1. У Discord перейдіть до налаштувань користувача.
  2. Увімкніть "Developer Mode" у налаштуваннях теми.
  3. Перейдіть до серверу, від якого ви хочете отримати ID.
  4. Клацніть правою кнопкою на назву сервера і виберіть "Copy ID".

- **ID каналу в Telegram:**
  1. Перейдіть до вебверсії Telegram (`https://web.telegram.org`).
  2. Відкрийте канал і зверніть увагу на URL в адресному рядку.
  3. ID каналу буде частиною URL після `t.me/`, для приватних каналів це комплект символів після `t.me/c/`.

- **API ID та API Hash з Telegram:**
  1. Відвідайте сайт Telegram (`https://my.telegram.org`).
  2. Увійдіть у свій обліковий запис.
  3. Перейдіть до розділу "API development tools".
  4. Створіть новий додаток, і ви отримаєте ваш `api_id` та `api_hash`.

1. **Створіть або відредагуйте файл `config.json`:**

   ```json
   {
     "DISCORD_TOKEN": "ваш_discord_токен",
     "TARGET_GUILD_ID": "ваш_target_guild_id",
     "destination_channel_usernames": [
       "https://t.me/ваш_телеграм_канал"
     ],
     "source_channel_ids": [
       ваш_telegram_source_id
     ],
     "account": {
       "api_id": "ваш_api_id",
       "api_hash": "ваш_api_hash"
     }
   }
   ```

2. **Запуск програми:**

   Використайте наступну команду для запуску програми:

   ```bash
   python tg_discord_interface.py
   ```

## Використання

1. **Інтерфейс:** В інтерфейсі ви можете змінювати налаштування та зберігати їх за допомогою кнопки `Apply`.
2. **Запуск і зупинка служб:** Використовуйте кнопки `Start` і `Stop` для керування процесами Telegram і Discord.

## Підтримка

Якщо у вас виникають питання або проблеми, будь ласка, звертайтеся до [Ваш контактний email або платформа].