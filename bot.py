import logging
import os
import time

import telegram
from dotenv import load_dotenv

import database.database as db

chat_id = 0

load_dotenv()

logger = logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logging.info("RV87_test_bot launched.")

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

WELCOME_MSG = ("Добро пожаловать, но у нас закрытое сообщество, поэтому " 
               "тэгни @ того, кто тебя сюда пригласил. У тебя есть 1 минута")

bot = telegram.Bot(TELEGRAM_TOKEN)

def get_updates():
    updates = bot.getUpdates()
    return updates

def get_last_update_id(updates):
    try:
        last_update_id = updates[-1].update_id
        logging.info(last_update_id)
        print(last_update_id)
    except IndexError:
        last_update_id = None
    return last_update_id

def get_new_members(last_update_id):
    new_members = []
    # last_update_id = get_last_update_id()
    for update in bot.getUpdates(offset=last_update_id, timeout=5):
        try:
            new_members.append(update.message.new_chat_members)
        except IndexError:
            new_members.append(None)
    print(new_members)
    return new_members

def get_chat_id(last_update_id):
    chat_id = None
    for update in bot.getUpdates():
        if last_update_id < update.update_id:
            chat_id = update.message.chat_id
    return chat_id

# def msg(msg):
#     chat_id = get_chat_id(last_update_id)
#     bot.sendMessage(chat_id=chat_id, text=msg)
#     logging.info("Sent message: " + msg)

def authentication():
    pass

def main():
    # global last_update_id
    # global chat_id
    while True:
        updates = get_updates()
        last_update_id = get_last_update_id(updates)
        new_members = get_new_members(last_update_id) or None
        chat_id = get_chat_id(last_update_id)
        if new_members:
            for new_member in new_members:
                print(new_member[0])
                bot.restrictChatMember(
                    chat_id=chat_id, 
                    user_id=new_member[0].id, 
                    permissions=telegram.ChatPermissions(can_send_messages = False)
                )
                bot.sendMessage(chat_id=os.getenv('TELEGRAM_CHAT_ID'), text=WELCOME_MSG)

if __name__ == '__main__':
    db.init_db()
    while True:
        main()
        time.sleep(1)

    #     if(user):
    #         try:
    #             username = update.message.new_chat_members[0].username
    #             first_name = update.message.new_chat_members[0].first_name
    #             last_name = update.message.new_chat_members[0].last_name
    #             group = update.message.chat.title
    #             msg('Welcome in the group ' + group + ', ' + first_name + ' ' + last_name + '! - @' + username + '\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
    #             pass
    #         except:
    #             try:
    #                 username = update.message.new_chat_members[0].username
    #                 first_name = update.message.new_chat_members[0].first_name
    #                 group = update.message.chat.title
    #                 msg('Welcome in the group ' + group + ', ' + first_name + '! - @' + username + '\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
    #                 pass
    #             except:
    #                 try:
    #                     username = update.message.new_chat_members[0].username
    #                     last_name = update.message.new_chat_members[0].first_name
    #                     group = update.message.chat.title
    #                     msg('Welcome in the group ' + group + ', ' + last_name + '! - @' + username + '\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
    #                     pass
    #                 except:
    #                     try:
    #                         first_name = update.message.new_chat_members[0].first_name
    #                         last_name = update.message.new_chat_members[0].last_name
    #                         group = update.message.chat.title
    #                         msg('Welcome in the group ' + group + ', ' + first_name + ' ' + last_name + '!\nJust ask a question.\nBbut first check me out! @WelcomeInDaHoodBot for the FAQ')
    #                         pass
    #                     except:
    #                         try:
    #                             first_name = update.message.new_chat_members[0].first_name
    #                             group = update.message.chat.title
    #                             msg('Welcome in the group ' + group + ', ' + first_name + '!\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
    #                             pass
    #                         except:
    #                             username = update.message.new_chat_members[0].username
    #                             group = update.message.chat.title
    #                             msg('Welcome in the group ' + group + ', ' + ' @' + username + '!\nJust ask a question.\nBut first check me out! @WelcomeInDaHoodBot for the FAQ')
    #                             pass
    #                         pass
    #                     pass
    #                 pass
    #             pass
    #     else:
    #         msg('Not a valid language!')
    #     pass
    # else:
    # #     pass

    # last_update_id = update.update_id






           # try:
                # if (is_group == True):
                #     message = update.message.text.encode('utf-8')
                #     logging.info('Got message from @' + update.message.from_user.username + ': ' + update.message.text)
                #     if message == '/faq':
                #         if lang == 'en':
                #             keyboard(1)
                #             pass
                #         else:
                #             msg('Not a valid language!')
                #         pass
                #     elif message == 'Next':
                #         keyboard(2)
                #         pass
                #     elif message == 'Exit':
                #         keyboard(3)
                #         pass
                #     elif message == 'How do I send photos with my bot?':
                #         msg("bot.sendPhoto(chat_id=chat_id, photo=open('path/image.jpg', 'rb').read())")
                #         pass
                #     elif message == 'How can I check if the message comes from a chat or a group?':
                #         msg('is_group = update.message.chat_id != update.message.from_user.id\nTrue = it is, False = it a personal chat.')
                #         pass
                #     elif message == 'Question 3':
                #         msg('Answer 3')
                #         pass
                #     elif message == 'Question 4':
                #         msg('Answer 4')
                #         pass
                #     elif message == 'Question 5':
                #         msg('Answer 5')
                #         pass
                #     elif message == 'Question 6':
                #         msg('Answer 6')
                #         pass
                #     pass
                # pass
            # except:
            #     pass