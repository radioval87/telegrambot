import logging
from typing import Dict
from time import sleep

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    run_async,
   
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
import os
from dotenv import load_dotenv


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

MENTIONING, WAITING, TYPING_ABOUT = range(3)



def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Hi! My name is Doctor Botter. I will hold a more complex conversation with you. "
        "Why don't you tell me something about yourself?")
    
    return MENTIONING


def done(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']
    update.message.reply_text(
        "I learned these facts about you:" "{}" "Until next time!".format(facts_to_str(user_data))
    )
    user_data.clear()
    return ConversationHandler.END

def new_member_validation(update: Update, context: CallbackContext) -> int:
    print('new_member_validation')
    update.message.reply_text("Mention")
    return WAITING

def delete_ment(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Deleted ment")
    return MENTIONING

def delete_wait(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Deleted wait")
    return WAITING

def delete_about(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Deleted about")
    return TYPING_ABOUT



def not_passed(update: Update, context: CallbackContext) -> int:
    print('not_passed')
    update.message.reply_text("Not passed")
    return MENTIONING

# def waiting(update: Update, context: CallbackContext):
#     print('waiting')
#     print(update.callback_query)
#     inviter_username = (update.message.text).strip('@')
#     updater.bot.sendMessage(chat_id=update.message.chat.id, text=('@'+inviter_username))
#     dispatcher.add_handler(MessageHandler(Filters.regex(r'да'), callback=choosing))
#     dispatcher.add_handler(MessageHandler(Filters.regex(r'нет'), callback=choosing))
#     return WAITING

# def choosing(update: Update, context: CallbackContext):
#     print('choosing')
#     print(update)
#     if update.message.text == 'да':
#         print('DAAA')
#         return TYPING_ABOUT
#     elif update.message.text == 'нет':
#         print('NEEEET')
#         return MENTIONING

CHECK = False
INVITER = None

def passed(update: Update, context: CallbackContext) -> int:
    print('passed')
    print(update.message.from_user.username)
    print(INVITER)
    global CHECK
    if update.message.from_user.username == INVITER:
        print('RAVNO')
        update.message.reply_text("Passed")
        CHECK = True
    update.message.reply_text("Deleted")

@run_async
def waiting(update: Update, context: CallbackContext):
    print('waiting')
    global INVITER 
    INVITER = (update.message.text).strip('@')
    updater.bot.sendMessage(chat_id=update.message.chat.id, text=('@'+INVITER))
    
    while CHECK == False:
        print(CHECK)
        # choosing()
        if CHECK == True:
            break
        sleep(5)
    return TYPING_ABOUT

def choosing():
    print('choosing')

    dispatcher.add_handler(MessageHandler(Filters.regex(r'да'), callback=passed))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'нет'), callback=not_passed))
    # if update.message.text == 'да':
    #     print('DAAA')
    #     return TYPING_ABOUT
    # elif update.message.text == 'нет':
    #     print('NEEEET')
    #     return MENTIONING


def final(update: Update, context: CallbackContext):
    print('final')
    update.message.reply_text("Молодец! Возьми с полки пирожок")
    return ConversationHandler.END

if __name__ == '__main__':
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENTIONING: [
                MessageHandler(
                    filters=(Filters.entity('mention') | Filters.entity('text_mention')),
                    callback=waiting),
                MessageHandler(
                    filters=(~Filters.entity('mention') | ~Filters.entity('text_mention')),
                    callback=delete_ment),
                MessageHandler(Filters.regex(r'да'), callback=passed),
                MessageHandler(Filters.regex(r'нет'), callback=not_passed)
            ],
            WAITING: [
                MessageHandler(Filters.regex(r'да'), callback=passed),
                MessageHandler(Filters.regex(r'нет'), callback=not_passed)
                # MessageHandler(~Filters.regex(r'nnn'), callback=delete_wait)
            ],
            TYPING_ABOUT: [
                MessageHandler(Filters.regex(r'#осебе'), callback=final),
                MessageHandler(~Filters.regex(r'#осебе'), callback=delete_about)
            ]

            # CHOOSING: [
            #     MessageHandler(
            #         Filters.regex('^(Age|Favourite colour|Number of siblings)$'), regular_choice
            #     ),
            #     MessageHandler(Filters.regex('^Something else...$'), custom_choice),
            # ],
            # TYPING_CHOICE: [
            #     MessageHandler(
            #         Filters.text & ~(Filters.command | Filters.regex('^Done$')), regular_choice
            #     )
            # ],
            # TYPING_REPLY: [
            #     MessageHandler(
            #         Filters.text & ~(Filters.command | Filters.regex('^Done$')),
            #         received_information,
            #     )
            # ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
    )

    dispatcher.add_handler(conv_handler, group=1)
    dispatcher.add_handler(MessageHandler(Filters.regex(r'да'), callback=passed))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'нет'), callback=not_passed))
    
    updater.start_polling()
    updater.idle()
