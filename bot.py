import logging
import os
import time
from datetime import datetime

import telegram
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Filters, MessageHandler, Updater

import database.database as db

load_dotenv()

logger = logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logging.info('RV87_test_bot launched.')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

WELCOME_MSG = ('добро пожаловать, но у нас закрытое сообщество, поэтому ' 
               'тэгни @ того, кто тебя сюда пригласил. У тебя есть 1 минута')
VALIDATION_MSG = 'ты ручаешься за'
VALIDATION_NEGATIVE_MSG = 'Увы, этот участник не мог тебя пригласить, выбери другого (у тебя одна минута)'
VALIDATION_POSITIVE_MSG = 'куча приветственных слов, напиши #осебе, без этого ты не сможешь общаться в чате'

validation_keyboard = ReplyKeyboardMarkup([['Да', 'Нет']], resize_keyboard=True, one_time_keyboard=True, selective=True)
remove_keyboard = ReplyKeyboardRemove()


def msg(chat_id, text, **kwargs):
    updater.bot.sendMessage(chat_id=chat_id, text=text, **kwargs)
    logging.info("Sent message: " + text)


def new_member_start(update, context):
    dispatcher.remove_handler(handler=dispatcher.handlers[0][0], group=0)
    chat_id=update.message.chat.id
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
    chat_id=update.message.chat.id
    sender = update.message.from_user
    receiver_username = (update.message.text).strip('@')
    receiver = db.get(db.User, username=receiver_username) or update.message.entities[0].user
    if receiver:
        if receiver.username:
            msg(chat_id=chat_id, text=('@' + receiver.username + ', ' + VALIDATION_MSG + f' ({sender.first_name}/{sender.username or "без username"})?'), keyboard=validation_keyboard)
        else:
            text=f'[{receiver.first_name}](tg://user?id={receiver.id}), {VALIDATION_MSG} \({sender.first_name}/{sender.username or "без username"}\)?'
            msg(chat_id=chat_id, text=text, reply_markup=validation_keyboard, parse_mode='MarkdownV2')
        positive_validation_handler = MessageHandler(filters=(Filters.regex('Да') & Filters.chat(chat_id) & Filters.user(receiver.id)), callback=lambda update, context: positive_validation(update, context, sender))
        negative_validation_handler = MessageHandler(filters=(Filters.regex('Нет') & Filters.chat(chat_id) & Filters.user(receiver.id)), callback=lambda update, context: negative_validation(update, context, sender))
        dispatcher.add_handler(positive_validation_handler, group=1)
        dispatcher.add_handler(negative_validation_handler, group=1)
    else:
        msg(chat_id=chat_id, text=VALIDATION_NEGATIVE_MSG)


def positive_validation(update, context, sender):
    dispatcher.remove_handler(handler=dispatcher.handlers[1][0], group=1)
    chat_id = update.message.chat.id
    inviter = update.message.from_user
    text=f'{sender.first_name}, {VALIDATION_POSITIVE_MSG}'
    msg(chat_id=chat_id, text=text, reply_markup=remove_keyboard)
    dispatcher.remove_handler(handler=dispatcher.handlers[0][1], group=0)
    dispatcher.remove_handler(handler=dispatcher.handlers[0][0], group=0)
    dispatcher.add_handler(MessageHandler(
        filters=(Filters.user(sender.id) & 
                Filters.regex(r'#осебе') & 
                Filters.chat(chat_id)), 
        callback=lambda update, context: add_new_member(update, context, inviter)))

    dispatcher.add_handler(MessageHandler(
        filters=(Filters.user(sender.id) & 
                Filters.chat(chat_id) & 
                (~Filters.regex('#осебе'))), 
        callback=delete_messages))
   
    
def negative_validation(update, context, sender):
    dispatcher.remove_handler(handler=dispatcher.handlers[1][0], group=1)
    chat_id = update.message.chat.id
    until_date = time.time()+86400
    updater.bot.kick_chat_member(chat_id=chat_id, user_id=sender.id, until_date=until_date)


def add_new_member(update, context, inviter):
    dispatcher.remove_handler(handler=dispatcher.handlers[0][1], group=0)
    dispatcher.remove_handler(handler=dispatcher.handlers[0][0], group=0)
    sender = update.message.from_user
    chat = update.message.chat
    new_user = {'tg_id': sender.id,
    'username': sender.username or 'NULL',
    'first_name': sender.first_name,
    'last_name': sender.last_name or 'NULL',
    'about': update.message.text,
    'joined_date': datetime.utcnow(),
    'inviter_tg_id': inviter.id,
    'inviter_username': inviter.username or 'NULL',
    'inviter_first_name': inviter.first_name,
    'enter_chat_id': chat.id}
    print(dispatcher.handlers)
    db.create(db.User, **new_user)


def delete_messages(update, context):
    chat_id=update.message.chat.id
    message_id=update.message.message_id
    updater.bot.deleteMessage(chat_id=chat_id, message_id=message_id) 


if __name__ == '__main__':
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(filters=(Filters.regex(r'new')), callback=new_member_start))
    updater.start_polling()
    updater.idle()
