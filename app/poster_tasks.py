import telegram
import os
from .celery import app

bot = telegram.bot.Bot(token=os.environ["TELEGRAM_API_KEY"])
chat_id = os.environ["TELEGRAM_ALLOWED_CHATS_ID"]


@app.task(rate_limit='10/m')
def send_message_with_post(text: str, attachments: list):
    if attachments:
        media_group = []
        for i,attach in enumerate(attachments):
            media = None
            t = attach["type"]
            if t == "photo":
                media = telegram.InputMediaPhoto(media=attach['url'])
            elif t == "doc":
                media = telegram.InputMediaDocument(media=attach['url'])
            if media:
                if i==0:    
                    media.caption=text
                    media.parse_mode='html'
                media_group.append(media)
        bot.send_media_group(chat_id,media_group)
    else:
        bot.send_message(chat_id, text, parse_mode="html")
