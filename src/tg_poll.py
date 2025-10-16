import os, telebot
BOT_TOKEN = os.environ["TG_TOKEN"]
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

try:
    bot.delete_webhook(drop_pending_updates=True)
except Exception:
    pass

@bot.message_handler(commands=['ping'])
def ping(m): bot.reply_to(m, "pong")

bot.infinity_polling(timeout=60, long_polling_timeout=50, skip_pending=True)
