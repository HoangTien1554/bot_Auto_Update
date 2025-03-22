import json
import asyncio
import requests
from dataclasses import dataclass
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Bot
import time

# Flask app để giữ kết nối mở
app = Flask(__name__)

@app.route('/')
def home():
    return "Server is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Chạy Flask trên một luồng riêng
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()

# Cấu hình bot Telegram
BOT_TOKEN = "8081288489:AAFnPeJPX2Sww3VlZwOnrZW8GfCcVzVJoGA"
CHAT_ID = "-1002671656846"
URL = "https://games.cagboot.com/directory.php?id=16"
OLD_GAMES_FILE = "old_games.json"

@dataclass
class Game:
    column_2: str  # Tên game
    column_3: str  # Kích thước
    column_4: str  # Ngày cập nhật
    column_5: str  # Trạng thái

# Hàm lấy danh sách game mới từ trang web
def get_game_list():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    rows = soup.find_all('tr')

    game_list = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            game = Game(
                column_2=cells[1].get_text(strip=True),
                column_3=cells[2].get_text(strip=True),
                column_4=cells[3].get_text(strip=True),
                column_5=cells[4].get_text(strip=True),
            )
            game_list.append(game)
    return game_list

# Lưu danh sách game vào file JSON
def save_old_games(games):
    with open(OLD_GAMES_FILE, "w", encoding="utf-8") as f:
        json.dump([game.__dict__ for game in games], f, ensure_ascii=False, indent=4)

# Đọc danh sách game cũ từ file
def load_old_games():
    try:
        with open(OLD_GAMES_FILE, "r", encoding="utf-8") as f:
            return [Game(**game) for game in json.load(f)]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Gửi tin nhắn đến Telegram
async def send_message(text):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text)

# Kiểm tra và thông báo game mới
async def check_new_games():
    old_games = load_old_games()
    new_games = get_game_list()

    new_entries = [game for game in new_games if game.column_4 not in [g.column_4 for g in old_games]]

    if new_entries:
        for game in new_entries:
            message = f"📢 Game mới cập nhật:\n🎮 Game: {game.column_2}\n📦 Kích thước: {game.column_3}\n📅 Ngày: {game.column_4}\n🔄 Trạng thái: {game.column_5}"
            await send_message(message)
            await asyncio.sleep(2)

        save_old_games(new_games)

# Chạy kiểm tra tự động
async def start_auto_checking():
    while True:
        await check_new_games()
        await asyncio.sleep(30)

# Khởi chạy chương trình
if __name__ == "__main__":
    # Chạy Flask trên một luồng riêng
    Thread(target=run_flask, daemon=True).start()

    # Tạo một event loop mới cho asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Chạy vòng lặp kiểm tra game trên một luồng riêng biệt
    Thread(target=lambda: loop.run_until_complete(start_auto_checking()), daemon=True).start()

    # Giữ chương trình chạy liên tục
    while True:
        time.sleep(1)
