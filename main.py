import telebot
import requests
import tempfile
import os
import json
from datetime import datetime

BOT_TOKEN = "8152798171:AAGRupVOrBcDmdT-KbKtfrsevWdsd2GaDyQ"
API_AUTH = "Basic RFJFUE9SVF9ISVNMMjpWbnB0Izc4OSE"
HISTORY_FILE = "history.json"

bot = telebot.TeleBot(BOT_TOKEN)

def save_history(user, bucket, file_name):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    record = {
        "user": user,
        "bucket": bucket,
        "file_name": file_name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    history.insert(0, record)
    history = history[:100]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_user_history(user):
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        return [h for h in history if h["user"] == user]
    except Exception:
        return []


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "👋 Bot sẵn sàng!\n"
        "📥 /getEMR <bucketName> <fileName> — tải file từ hệ thống\n"
        "📜 /listEMR — xem 10 file gần nhất bạn đã tải"
    )


@bot.message_handler(commands=['getEMR'])
def get_emr(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❗Cú pháp đúng: /getEMR <bucketName> <fileName>")
            return

        bucket_name = args[1]
        file_name = args[2]

        url = "https://onehealth2.vncare.vn/api/dreport/drpapi/basicauth/miniodata"
        headers = {
            "Accept": "application/xml",
            "Content-Type": "application/json",
            "Authorization": API_AUTH
        }

        res = requests.post(url, headers=headers, json={
            "bucketName": bucket_name,
            "fileName": file_name
        })

        if res.status_code == 200:
            tmp_path = os.path.join(tempfile.gettempdir(), os.path.basename(file_name))
            with open(tmp_path, "wb") as f:
                f.write(res.content)

            with open(tmp_path, "rb") as f:
                bot.send_document(message.chat.id, f)

            os.remove(tmp_path)
            save_history(message.from_user.username or message.from_user.id, bucket_name, file_name)

        # Không cần báo lỗi chi tiết cho người dùng
    except Exception as e:
        print(f"Lỗi xử lý: {e}")


@bot.message_handler(commands=['listEMR'])
def list_emr(message):
    user = message.from_user.username or message.from_user.id
    history = get_user_history(user)
    if not history:
        bot.reply_to(message, "📭 Chưa có lịch sử tải nào.")
        return

    msg = "📜 *10 file gần nhất bạn đã tải:*\n\n"
    for h in history[:10]:
        msg += f"📁 `{h['file_name']}` — {h['bucket']}\n🕒 {h['time']}\n\n"

    bot.send_message(message.chat.id, msg, parse_mode="Markdown")


print("🤖 Bot đang chạy...")
bot.infinity_polling()
