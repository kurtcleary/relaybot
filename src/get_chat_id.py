import os, telebot
b = telebot.TeleBot(os.environ["TG_TOKEN"])
@b.message_handler(commands=['id'])
def _(m): b.reply_to(m, f"chat_id={m.chat.id}")
b.delete_webhook(drop_pending_updates=True)
b.infinity_polling()
