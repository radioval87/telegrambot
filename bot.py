import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
import database.database as db


# import urllib
# import json


chat_id = 0
lang = 'en'


load_dotenv()
# logger = logging.getLogger('telegrambot')
# logging.basicConfig()

logger = logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logging.info("RV87_test_bot launched.")

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telegram.Bot(TELEGRAM_TOKEN)

try:
    LAST_UPDATE_ID = bot.getUpdates()[-1].update_id
except IndexError:
    LAST_UPDATE_ID = None

def msg(msg):
    bot.sendMessage(chat_id=chat_id, text=msg)
    logging.info("Send message: " + msg)
    # pass

def echo():
    global LAST_UPDATE_ID
    global chat_id
    for update in bot.getUpdates(offset=LAST_UPDATE_ID):
        if LAST_UPDATE_ID < update.update_id:
            chat_id = update.message.chat_id
            is_group = update.message.chat_id != update.message.from_user.id
            usernamefrom = update.message.from_user.username
            try:
                if (is_group == False):
                    message = update.message.text.encode('utf-8')
                    logging.info('Got message from @' + update.message.from_user.username + ': ' + update.message.text)
                    if message == '/faq':
                        if lang == 'en':
                            keyboard(1)
                            pass
                        else:
                            msg('Not a valid language!')
                        pass
                    elif message == 'Next':
                        keyboard(2)
                        pass
                    elif message == 'Exit':
                        keyboard(3)
                        pass
                    elif message == 'How do I send photos with my bot?':
                        msg("bot.sendPhoto(chat_id=chat_id, photo=open('path/image.jpg', 'rb').read())")
                        pass
                    elif message == 'How can I check if the message comes from a chat or a group?':
                        msg('is_group = update.message.chat_id != update.message.from_user.id\nTrue = it is, False = it a personal chat.')
                        pass
                    elif message == 'Question 3':
                        msg('Answer 3')
                        pass
                    elif message == 'Question 4':
                        msg('Answer 4')
                        pass
                    elif message == 'Question 5':
                        msg('Answer 5')
                        pass
                    elif message == 'Question 6':
                        msg('Answer 6')
                        pass
                    pass
                pass
            except:
                pass
            
            try:
                user = update.message.new_chat_members[0]
            except IndexError:
                user = None

            if(user):
                if lang == 'en':
                    try:
                        username = update.message.new_chat_members[0].username
                        first_name = update.message.new_chat_members[0].first_name
                        last_name = update.message.new_chat_members[0].last_name
                        group = update.message.chat.title
                        msg('Welcome in the group ' + group + ', ' + first_name + ' ' + last_name + '! - @' + username + '\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
                        pass
                    except:
                        try:
                            username = update.message.new_chat_members[0].username
                            first_name = update.message.new_chat_members[0].first_name
                            group = update.message.chat.title
                            msg('Welcome in the group ' + group + ', ' + first_name + '! - @' + username + '\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
                            pass
                        except:
                            try:
                                username = update.message.new_chat_members[0].username
                                last_name = update.message.new_chat_members[0].first_name
                                group = update.message.chat.title
                                msg('Welcome in the group ' + group + ', ' + last_name + '! - @' + username + '\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
                                pass
                            except:
                                try:
                                    first_name = update.message.new_chat_members[0].first_name
                                    last_name = update.message.new_chat_members[0].last_name
                                    group = update.message.chat.title
                                    msg('Welcome in the group ' + group + ', ' + first_name + ' ' + last_name + '!\nJust ask a question.\nBbut first check me out! @WelcomeInDaHoodBot for the FAQ')
                                    pass
                                except:
                                    try:
                                        first_name = update.message.new_chat_members[0].first_name
                                        group = update.message.chat.title
                                        msg('Welcome in the group ' + group + ', ' + first_name + '!\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
                                        pass
                                    except:
                                        username = update.message.new_chat_members[0].username
                                        group = update.message.chat.title
                                        msg('Welcome in the group ' + group + ', ' + ' @' + username + '!\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
                                        pass
                                    pass
                                pass
                            pass
                        pass
                else:
                    msg('Not a valid language!')
                pass
            else:
                pass

            LAST_UPDATE_ID = update.update_id

if __name__ == '__main__':
    db.init_db()
    while True:
        echo()
        time.sleep(1)
