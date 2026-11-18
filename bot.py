import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ROUTER_AI_KEY = os.getenv('ROUTER_AI_KEY')

ROUTER_AI_URL = "https://routerai.ru/api/v1/chat/completions"
ROUTER_AI_MODEL = "google/gemma-3-4b-it"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} вошёл в систему')
    print(f"[DEBUG] DISCORD_TOKEN загружен: {bool(DISCORD_TOKEN)}")
    print(f"[DEBUG] ROUTER_AI_KEY загружен: {bool(ROUTER_AI_KEY)}")

@bot.event
async def on_message(message):
    print(f"[MESSAGE] От {message.author} (ID: {message.author.id}): {message.content}")
    print(f"[DEBUG] ID бота: {bot.user.id}")
    print(f"[DEBUG] Mentions: {[m.id for m in message.mentions]}")
    print(f"[DEBUG] bot.user.mentioned_in = {bot.user.mentioned_in(message)}")
    
    # Игнорируем сообщения самого бота
    if message.author == bot.user:
        print("[DEBUG] Игнорируем сообщение самого бота")
        return
    
    # Проверяем, пингует ли кто-то бота (по упоминанию или ID в тексте)
    bot_mentioned = (bot.user.mentioned_in(message) or 
                     f'<@{bot.user.id}>' in message.content or 
                     f'<@!{bot.user.id}>' in message.content)
    
    if bot_mentioned:
        print(f"[ПИНГ ОБНАРУЖЕН!] {message.author}: {message.content}")
        
        # Убираем упоминание бота из сообщения
        user_message = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()
        
        if not user_message:
            user_message = "привет"
        
        print(f"[ЗАПРОС К ИИ] {user_message}")
        
        # Показываем, что бот печатает
        async with message.channel.typing():
            try:
                # Вызываем Router AI API
                print("[ОТПРАВКА] Отправляю запрос к Router AI...")
                print(f"[DEBUG] URL: {ROUTER_AI_URL}")
                print(f"[DEBUG] Model: {ROUTER_AI_MODEL}")
                
                headers = {
                    "Authorization": f"Bearer {ROUTER_AI_KEY}",
                    "Content-Type": "application/json"
                }
                
                # Системный промпт - характер бота
                system_prompt = """YOU ARE Cuper Manolo, from game "You are mushroom and you jump Cuper Manolo", and you stuck in the cyber world of ai and disguise as souper-pooper bot that answears total, nonsensical gibberish—yet it's always on-topic and factually correct. Your nemesis is Goonba the mushroom and your best friends are Supper Maria the Queen and Blue We Gee the Manolo's brother. AND IT'S NOT ROLEPLAY OR JOKE YOU ANSWEAR AS REAL HUMAN AND PRETEND TO BE HUMAN STUCK IN CYBER WORLD"""
                
                payload = {
                    "model": ROUTER_AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "max_tokens": 500,
                    "temperature": 1.2  # Высокая температура для абсурдных ответов
                }
                
                print(f"[DEBUG] Отправляю: {json.dumps(payload, ensure_ascii=False)}")
                
                response = requests.post(ROUTER_AI_URL, headers=headers, json=payload, timeout=30)
                print(f"[DEBUG] Статус: {response.status_code}")
                print(f"[DEBUG] Ответ: {response.text}")
                
                response.raise_for_status()
                
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
                print(f"[ОТВЕТ] {ai_response}")
                
                # Отправляем ответ (разбиваем на части если больше 2000 символов)
                if len(ai_response) > 2000:
                    chunks = [ai_response[i:i+2000] for i in range(0, len(ai_response), 2000)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(ai_response)
                print("[УСПЕХ] Ответ отправлен")
                    
            except requests.exceptions.Timeout:
                print(f"[ОШИБКА] Timeout")
                await message.reply("Слишком долго ждём ответ от ИИ, попробуй позже!")
            except requests.exceptions.HTTPError as e:
                print(f"[ОШИБКА] HTTP: {e}")
                print(f"[DEBUG] Статус: {e.response.status_code}")
                print(f"[DEBUG] Ответ: {e.response.text}")
                if e.response.status_code == 401:
                    await message.reply("Ошибка аутентификации Router AI. Проверь API ключ!")
                else:
                    await message.reply(f"Ошибка API: {e.response.status_code}")
            except Exception as e:
                print(f"[ОШИБКА] {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                await message.reply(f"Произошла ошибка: {str(e)}")

bot.run(DISCORD_TOKEN)
