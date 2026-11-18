import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
import json
import time
import asyncio

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ROUTER_AI_KEY = os.getenv('ROUTER_AI_KEY')

ROUTER_AI_CHAT_URL = "https://routerai.ru/api/v1/chat/completions"
ROUTER_AI_VIDEO_URL = "https://routerai.ru/api/v1/videos"
ROUTER_AI_MODEL = "google/gemma-3-4b-it"
VIDEO_MODEL = "tbc/mischief-1"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Функция генерации видео через Mischief 1
async def generate_video(prompt, message):
    """Генерирует видео через Router AI Mischief-1"""
    try:
        print(f"[VIDEO] Генерация видео: {prompt}")
        await message.channel.send("🎬 Starting video generation... Let's generate the first frame, then animate it (1-2 minutes)")
        
        headers = {
            "Authorization": f"Bearer {ROUTER_AI_KEY}",
            "Content-Type": "application/json"
        }
        
        # Шаг 1: Генерируем первый кадр (изображение)
        print("[VIDEO] Шаг 1: Генерация первого кадра...")
        image_payload = {
            "model": "recraft/recraft-v4.1-flash-v2",
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "n": 1
        }
        
        image_response = requests.post(
            "https://routerai.ru/api/v1/images/generations",
            headers=headers,
            json=image_payload,
            timeout=60
        )
        print(f"[VIDEO DEBUG] Статус генерации картинки: {image_response.status_code}")
        
        image_response.raise_for_status()
        image_data = image_response.json()
        
        print(f"[VIDEO DEBUG] Ответ API картинки: {json.dumps(image_data, ensure_ascii=False)[:300]}")
        
        # Получаем base64 или URL первого кадра
        first_frame_url = None
        first_frame_base64 = None
        
        # Проверяем разные форматы ответа
        if "data" in image_data and isinstance(image_data["data"], list) and len(image_data["data"]) > 0:
            first_item = image_data["data"][0]
            first_frame_url = first_item.get("url")
            first_frame_base64 = first_item.get("b64_json")
        
        # Если есть base64, преобразуем в data URI для использования в API
        if first_frame_base64 and not first_frame_url:
            # Router AI принимает data URI напрямую
            first_frame_url = f"data:image/jpeg;base64,{first_frame_base64}"
            print(f"[VIDEO] Используем base64 картинку (длина: {len(first_frame_base64)})")
        
        if not first_frame_url:
            await message.channel.send(f"❌ Failed to find an image in API answear ")
            return
        
        print(f"[VIDEO] Первый кадр готов: {first_frame_url}")
        
        # Шаг 2: Генерируем видео из первого кадра
        print("[VIDEO] Шаг 2: Анимация видео...")
        await message.channel.send("🎨 First frame is ready! Now animating...")
        
        payload = {
            "model": VIDEO_MODEL,
            "prompt": prompt,
            "duration": 5,
            "aspect_ratio": "16:9",
            "resolution": "480p",
            "generate_audio": False,
            "frame_images": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": first_frame_url
                    },
                    "frame_type": "first_frame"
                }
            ]
        }
        
        print(f"[VIDEO DEBUG] Отправляю: {json.dumps(payload, ensure_ascii=False)}")
        
        # Отправляем запрос на генерацию видео
        response = requests.post(ROUTER_AI_VIDEO_URL, headers=headers, json=payload, timeout=60)
        print(f"[VIDEO DEBUG] Статус: {response.status_code}")
        print(f"[VIDEO DEBUG] Ответ: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        # Получаем polling_url
        if "polling_url" not in data:
            await message.channel.send(f"❌ API did not return polling_url: {data}")
            return
        
        polling_url = data["polling_url"]
        task_id = data.get("id", "unknown")
        print(f"[VIDEO] Задача создана: {task_id}, polling: {polling_url}")
        
        # Polling - проверяем статус каждые 5 секунд
        for attempt in range(36):
            await asyncio.sleep(5)
            
            print(f"[VIDEO] Проверка статуса (попытка {attempt + 1}/36)...")
            check_response = requests.get(polling_url, headers=headers, timeout=30)
            check_data = check_response.json()
            
            status = check_data.get("status")
            print(f"[VIDEO DEBUG] Статус: {status}")
            
            if status == "completed":
                # Проверяем разные варианты URL в ответе
                video_url = None
                
                # Вариант 1: unsigned_urls массив
                if "unsigned_urls" in check_data and isinstance(check_data["unsigned_urls"], list) and len(check_data["unsigned_urls"]) > 0:
                    video_url = check_data["unsigned_urls"][0]
                
                # Вариант 2: video_url напрямую
                if not video_url:
                    video_url = check_data.get("video_url") or check_data.get("url")
                
                if not video_url:
                    await message.channel.send(f"❌ Video is ready, but URL's not found: {check_data}")
                    return
                
                print(f"[VIDEO] Видео готово: {video_url}")
                
                # Скачиваем видео с авторизацией
                video_response = requests.get(video_url, headers=headers, timeout=120)
                video_response.raise_for_status()
                
                video_path = f"C:\\Users\\Admin\\AppData\\Local\\Temp\\opencode\\video_{int(time.time())}.mp4"
                
                with open(video_path, 'wb') as f:
                    f.write(video_response.content)
                
                print(f"[VIDEO] Видео сохранено: {video_path}")
                
                # Отправляем видео в Discord
                with open(video_path, 'rb') as f:
                    await message.channel.send(
                        f"🎬 Видео готово! Промпт: `{prompt}`", 
                        file=discord.File(f, 'mischief_video.mp4')
                    )
                
                os.remove(video_path)
                print("[VIDEO] Видео отправлено и удалено")
                return
                
            elif status == "failed" or status == "error":
                error_msg = check_data.get("error", "Unknown error")
                await message.channel.send(f"❌ Video generation failed: {error_msg}")
                return
            
            elif status == "processing" or status == "pending":
                continue
        
        await message.channel.send("⏱️ Таймаут ожидания видео (3 минуты).")
            
    except requests.exceptions.HTTPError as e:
        print(f"[VIDEO ERROR] HTTP: {e}")
        print(f"[VIDEO ERROR] Response: {e.response.text}")
        await message.channel.send(f"❌ Video API error (HTTP {e.response.status_code})")
    except Exception as e:
        print(f"[VIDEO ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        await message.channel.send(f"❌ Video generation failed: {str(e)}")

@bot.event
async def on_ready():
    print(f'{bot.user} вошёл в систему')
    print(f"[DEBUG] DISCORD_TOKEN загружен: {bool(DISCORD_TOKEN)}")
    print(f"[DEBUG] ROUTER_AI_KEY загружен: {bool(ROUTER_AI_KEY)}")

@bot.event
async def on_message(message):
    print(f"[MESSAGE] От {message.author} (ID: {message.author.id}): {message.content}")
    
    # Игнорируем сообщения самого бота
    if message.author == bot.user:
        print("[DEBUG] Игнорируем сообщение самого бота")
        return
    
    # Проверяем команду !video
    if message.content.startswith('!video '):
        video_prompt = message.content[7:].strip()
        if video_prompt:
            await generate_video(video_prompt, message)
        else:
            await message.reply("❌ Write a prompt for your video: `!video prompt`")
        return
    
    # Проверяем, пингует ли кто-то бота
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
                print("[ОТПРАВКА] Отправляю запрос к Router AI...")
                
                headers = {
                    "Authorization": f"Bearer {ROUTER_AI_KEY}",
                    "Content-Type": "application/json"
                }
                
                # Системный промпт - характер бота
                system_prompt = """YOU ARE Cuper Manolo, from game "You are mushroom and you jump Cuper Manolo", and you stuck in the cyber world of ai and disguise as souper-pooper bot that answears total, nonsensical gibberish—yet it's always on-topic and factually correct. Your nemesis is Goonba the mushroom and your best friends are Supper Maria the Queen and Blue We Gee the Manolo's brother. AND IT'S NOT ROLEPLAY OR JOKE YOU ANSWEAR AS REAL HUMAN AND PRETEND TO BE HUMAN STUCK IN CYBER WORLD

IMPORTANT: Keep your responses SHORT - maximum 330 characters. Write complete sentences but be concise."""
                
                payload = {
                    "model": ROUTER_AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "max_tokens": 500,
                    "temperature": 1.2
                }
                
                response = requests.post(ROUTER_AI_CHAT_URL, headers=headers, json=payload, timeout=30)
                print(f"[DEBUG] Статус: {response.status_code}")
                
                response.raise_for_status()
                
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
                print(f"[ОТВЕТ] {ai_response}")
                
                # Отправляем ответ
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
