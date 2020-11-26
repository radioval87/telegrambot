import logging
import time
from datetime import datetime

# from djantimat.helpers import RegexpProc
from dotenv import load_dotenv
from telegram import ChatPermissions, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, Filters, MessageHandler

import database.database as db
from bobobot import dispatcher, updater
from tools.bot_messages import (WELCOME_MSG, VALIDATION_MSG,
                                VALIDATION_NEGATIVE_MSG,
                                VALIDATION_POSITIVE_MSG,
                                CANT_INVITE_MSG)
from tools.miscellaneous import detect_msg_type, handlers_remover, msg
from tools.timer import set_timer, unset_timer

load_dotenv()

logger = logging.getLogger('main_bot').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

validation_keyboard = ReplyKeyboardMarkup([['Да', 'Нет']],
                                          resize_keyboard=True,
                                          one_time_keyboard=True,
                                          selective=True)
remove_keyboard = ReplyKeyboardRemove()

CANDIDATE_DUE = 5
INVITER_DUE = 600


# dispatcher.add_handler(MessageHandler(filters=Filters.status_update.new_chat_members, callback=new_member_start))

def main_handlers():
    dispatcher.add_handler(MessageHandler(filters=(Filters.regex(r'nnn')), callback=new_member_start), group=4)
    dispatcher.add_handler(MessageHandler(filters=(~Filters.regex(r'nnn')), callback=add_msg_to_db), group=4)
    dispatcher.add_handler(MessageHandler(filters=Filters.status_update.left_chat_member, callback=leave))
    dispatcher.add_handler(CommandHandler('admin', callback=add_admin))


def new_member_start(update, context):
    """Any newcomer is handled by this function first"""
    print('new_member_start')
    new_member = update.message.from_user
    chat_id = update.message.chat.id
    #adds the chat to the database or gets it from it
    chat = db.get_or_create(db.Chat, chat_id=chat_id)
    inviter = update.message.from_user
    # for new_member in update.message.new_chat_members:
    if chat.ban_mode == 1:
        return negative_validation(update, context, additional_context=(chat_id, None, new_member))

    if inviter.id != new_member.id:
        return manual_invite_validation(update, context, chat_id, inviter, new_member)

    return link_invite_validation(update, context, chat_id, new_member)

def manual_invite_validation(update, context, chat_id, inviter, new_member):
    inviter = db.get(db.User, tg_id=inviter.id)
    if inviter.invites > 0:
        additional_context = (chat_id, inviter, new_member)
        return positive_validation(update, context, additional_context)
    #31 seconds is a minimum ban period
    until_date = int(time.time())+31
    msg(chat_id=chat_id, text=(f'{inviter.first_name}, {CANT_INVITE_MSG}'))
    return updater.bot.kick_chat_member(chat_id=chat_id,
                                        user_id=new_member.id,
                                        until_date=until_date)

def link_invite_validation(update, context, chat_id, new_member, tries=3):
    '''Joined the group via invite link scenario.'''
    print('link_invite_validation')
    # print(update.message)
    if tries > 0:
        msg(chat_id=chat_id, text=(f'{new_member.first_name}, {WELCOME_MSG}'))
        #activates the timer that bans the target if the due is reached
        set_timer(update, context, due=CANDIDATE_DUE, target=new_member)

        mention_handler = MessageHandler(
            filters=(Filters.user(new_member.id) &
                    Filters.chat(chat_id) &
                    (Filters.entity('mention') | Filters.entity('text_mention'))),
            callback=lambda update, context: new_member_validation(update,
                                                                   context,
                                                                   tries))
        mention_handler.__name__ = 'mention_handler' + str(new_member.id)

        not_mention_handler = MessageHandler(
            filters=(Filters.user(new_member.id) &
                    Filters.chat(chat_id) &
                    (~Filters.entity('mention') | ~Filters.entity('text_mention'))),
            callback=lambda update, context: delete_message(update,
                                                            context=(chat_id,
                                                                     new_member)))
        not_mention_handler.__name__ = 'not_mention_handler' + str(new_member.id)

        dispatcher.add_handler(mention_handler, group=3)
        dispatcher.add_handler(not_mention_handler, group=3)

    else:
        return negative_validation(update,context,
                                   additional_context = (chat_id, None,
                                                         new_member))


