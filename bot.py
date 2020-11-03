import logging
import os
import time
from datetime import datetime

# from djantimat.helpers import RegexpProc
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Filters, MessageHandler, CommandHandler, Updater

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
VALIDATION_NEGATIVE_MSG = ('Увы, этот участник не мог тебя пригласить, '
                           'выбери другого (у тебя одна минута)')
VALIDATION_POSITIVE_MSG = ('куча приветственных слов, напиши #осебе '
                           'и что-нибудь о себе - '
                           'без этого ты не сможешь общаться в чате')
CANT_INVITE_MSG = 'у тебя закончились инвайты, ты не можешь приглашать'

validation_keyboard = ReplyKeyboardMarkup([['Да', 'Нет']],
                                          resize_keyboard=True,
                                          one_time_keyboard=True,
                                          selective=True)
remove_keyboard = ReplyKeyboardRemove()

CANDIDATE_DUE = 60
INVITER_DUE = 120


def msg(chat_id, text, **kwargs):
    """Sends a message with possible additions such as a keyboard."""
    updater.bot.sendMessage(chat_id=chat_id, text=text, **kwargs)
    logging.info('Sent message: ' + text)


def new_member_start(update, context, tries=3):
    print('new_member_start')
    print(update.message.new_chat_members)
    """Any newcomer is handled by this function first"""
    handlers_remover(dispatcher, group=2)                                                                   # to prevent deleted messages from getting to DB
    chat_id = update.message.chat.id
    chat = db.get_or_create(db.Chat, chat_id=chat_id)                                                       #adds the chat to the database or gets it from it
    inviter = update.message.from_user
    for new_member in update.message.new_chat_members:
        if chat.ban_mode == 1:
            return negative_validation(update, context, additional_context = (chat_id, None, new_member))

        if inviter.id != new_member.id:                                                                              #checks if a person was added not by link
            inviter = db.get(db.User, tg_id=inviter.id)
            if inviter.invites > 0:
                additional_context = (chat_id, inviter, new_member)
                return positive_validation(update, context, additional_context)
            until_date = int(time.time())+31                                                                         #31 seconds is a minimum ban period
            updater.bot.kick_chat_member(chat_id=chat_id, user_id=new_member.id, until_date=until_date)
            msg(chat_id=chat_id, text=(f'{inviter.first_name}, {CANT_INVITE_MSG}'))

        else:                                                                                                       #joined the group via invite link scenario
            if tries > 0:                                                                                           #checks how many tries left 
                handlers_remover(dispatcher, group=0)                                                               #removes any redundant handlers                                                            #
                msg(chat_id=chat_id, text=(new_member.first_name + ', ' + WELCOME_MSG))
                set_timer(update, context, due=CANDIDATE_DUE, target=new_member)                                    #activates the timer that bans the target if the due is reached
                dispatcher.add_handler(MessageHandler(
                    filters=(Filters.user(new_member.id) &
                            (Filters.entity('mention') | Filters.entity('text_mention')) &
                            Filters.chat(chat_id)),
                    callback=lambda update, context: new_member_validation(update, context, tries)))

                dispatcher.add_handler(MessageHandler(
                    filters=(Filters.user(new_member.id) &
                            Filters.chat(chat_id) &
                            (~Filters.entity('mention') | ~Filters.entity('text_mention'))),
                    callback=lambda update, context: delete_messages(update, context=(chat_id, new_member))))
            else:
                print(f'chat_id:{chat_id} ---- new_member{new_member}')
                return negative_validation(update, context, additional_context = (chat_id, None, new_member))


