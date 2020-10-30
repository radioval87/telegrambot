import logging
import os
import time
from datetime import datetime

import telegram
# from djantimat.helpers import RegexpProc
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Filters, MessageHandler, Updater

import database.database as db
from tools.miscellaneous import handlers_remover, detect_msg_type
from tools.timer import set_timer, unset_timer

load_dotenv()

logger = logging.getLogger('main_bot').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

WELCOME_MSG = ('добро пожаловать, но у нас закрытое сообщество, поэтому ' 
               'тэгни @ того, кто тебя сюда пригласил. У тебя есть 1 минута')
VALIDATION_MSG = 'ты ручаешься за'
VALIDATION_NEGATIVE_MSG = 'Увы, этот участник не мог тебя пригласить, выбери другого (у тебя одна минута)'
VALIDATION_POSITIVE_MSG = 'куча приветственных слов, напиши #осебе, без этого ты не сможешь общаться в чате'

validation_keyboard = ReplyKeyboardMarkup([['Да', 'Нет']], 
                                          resize_keyboard=True, 
                                          one_time_keyboard=True, 
                                          selective=True)
remove_keyboard = ReplyKeyboardRemove()

candidate_due = 60
receiver_due = 120


def msg(chat_id, text, **kwargs):
    updater.bot.sendMessage(chat_id=chat_id, text=text, **kwargs)
    logging.info('Sent message: ' + text)


def new_member_start(update, context, tries=3):
    chat_id = update.message.chat.id
    inviter = update.message.from_user
    new_member = update.message.new_chat_members[0]
    
    if inviter.id != new_member.id:
        invites = db.get(db.User, tg_id=inviter.id).invites
        if invites > 0:
            return positive_validation(update, context, candidate=new_member)
        until_date = int(time.time())+31
        updater.bot.kick_chat_member(chat_id=chat_id, user_id=new_member.id, until_date=until_date)
        return msg(chat_id=chat_id, text=(f'{inviter.first_name} у тебя закончились инвайты, ты не можешь приглашать'))

    else:
        chat = db.get_or_create(db.Chat, chat_id=chat_id)
        if tries > 0 and chat.ban_mode == 0:
            handlers_remover(dispatcher, group=0)
            msg(chat_id=chat_id, text=(new_member.first_name + ', ' + WELCOME_MSG))
            set_timer(update, context, due=candidate_due, target=new_member)
            
            dispatcher.add_handler(MessageHandler(
                filters=(Filters.user(new_member.id) & 
                        (Filters.entity('mention') | Filters.entity('text_mention')) & 
                        Filters.chat(chat_id)), 
                callback=lambda update, context: new_member_validation(update, context, tries)))
            
            dispatcher.add_handler(MessageHandler(
                filters=(Filters.user(new_member.id) & 
                        Filters.chat(chat_id) & 
                        (~Filters.entity('mention') | ~Filters.entity('text_mention'))), 
                callback=delete_messages))
        else:
            return negative_validation(update, context, candidate=new_member)


def new_member_validation(update, context, tries):
    unset_timer(update, context)
    chat_id=update.message.chat.id
    candidate = update.message.from_user
    receiver_username = (update.message.text).strip('@')
    receiver = (db.get(db.User, username=receiver_username) or
                db.get(db.User, tg_id=update.message.entities[0].user.id))
    if receiver and receiver.invites > 0:
        if receiver.username:
            set_timer(update, context, due=receiver_due, target=candidate)
            msg(chat_id=chat_id, text=('@' + receiver.username + ', ' + VALIDATION_MSG + f' ({candidate.first_name}/{candidate.username or "без username"})?'), keyboard=validation_keyboard)
        else:
            set_timer(update, context, due=receiver_due, target=candidate)
            text=f'[{receiver.first_name}](tg://user?id={receiver.id}), {VALIDATION_MSG} \({candidate.first_name}/{candidate.username or "без username"}\)?'
            msg(chat_id=chat_id, text=text, reply_markup=validation_keyboard, parse_mode='MarkdownV2')
        positive_validation_handler = MessageHandler(filters=(Filters.regex('Да') & Filters.chat(chat_id) & Filters.user(receiver.id)), callback=lambda update, context: positive_validation(update, context, candidate))
        negative_validation_handler = MessageHandler(filters=(Filters.regex('Нет') & Filters.chat(chat_id) & Filters.user(receiver.id)), callback=lambda update, context: negative_validation(update, context, candidate))
        dispatcher.add_handler(positive_validation_handler, group=1)
        dispatcher.add_handler(negative_validation_handler, group=1)
    else:
        msg(chat_id=chat_id, text=VALIDATION_NEGATIVE_MSG)
        tries -= 1
        return new_member_start(update, context, tries)


