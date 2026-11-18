# Discord AI Bot

Discord бот с AI, который отвечает на сообщения когда его пингуют.

## Особенности

- Отвечает только когда бота пингуют (@BotName)
- Использует Router AI API с моделью MythoMax 13B
- Настраиваемый системный промпт для характера бота

## Установка

1. **Установи зависимости:**
```bash
pip install -r requirements.txt
```

2. **Создай файл `.env` и добавь ключи:**
```env
DISCORD_TOKEN=твой_discord_token
ROUTER_AI_KEY=твой_router_ai_ключ
```

### Получение ключей

**Discord Token:**
1. Перейди на https://discord.com/developers/applications
2. Создай новое приложение (New Application)
3. Перейди в раздел "Bot" → "Add Bot"
4. Скопируй токен и вставь в `.env`

**Router AI Key:**
1. Перейди на https://routerai.ru
2. Зарегистрируйся и получи API ключ
3. Вставь в `.env`

### Настройка Discord бота

1. В Developer Portal перейди в "Bot"
2. Включи **Privileged Gateway Intents**:
   - ✅ MESSAGE CONTENT INTENT
   - ✅ SERVER MEMBERS INTENT
   - ✅ PRESENCE INTENT
3. Перейди в "OAuth2" → "URL Generator"
4. Выбери scopes: `bot`
5. Выбери permissions: `Send Messages`, `Read Message History`, `Mention Everyone`
6. Скопируй ссылку и добавь бота на сервер

## Запуск

```bash
python bot.py
```

## Настройка характера бота

Открой `bot.py` и измени `system_prompt` (строка ~70) на любой характер:

```python
system_prompt = """ТУТ ОПИСАНИЕ ХАРАКТЕРА БОТА"""
```

Можно изменить температуру (0.1 = скучно, 2.0 = хаос) в строке `temperature`.

## Использование

Просто пингуй бота в Discord:
```
@BotName привет!
```

## Структура проекта

```
.
├── bot.py              # Основной скрипт бота
├── requirements.txt    # Зависимости Python
├── .env               # Секретные ключи (НЕ в Git!)
└── README.md          # Эта инструкция
```

## Требования

- Python 3.8+
- Discord account
- Router AI API key