def new_member_validation(update, context, tries):
    print('new_member_validation')
    unset_timer(update, context)
    chat_id = update.message.chat.id
    candidate = update.message.from_user
    inviter_username = (update.message.text).strip('@')
    try:
        inviter = (db.get(db.User, username=inviter_username) or
                   db.get(db.User, tg_id=update.message.entities[0].user.id))
    except AttributeError:
        inviter = None
    if inviter and inviter.invites > 0:
        set_timer(update, context, due=INVITER_DUE, target=candidate)
        if inviter.username != 'NULL':
            msg(chat_id=chat_id, text=('@' + inviter.username + ', ' + VALIDATION_MSG + f' ({candidate.first_name}/{candidate.username or "без username"})?'), reply_markup=validation_keyboard)
        else:
            text = f'[{inviter.first_name}](tg://user?id={inviter.tg_id}), {VALIDATION_MSG} \({candidate.first_name}/{candidate.username or "без username"}\)?'
            msg(chat_id=chat_id, text=text, reply_markup=validation_keyboard, parse_mode='MarkdownV2')
        positive_validation_handler = MessageHandler(filters=(Filters.regex('Да') & Filters.chat(chat_id) & Filters.user(inviter.tg_id)), callback=lambda update, context: positive_validation(update, context, additional_context = (chat_id, inviter, candidate)))
        negative_validation_handler = MessageHandler(filters=(Filters.regex('Нет') & Filters.chat(chat_id) & Filters.user(inviter.tg_id)), callback=lambda update, context: negative_validation(update, context, additional_context = (chat_id, inviter, candidate)))
        dispatcher.add_handler(positive_validation_handler, group=1)
        dispatcher.add_handler(negative_validation_handler, group=1)
    else:
        msg(chat_id=chat_id, text=VALIDATION_NEGATIVE_MSG)
        tries -= 1
        update.message.new_chat_members = [candidate]
        return new_member_start(update, context, tries)


def positive_validation(update, context, additional_context):
    print('positive_validation')
    chat_id, inviter, candidate = additional_context
    try:
        unset_timer(update, context)
        handlers_remover(dispatcher, group=0)
        handlers_remover(dispatcher, group=1)
        logging.info(f'{candidate.username or candidate.first_name} was invited by link')
    except:
        logging.info(f'{candidate.username or candidate.first_name} was invited directly')
    text = f'{candidate.first_name}, {VALIDATION_POSITIVE_MSG}'
    msg(chat_id=chat_id, text=text, reply_markup=remove_keyboard)

    dispatcher.add_handler(MessageHandler(
        filters=(Filters.user(candidate.id) &
                 Filters.regex(r'#осебе') &
                 Filters.chat(chat_id)),
        callback=lambda update, context: add_new_member(update, context=(chat_id, candidate, inviter))))

    dispatcher.add_handler(MessageHandler(
        filters=(Filters.user(candidate.id) &
                 Filters.chat(chat_id) &
                 (~Filters.regex('#осебе'))),
        callback=lambda update, context: delete_messages(update, context=(chat_id, candidate))))


def add_new_member(update, context):
    print('add_new_member')
    chat_id, candidate, inviter = context
    handlers_remover(dispatcher, group=0)
    db.update_invites(inviter.tg_id, -1)
    new_user = {'tg_id': candidate.id,
                'username': candidate.username or 'NULL',
                'first_name': candidate.first_name,
                'last_name': candidate.last_name or 'NULL',
                'about': update.message.text,
                'joined_date': datetime.utcnow(),
                'inviter_tg_id': inviter.tg_id,
                'inviter_username': inviter.username or 'NULL',
                'inviter_first_name': inviter.first_name,
                'enter_chat_id': chat_id}
    db.create(db.User, **new_user)
    logging.info(f'{candidate.username or candidate.first_name} was added to database')
#==========================================================================================================================

