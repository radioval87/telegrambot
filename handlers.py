import logging
import time
from datetime import datetime

# from djantimat.helpers import RegexpProc
from dotenv import load_dotenv
from telegram import ChatPermissions, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Filters, MessageHandler

import database.database as db
from tools.bot_messages import (WELCOME_MSG, VALIDATION_MSG,
                                VALIDATION_NEGATIVE_MSG,
                                VALIDATION_POSITIVE_MSG,
                                CANT_INVITE_MSG, REGISTERED_MSG)
from tools.miscellaneous import detect_msg_type, handlers_remover, msg
from tools.timer import set_timer, unset_timer

load_dotenv()

logger = logging.getLogger('main_bot').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

validation_keyboard = ReplyKeyboardMarkup([['Да', 'Нет']],
                                          resize_keyboard=True,
                                          one_time_keyboard=True,
                                          selective=True)
remove_keyboard = ReplyKeyboardRemove()

CANDIDATE_DUE = 500
INVITER_DUE = 600


class MainHandlers:
    '''Welcoming new members'''
    def __init__(self, updater):
        self.updater = updater
        self.dispatcher = updater.dispatcher

    def new_member_start(self, update, context):
        '''Any newcomer is handled by this method first'''
        print('new_member_start')
        chat_id = update.message.chat.id
        chat = db.get_or_create(db.Chat, chat_id=chat_id)
        print(f'============================={chat}')
        context.chat_data.update({'chat_id': chat_id})
        inviter = update.message.from_user
        for new_member in update.message.new_chat_members:
            logging.info(f'{new_member.username or new_member.first_name} \
            joined chat')
            context.user_data.update({'new_member': new_member})
            if chat.ban_mode == 1:
                self.negative_validation(update, context)
            
            elif inviter.id != new_member.id:
                context.user_data.update({'inviter': inviter})
                self.manual_invite_validation(update, context)
            # When user enters by link, he is in message.from_user and
            # in message.new_chat_members at the same time
            else:
                self.link_invite_validation(update, context)

    def manual_invite_validation(self, update, context):
        print('manual_invite_validation')
        chat_id = update.message.chat.id
        inviter = update.message.from_user
        new_member = context.user_data.get('new_member')
        inviter = db.get(db.User, tg_id=inviter.id, enter_chat_id=chat_id)
        if inviter.invites > 0:
            context.user_data.update({'inviter': inviter})
            return self.positive_validation(update, context)
        #31 seconds is a minimum ban period
        until_date = int(time.time())+31
        msg(self.updater, chat_id=chat_id, text=(f'{inviter.first_name}, \
                                                 {CANT_INVITE_MSG}'))
        return self.updater.bot.kick_chat_member(chat_id=chat_id,
                                                 user_id=new_member.id,
                                                 until_date=until_date)

    def link_invite_validation(self, update, context, tries=3):
        '''Joined the group via invite link scenario.'''
        print('link_invite_validation')
        chat_id = update.message.chat.id
        new_member = context.user_data.get('new_member')
        if tries > 0:
            msg(self.updater, chat_id=chat_id, text=(f'{new_member.first_name}, \
                                                     {WELCOME_MSG}'))
            #activates the timer that bans the target if the due is reached
            context.chat_data.update({'chat_id': chat_id})
            set_timer(context, due=CANDIDATE_DUE, target=new_member)

            mention_handler = MessageHandler(
                filters=(Filters.user(new_member.id) &
                         Filters.chat(chat_id) &
                        (Filters.entity('mention') |
                         Filters.entity('text_mention'))),
                callback=lambda update, context: self.new_member_validation(
                    update, context, tries))
            mention_handler.__name__ = 'mention_handler' + str(new_member.id) + str(chat_id)

            not_mention_handler = MessageHandler(
                filters=(Filters.user(new_member.id) &
                         Filters.chat(chat_id) &
                        (~Filters.entity('mention') |
                         ~Filters.entity('text_mention'))),
                callback=self.delete_message)
            not_mention_handler.__name__ = 'not_mention_handler' + str(new_member.id) + str(chat_id)

            self.dispatcher.add_handler(mention_handler, group=3)
            self.dispatcher.add_handler(not_mention_handler, group=3)

        else:
            return self.negative_validation(update,context)


    def new_member_validation(self, update, context, tries):
        print('new_member_validation')
        
        chat_id = update.message.chat.id
        candidate = context.user_data.get('new_member')
        unset_timer(context)

        handlers_remover(self.dispatcher, 'mention_handler', user_id=candidate.id, chat_id=chat_id, group=3)
        handlers_remover(self.dispatcher, 'not_mention_handler', user_id=candidate.id, chat_id=chat_id, group=3)

        inviter_username = (update.message.text).strip('@')
        try:
            inviter = (db.get(db.User, username=inviter_username, enter_chat_id=chat_id) or
                       db.get(db.User, tg_id=update.message.entities[0].user.id, enter_chat_id=chat_id))
        except AttributeError:
            inviter = None
        if inviter and inviter.invites > 0:
            context.bot.restrict_chat_member(chat_id=chat_id, user_id=candidate.id,
            permissions=ChatPermissions(can_send_messages=False,
                                        can_send_media_messages=False,
                                        can_send_other_messages=False,
                                        can_add_web_page_previews=False,
                                        ))
            set_timer(context, due=INVITER_DUE, target=candidate)
            if inviter.username != 'NULL':
                msg(self.updater, chat_id=chat_id, text=('@' + inviter.username + ', ' + VALIDATION_MSG + f' ({candidate.first_name}/{candidate.username or "без username"})?'), reply_markup=validation_keyboard)
            else:
                text = f'[{inviter.first_name}](tg://user?id={inviter.tg_id}), {VALIDATION_MSG} {candidate.first_name}/{candidate.username or "без username"}?'
                msg(self.updater, chat_id=chat_id, text=text, reply_markup=validation_keyboard, parse_mode='MarkdownV2')
            

            yes_handler = MessageHandler(filters=(Filters.regex('Да') &
                                                  Filters.chat(chat_id) &
                                                  Filters.user(inviter.tg_id)),
                                        callback=lambda update, context: self.positive_validation(update, context, additional_context = (inviter, candidate)))
            yes_handler.__name__ = 'yes_handler' + str(inviter.tg_id) + str(chat_id)

            no_handler = MessageHandler(filters=(Filters.regex('Нет') &
                                                 Filters.chat(chat_id) &
                                                 Filters.user(inviter.tg_id)),
                                        callback=lambda update, context: self.negative_validation(update, context, additional_context = (inviter, candidate)))
            no_handler.__name__ = 'no_handler' + str(inviter.tg_id) + str(chat_id)

            self.dispatcher.add_handler(yes_handler, group=2)
            self.dispatcher.add_handler(no_handler, group=2)
        else:
            msg(self.updater, chat_id=chat_id, text=VALIDATION_NEGATIVE_MSG)
            tries -= 1
            update.message.entities = []
            update.message.text = ''
            return self.link_invite_validation(update, context, tries)


    def positive_validation(self, update, context, additional_context=None):
        print('positive_validation')
        chat_id = update.message.chat.id
        if additional_context is not None:
            inviter, candidate = additional_context
        else:
            inviter = context.user_data.get('inviter')
            candidate = context.user_data.get('new_member')
        
        context.user_data.update({'inviter': inviter})
        context.user_data.update({'new_member': candidate})
        try:
            unset_timer(context)
            handlers_remover(self.dispatcher, 'yes_handler', user_id=inviter.tg_id, chat_id=chat_id, group=2)
            handlers_remover(self.dispatcher, 'no_handler', user_id=inviter.tg_id, chat_id=chat_id, group=2)
            context.bot.restrict_chat_member(chat_id=chat_id, user_id=candidate.id,
                permissions=ChatPermissions(can_send_messages=True))
            logging.info(f'{candidate.username or candidate.first_name} was invited by link')
        except AttributeError:
            logging.info(f'{candidate.username or candidate.first_name} was invited directly')
        text = f'{candidate.first_name}, {VALIDATION_POSITIVE_MSG}'
        msg(self.updater, chat_id=chat_id, text=text, reply_markup=remove_keyboard)

        about_handler = MessageHandler(
            filters=(Filters.user(candidate.id) &
                    Filters.regex(r'#осебе') &
                    Filters.chat(chat_id)),
            # callback=self.add_new_member)
            callback=lambda update, context: self.add_new_member(update, context, additional_context = (inviter, candidate)))
        about_handler.__name__ = 'about_handler' + str(candidate.id) + str(chat_id)

        not_about_handler = MessageHandler(
            filters=(Filters.user(candidate.id) &
                    Filters.chat(chat_id) &
                    (~Filters.regex('#осебе'))),
            # callback=self.delete_message)
            callback=lambda update, context: self.delete_message(update, context, additional_context=candidate))
        not_about_handler.__name__ = 'not_about_handler' + str(candidate.id) + str(chat_id)

        self.dispatcher.add_handler(about_handler, group=1)
        self.dispatcher.add_handler(not_about_handler, group=1)
        for handler in self.dispatcher.handlers[1]:
            print(handler.filters)


    def add_new_member(self, update, context, additional_context=None):
        print('add_new_member')
        chat_id = update.message.chat.id
        if additional_context is not None:
            inviter, candidate = additional_context
        else:
            inviter = context.user_data.get('inviter')
            candidate = context.user_data.get('new_member')
        text = f'{candidate.first_name}, {REGISTERED_MSG}'
        msg(self.updater, chat_id=chat_id, text=text)
        handlers_remover(self.dispatcher, 'about_handler', user_id=candidate.id, chat_id=chat_id, group=1)
        handlers_remover(self.dispatcher, 'not_about_handler', user_id=candidate.id, chat_id=chat_id, group=1)
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


    def negative_validation(self, update, context, additional_context=None):
        print('negativ_validation')
        chat_id = update.message.chat.id
        if additional_context is not None:
            inviter, candidate = additional_context
        else:
            inviter = context.user_data.get('inviter')
            candidate = context.user_data.get('new_member')
        unset_timer(context)
        try:
            unset_timer(context)
            handlers_remover(self.dispatcher, 'yes_handler', user_id=inviter.tg_id, chat_id=chat_id, group=2)
            handlers_remover(self.dispatcher, 'no_handler', user_id=inviter.tg_id, chat_id=chat_id, group=2)
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
                                        can_add_web_page_previews=True,
                                        can_send_polls=True,
                                        can_invite_users=True,
                                        can_pin_messages=True))
        
        self.updater.bot.kick_chat_member(chat_id=chat_id, user_id=candidate.id, until_date=until_date)

        try:
            if inviter.username != 'NULL':
                logging.info(f'{inviter.username} denied {candidate.username or candidate.first_name}')
            logging.info(f'{inviter.first_name or "Chat"} denied {candidate.username or candidate.first_name}')
        except AttributeError:
            logging.info(f'{candidate.username or candidate.first_name} ran out of tries')


    def delete_message(self, update, context, additional_context=None):
        chat_id = update.message.chat.id
        if additional_context is not None:
            candidate = additional_context
        else:
            candidate = context.user_data.get('new_member')
        message_id = update.message.message_id
        self.updater.bot.deleteMessage(chat_id=chat_id, message_id=message_id)
        logging.info(f'Message from {candidate.username or candidate.first_name} was deleted')


    def add_msg_to_db(self, update, context):
        chat_id = update.message.chat.id
        chat = db.get(db.Chat, chat_id=chat_id)
        from_user_id = update.message.from_user.id
        from_user = db.get(db.User, tg_id=from_user_id, enter_chat_id=chat_id)
        if not from_user:
            logging.info('User is not in DB')
        else:
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
                    'chat_id': chat.chat_id,
                    'mat': mat,
                    'caps': caps}
            db.create(db.Message, **new_msg)


    def add_admin(self, update, context):
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


    def leave(self, update, context):
        print('leave')
        user = update.message.left_chat_member
        user_id = user.id
        chat_id = update.message.chat.id
        context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True,
                                        can_send_media_messages=True,
                                        can_send_other_messages=True,
                                        can_add_web_page_previews=True,
                                        can_send_polls=True,
                                        can_invite_users=True,
                                        can_pin_messages=True))
        unset_timer(context)
        handlers_remover(self.dispatcher, 'mention_handler', user_id, chat_id, 3)
        handlers_remover(self.dispatcher, 'not_mention_handler', user_id, chat_id, 3)
        handlers_remover(self.dispatcher, 'yes_handler', user_id, chat_id, 2)
        handlers_remover(self.dispatcher, 'no_handler', user_id, chat_id, 2)
        handlers_remover(self.dispatcher, 'about_handler', user_id, chat_id, 1)
        handlers_remover(self.dispatcher, 'not_about_handler', user_id, chat_id, 1)
        logging.info(f'{user.username or user.first_name} left chat {chat_id}')