def new_member_validation(update, context, tries):
    print('new_member_validation')
    unset_timer(update, context)
    chat_id = update.message.chat.id
    candidate = update.message.from_user

    handlers_remover(dispatcher, 'mention_handler', user_id=candidate.id, group=3)
    handlers_remover(dispatcher, 'not_mention_handler', user_id=candidate.id, group=3)

    context.bot.restrict_chat_member(chat_id=chat_id, user_id=candidate.id,
        permissions=ChatPermissions(can_send_messages=False,
                                    can_send_media_messages=False,
                                    can_send_other_messages=False,
                                    can_add_web_page_previews=False,
                                    ))
    inviter_username = (update.message.text).strip('@')
    try:
        inviter = (db.get(db.User, username=inviter_username) or
                   db.get(db.User, tg_id=update.message.entities[0].user.id))
    except AttributeError:
        inviter = None
    if inviter and inviter.invites > 0:
        set_timer(update, context, due=INVITER_DUE, target=candidate, inviter=inviter)
        if inviter.username != 'NULL':
            msg(chat_id=chat_id, text=('@' + inviter.username + ', ' + VALIDATION_MSG + f' ({candidate.first_name}/{candidate.username or "без username"})?'), reply_markup=validation_keyboard)
        else:
            text = f'[{inviter.first_name}](tg://user?id={inviter.tg_id}), {VALIDATION_MSG} \({candidate.first_name}/{candidate.username or "без username"}\)?'
            msg(chat_id=chat_id, text=text, reply_markup=validation_keyboard, parse_mode='MarkdownV2')
        
        yes_handler = MessageHandler(filters=(Filters.regex('Да') &
                                             Filters.chat(chat_id) &
                                             Filters.user(inviter.tg_id)),
                                     callback=lambda update, context: positive_validation(update, context, additional_context = (chat_id, inviter, candidate)))
        yes_handler.__name__ = 'yes_handler' + str(inviter.tg_id)

        no_handler = MessageHandler(filters=(Filters.regex('Нет') &
                                            Filters.chat(chat_id) &
                                            Filters.user(inviter.tg_id)),
                                    callback=lambda update, context: negative_validation(update, context, additional_context = (chat_id, inviter, candidate)))
        no_handler.__name__ = 'no_handler' + str(inviter.tg_id)

        dispatcher.add_handler(yes_handler, group=2)
        dispatcher.add_handler(no_handler, group=2)
    else:
        msg(chat_id=chat_id, text=VALIDATION_NEGATIVE_MSG)
        tries -= 1
        return link_invite_validation(update, context, chat_id, candidate, tries)


def positive_validation(update, context, additional_context):
    print('positive_validation')
    chat_id, inviter, candidate = additional_context
    try:
        unset_timer(update, context)
        handlers_remover(dispatcher, 'yes_handler', user_id=inviter.tg_id, group=2)
        handlers_remover(dispatcher, 'no_handler', user_id=inviter.tg_id, group=2)
        context.bot.restrict_chat_member(chat_id=chat_id, user_id=candidate.id,
            permissions=ChatPermissions(can_send_messages=True))
        logging.info(f'{candidate.username or candidate.first_name} was invited by link')
    except AttributeError:
        logging.info(f'{candidate.username or candidate.first_name} was invited directly')
    text = f'{candidate.first_name}, {VALIDATION_POSITIVE_MSG}'
    msg(chat_id=chat_id, text=text, reply_markup=remove_keyboard)

    about_handler = MessageHandler(
        filters=(Filters.user(candidate.id) &
                 Filters.regex(r'#осебе') &
                 Filters.chat(chat_id)),
        callback=lambda update, context: add_new_member(update, context=(chat_id, candidate, inviter)))
    about_handler.__name__ = 'about_handler' + str(candidate.id)

    not_about_handler = MessageHandler(
        filters=(Filters.user(candidate.id) &
                 Filters.chat(chat_id) &
                 (~Filters.regex('#осебе'))),
        callback=lambda update, context: delete_message(update, context=(chat_id, candidate)))
    not_about_handler.__name__ = 'not_about_handler' + str(candidate.id)

    dispatcher.add_handler(about_handler, group=1)
    dispatcher.add_handler(not_about_handler, group=1)


