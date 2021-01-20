import logging
import os

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

import handlers

load_dotenv()

logger = logging.getLogger('main_bot').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

def main():
    logging.info('Bot launched.')
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    mh = handlers.MainHandlers(updater)

    dispatcher.add_handler(MessageHandler(
        filters=Filters.status_update.new_chat_members,
        callback=mh.new_member_start), group=4)
    dispatcher.add_handler(MessageHandler(
        filters=((~Filters.status_update.new_chat_members) &
        (~Filters.command)), callback=mh.add_msg_to_db), group=4)
    dispatcher.add_handler(MessageHandler(
        filters=Filters.status_update.left_chat_member,
        callback=mh.leave))
    dispatcher.add_handler(CommandHandler('admin', callback=mh.add_admin))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
