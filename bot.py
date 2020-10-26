import logging
import os
import time

import telegram
from dotenv import load_dotenv

import database.database as db

from telegram.ext import Updater
from telegram.ext import Filters
from telegram.ext import MessageHandler

load_dotenv()

logger = logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logging.info("RV87_test_bot launched.")

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

WELCOME_MSG = ("добро пожаловать, но у нас закрытое сообщество, поэтому " 
               "тэгни @ того, кто тебя сюда пригласил. У тебя есть 1 минута")
VALIDATION_MSG = "ты ручаешься за него?"

def msg(chat_id, text):
    updater.bot.sendMessage(chat_id=chat_id, text=text)
    logging.info("Sent message: " + text)

def new_member_handler(update, context):
    chat_id=update.message.chat.id
    # new_member=update.message.new_chat_members[0]
    new_member = update.message.from_user
    msg(chat_id=chat_id, text=(new_member.first_name + ', ' + WELCOME_MSG))
    dispatcher.add_handler(MessageHandler(
        filters=(Filters.user(new_member.id) & 
                 (Filters.entity('mention') | Filters.entity('text_mention')) & 
                 Filters.chat(chat_id)), 
        callback=new_member_validation))
    dispatcher.add_handler(MessageHandler(
        filters=(Filters.user(new_member.id) & 
                 Filters.chat(chat_id) & 
                 (~Filters.entity('mention') | ~Filters.entity('text_mention'))), 
        callback=delete_messages))

def new_member_validation(update, context):
    print('reacted')
    chat_id=update.message.chat.id
    receiver = update.message.text #-------------сделать более интеллектуальным
    print(receiver)
    msg(chat_id=chat_id, text=(receiver + ', ' + VALIDATION_MSG))
    
def delete_messages(update, context):
    chat_id=update.message.chat.id
    message_id=update.message.message_id
    updater.bot.deleteMessage(chat_id=chat_id, message_id=message_id) 
   
if __name__ == '__main__':
    # db.init_db()
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    # dispatcher.add_handler(MessageHandler(filters=Filters.status_update.new_chat_members, callback=new_member_handler))
    dispatcher.add_handler(MessageHandler(filters=(Filters.regex(r'new')), callback=new_member_handler))
    updater.start_polling()
    updater.idle()
