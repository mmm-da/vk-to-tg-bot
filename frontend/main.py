import os
import logging
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = os.environ['TELEGRAM_API_KEY']
ADMIN_USERS = os.environ['TELEGRAM_ALLOWED_CHATS_ID'].split(',')
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):    
    help_str = f'Это админка бота который пересылает посты,\n из выбранных пабликов ВК в каналы Телеграмма.'
    await message.reply(help_str)

@dp.message_handler(user_id=ADMIN_USERS)
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)

    await message.answer(message.text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)