def negative_validation(update, context, additional_context):
    print('negativ_validation')
    chat_id, inviter, candidate = additional_context
    unset_timer(update, context)
    handlers_remover(dispatcher, group=1)
    chat = db.get(db.Chat, chat_id=chat_id)
    if chat.ban_mode == 1:
        until_date = int(time.time())+31
    else:
        until_date = int(time.time())+31                                                        #FOR DEBUG ONLY 
    updater.bot.kick_chat_member(chat_id=chat_id, user_id=candidate.id, until_date=until_date)
    print(update.message.new_chat_members)
    update.message.new_chat_members = []
    print(update.message.new_chat_members)
    try:
        logging.info(f'{inviter.username or inviter.first_name or "Chat"} denied \
                    {candidate.username or candidate.first_name}')
    except AttributeError:
        logging.info(f'{candidate.username or candidate.first_name} ran out of tries')


def delete_messages(update, context):
    chat_id, candidate = context
    message_id = update.message.message_id
    updater.bot.deleteMessage(chat_id=chat_id, message_id=message_id)
    logging.info(f'Message from {candidate.username or candidate.first_name} was deleted')


def add_msg_to_db(update, context):
    from_user_id = update.message.from_user.id
    from_user = db.get(db.User, tg_id=from_user_id)
    if not from_user:
        pass
    else:
        chat_id = update.message.chat.id
        chat = db.get(db.Chat, chat_id=chat_id)
        # mat = RegexpProc.test(text)
        mat = 0
        caps = 0
        msg_type = detect_msg_type(update.message)
        new_msg = {'from_id': from_user.tg_id,
                'from_username': from_user.username,
                'from_first_name': from_user.first_name,
                'msg_date': datetime.utcnow(),
                'msg_type': msg_type,
                'text': update.message.text or update.message.caption or 'NULL',
                'chat_id': chat.chat_id,
                'mat': mat,
                'caps': caps}
        db.create(db.Message, **new_msg)


def add_admin(update, context):
    candidate = update.message.from_user
    chat_id = update.message.chat.id
    chat = db.get_or_create(db.Chat, chat_id=chat_id)        
    new_user = {'tg_id': candidate.id,
                'username': candidate.username or 'NULL',
                'first_name': candidate.first_name,
                'last_name': candidate.last_name or 'NULL',
                'about': 'admin',
                'joined_date': datetime.utcnow(),
                'inviter_tg_id': candidate.id,
                'inviter_username': candidate.username or 'NULL',
                'inviter_first_name': candidate.first_name,
                'enter_chat_id': chat_id}
    db.create(db.User, **new_user)
    logging.info(f'{candidate.username or candidate.first_name} was added to database')


if __name__ == '__main__':
    logging.info('RV87_test_bot launched.')
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(filters=Filters.status_update.new_chat_members, callback=new_member_start))
    dispatcher.add_handler(MessageHandler(filters=((~Filters.status_update.new_chat_members) & (~Filters.command)), callback=add_msg_to_db), group=2)
    dispatcher.add_handler(CommandHandler('admin', callback=add_admin))
    # dispatcher.add_handler(MessageHandler(filters=(Filters.regex(r'new')), callback=new_member_start))
    # dispatcher.add_handler(MessageHandler(filters=(~Filters.regex(r'new')), callback=add_msg_to_db))
    updater.start_polling()
    updater.idle()



        # for handler in dispatcher.handlers[1]:
        #     print(handler.filters)


    # print(f'delete context {dir(context)}')
    # print(f'args {context.args}')
    # print(f'async_args {context.async_args}')
    # print(f'async_kwargs {context.async_kwargs}')
    # print(f'bot {context.bot}')
    # print(f'bot_data {context.bot_data}')
    # print(f'chat_data {context.chat_data}')
    # print(f'dispatcher {context.dispatcher}')
    # print(f'error {context.error}')
    # print(f'from_error {context.from_error}')
    # print(f'from_job {context.from_job}')
    # print(f'from_update {context.from_update}')
    # print(f'job {context.job}')
    # print(f'job_queue {context.job_queue}' )
    # print(f'match {context.match}')
    # print(f'matches {context.matches}')
    # print(f'update {context.update}')
    # print(f'update_queue {context.update_queue}')
    # print(f'user_data {context.user_data}')