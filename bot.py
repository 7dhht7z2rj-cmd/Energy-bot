import os
import logging
import asyncio
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Отримуємо токен зі змінних середовища Render
API_TOKEN = os.getenv('BOT_TOKEN')

# URL сторінки для моніторингу
TARGET_URL = "https://energy-ua.info/grafik/%D0%9F%D0%BE%D0%BB%D1%82%D0%B0%D0%B2%D0%B0/%D0%B1%D1%83%D0%BB%D1%8C%D0%B2.+%D0%91.%D0%A5%D0%BC%D0%B5%D0%BB%D1%8C%D0%BD%D0%B8%D1%86%D1%8C%D0%BA%D0%BE%D0%B3%D0%BE/9%D0%B0"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def parse_schedule() -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        queue_title = soup.find('h1') or soup.find('h2')
        queue_text = queue_title.get_text(strip=True) if queue_title else "Графік відключень"
        
        paragraphs = soup.find_all(['p', 'li', 'div'])
        
        schedule_lines = []
        capture = False
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if "Періоди відключень" in text:
                capture = True
                schedule_lines.append(f"<b>{text}</b>\n")
                continue
            
            if capture:
                if "з " in text.lower() or "тривалість" in text.lower():
                    schedule_lines.append(f"• {text}")
                elif len(schedule_lines) > 1 and not text:
                    break

        if schedule_lines:
            result_text = f"<b>{queue_text}</b>\n\n" + "\n".join(schedule_lines)
        else:
            result_text = f"<b>{queue_text}</b>\n\nНе вдалося розпізнати конкретні блоки графіку. Перевірте інформацію на сайті напряму."

        return result_text

    except Exception as e:
        logging.error(f"Помилка при парсингу: {e}")
        return "❌ Помилка при отриманні даних із сайту. Спробуйте пізніше."

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    kb = [
        [types.KeyboardButton(text="⚡ Отримати графік")]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    await message.answer(
        "Привіт! Натисніть кнопку нижче або відправте команду /schedule, щоб отримати актуальний графік відключень.",
        reply_markup=keyboard
    )

@dp.message(Command("schedule"))
@dp.message(lambda message: message.text == "⚡ Отримати графік")
async def send_schedule(message: types.Message):
    await message.answer("🔄 Завантажую дані з сайту...")
    schedule_info = parse_schedule()
    await message.answer(schedule_info, parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