def positive_validation(update, context, candidate):
    unset_timer(update, context)
    handlers_remover(dispatcher, group=0)
    handlers_remover(dispatcher, group=1)
    chat_id = update.message.chat.id
    inviter = update.message.from_user
    text=f'{candidate.first_name}, {VALIDATION_POSITIVE_MSG}'
    msg(chat_id=chat_id, text=text, reply_markup=remove_keyboard)
    
    dispatcher.add_handler(MessageHandler(
        filters=(Filters.user(candidate.id) & 
                Filters.regex(r'#осебе') & 
                Filters.chat(chat_id)), 
        callback=lambda update, context: add_new_member(update, context, inviter)))

    dispatcher.add_handler(MessageHandler(
        filters=(Filters.user(candidate.id) & 
                Filters.chat(chat_id) & 
                (~Filters.regex('#осебе'))), 
        callback=delete_messages))
   
    
def negative_validation(update, context, candidate):
    unset_timer(update, context)
    handlers_remover(dispatcher, group=1)
    chat_id = update.message.chat.id
    chat = db.get(db.Chat, chat_id=chat_id)
    inviter = update.message.from_user
    # until_date = int(time.time())+86400
    if chat.ban_mode == 1:
        until_date = int(time.time())+31
    else:
        until_date = int(time.time())+31
    updater.bot.kick_chat_member(chat_id=chat_id, user_id=candidate.id, until_date=until_date)
    logging.info(f'{inviter.username or inviter.first_name or "Chat"} denied \
                 {candidate.username or candidate.first_name}')


def add_new_member(update, context, inviter):
    handlers_remover(dispatcher, group=0)
    inviter.invites -= 1
    candidate = update.message.from_user
    chat = update.message.chat
    new_user = {'tg_id': candidate.id,
                'username': candidate.username or 'NULL',
                'first_name': candidate.first_name,
                'last_name': candidate.last_name or 'NULL',
                'about': update.message.text,
                'joined_date': datetime.utcnow(),
                'inviter_tg_id': inviter.id,
                'inviter_username': inviter.username or 'NULL',
                'inviter_first_name': inviter.first_name,
                'enter_chat_id': chat.id}
    db.create(db.User, **new_user)
    logging.info(f'{candidate.username or candidate.first_name} was added to database')


def delete_messages(update, context):
    chat_id=update.message.chat.id
    message_id=update.message.message_id
    candidate = update.message.from_user
    updater.bot.deleteMessage(chat_id=chat_id, message_id=message_id) 
    logging.info(f'Message from {candidate.username or candidate.first_name} was deleted')


def add_msg_to_db(update, context):
    from_user = update.message.from_user
    chat = update.message.chat
    text = update.message.text
    print(update)
    # mat = RegexpProc.test(text)
    mat = 0
    caps = 0
    msg_type = detect_msg_type(update.message)
    new_msg = {'from_id': from_user.id,
               'from_username': from_user.username,
               'from_first_name': from_user.first_name,
               'msg_date': datetime.utcnow(),
               'msg_type': msg_type,
               'text': update.message.text or update.message.caption or 'NULL',
               'chat_id': chat.id,
               'mat': mat,
               'caps': caps}
    db.create(db.Message, **new_msg)


if __name__ == '__main__':
    logging.info('RV87_test_bot launched.')
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    # dispatcher.add_handler(MessageHandler(filters=Filters.status_update.new_chat_members, callback=new_member_start))
    dispatcher.add_handler(MessageHandler(filters=(Filters.regex(r'new')), callback=new_member_start))
    dispatcher.add_handler(MessageHandler(filters=(~Filters.regex(r'new')), callback=add_msg_to_db))
    # dispatcher.add_handler(CommandHandler(filters=(~Filters.regex(r'new')), callback=add_msg_to_db))
    updater.start_polling()
    updater.idle()

'''
{'message_id': 1500, 
'date': 1604067058, 
'chat': {'id': -1001273799823, 
'type': 'supergroup', 
'title': 'Bot_test'}, 
'entities': [], 
'caption_entities': [], 
'photo': [], 
'new_chat_members': [{'id': 205260481, 'first_name': 'Валя', 'is_bot': False, 'username': 'boredteenager'}], 
'new_chat_photo': [], 
'delete_chat_photo': False, 
'group_chat_created': False, 
'supergroup_chat_created': False, 
'channel_chat_created': False, 
'from': {'id': 70635837, 'first_name': 'Valentin', 'is_bot': False, 'last_name': 'Gun', 'language_code': 'ru'}}

{'message_id': 1502, 
'date': 1604067175, 
'chat': {'id': -1001273799823, 
'type': 'supergroup', 
'title': 'Bot_test'}, 
'entities': [], 
'caption_entities': [], 
'photo': [], 
'new_chat_members': [{'id': 70635837, 'first_name': 'Valentin', 'is_bot': False, 'last_name': 'Gun', 'language_code': 'ru'}], 
'new_chat_photo': [], 
'delete_chat_photo': False, 
'group_chat_created': False, 
'supergroup_chat_created': False, 
'channel_chat_created': False, 
'from': {'id': 70635837, 'first_name': 'Valentin', 'is_bot': False, 'last_name': 'Gun', 'language_code': 'ru'}}
'''