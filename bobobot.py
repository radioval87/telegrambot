import logging
import os
import time
from datetime import datetime

# from djantimat.helpers import RegexpProc
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatPermissions
from telegram.ext import Filters, MessageHandler, CommandHandler, Updater

import database.database as db
from tools.miscellaneous import handlers_remover, detect_msg_type
from tools.timer import set_timer, unset_timer
# from tools.bot_messages import *
from handlers import main_handlers

load_dotenv()

logger = logging.getLogger('main_bot').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# validation_keyboard = ReplyKeyboardMarkup([['Да', 'Нет']],
#                                           resize_keyboard=True,
#                                           one_time_keyboard=True,
#                                           selective=True)
# remove_keyboard = ReplyKeyboardRemove()



if __name__ == '__main__':
    logging.info('RV87_test_bot launched.')
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    updater.start_polling()
    updater.idle()