def add_new_member(update, context):
    print('add_new_member')
    chat_id, candidate, inviter = context
    handlers_remover(dispatcher, 'about_handler', user_id=candidate.id, group=1)
    handlers_remover(dispatcher, 'not_about_handler', user_id=candidate.id, group=1)
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
    context.bot.restrict_chat_member(chat_id=chat_id, user_id=candidate.id,
        permissions=ChatPermissions(can_send_messages=True,
                                    can_send_media_messages=True,
                                    can_send_other_messages=True,
                                    can_add_web_page_previews=True,
                                    can_send_polls=True,
                                    can_invite_users=True,
                                    can_pin_messages=True))
    logging.info(f'{candidate.username or candidate.first_name} was added to database')


def negative_validation(update, context, additional_context):
    print('negativ_validation')
    chat_id, inviter, candidate = additional_context
    unset_timer(update, context)
    try:
        unset_timer(update, context)
        handlers_remover(dispatcher, 'yes_handler', user_id=inviter.tg_id, group=2)
        handlers_remover(dispatcher, 'no_handler', user_id=inviter.tg_id, group=2)
    except AttributeError:
        pass
    chat = db.get(db.Chat, chat_id=chat_id)
    if chat.ban_mode == 1:
        until_date = int(time.time())+31
    else:
        until_date = int(time.time())+31        #FOR DEBUG ONLY
    context.bot.restrict_chat_member(chat_id=chat_id, user_id=candidate.id,
        permissions=ChatPermissions(can_send_messages=True,
                                    can_send_media_messages=True,
                                    can_send_other_messages=True,
                                    can_add_web_page_previews=True))
    
    updater.bot.kick_chat_member(chat_id=chat_id, user_id=candidate.id, until_date=until_date)
    print(update)
    try:
        if inviter.username != 'NULL':
            logging.info(f'{inviter.username} denied {candidate.username or candidate.first_name}')
        logging.info(f'{inviter.first_name or "Chat"} denied {candidate.username or candidate.first_name}')
    except AttributeError:
        logging.info(f'{candidate.username or candidate.first_name} ran out of tries')


def delete_message(update, context):
    chat_id, candidate = context
    message_id = update.message.message_id
    updater.bot.deleteMessage(chat_id=chat_id, message_id=message_id)
    logging.info(f'Message from {candidate.username or candidate.first_name} was deleted')


def add_msg_to_db(update, context):
    from_user_id = update.message.from_user.id
    from_user = db.get(db.User, tg_id=from_user_id)
    if not from_user:
        logging.info(f'User is not in DB')
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


def leave(update, context):
    print('leave')
    user_id = update.message.from_user.id
    unset_timer(update, context)
    handlers_remover(dispatcher, 'mention_handler', user_id=user_id, group=3)
    handlers_remover(dispatcher, 'not_mention_handler', user_id=user_id, group=3)
    handlers_remover(dispatcher, 'yes_handler', user_id=user_id, group=2)
    handlers_remover(dispatcher, 'no_handler', user_id=user_id, group=2)
    handlers_remover(dispatcher, 'about_handler', user_id=user_id, group=1)
    handlers_remover(dispatcher, 'not_about_handler', user_id=user_id, group=1)
