import telegram
import os
from .celery import app

bot = telegram.bot.Bot(token=os.environ["TELEGRAM_API_KEY"])
chat_id = os.environ["TELEGRAM_ALLOWED_CHATS_ID"]


@app.task(rate_limit='10/m')
def send_message_with_post(text: str, attachments: list):
    for attach in attachments:
        t = attach["type"]
        if t == "photo":
            bot.send_photo(chat_id, attach["url"], text,parse_mode="html")
        elif t == "doc":
            bot.send_document(chat_id, attach["url"], text,parse_mode="html")
    else:
        bot.send_message(chat_id, text, parse_mode="html")
