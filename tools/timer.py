import logging
import time

from telegram import error

from .miscellaneous import add_logger_err

logger = logging.getLogger('timer').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def alarm(context):
    """Blocks the target when time runs out"""
    try:
        chat_id = context.job.context.chat_data.get('chat_id')
        target = context.job.context.user_data.get('new_member')
        until_date = int(time.time())+31
        context.bot.kick_chat_member(chat_id=chat_id,
                                     user_id=target.id, until_date=until_date)
        logging.info(f'{target.username or target.first_name}'+
                     ' ran out of time and was banned')
    except error.BadRequest as e:
        logging.info(f'Alarm failed with error: {e.message}')
    except Exception as e:
        add_logger_err(e)

def remove_job_if_exists(name, context):
    """Remove job with given name. Returns whether job was removed."""
    try:
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True
    except Exception as e:
        add_logger_err(e)

def set_timer(context, due):
    """Add a job to the queue."""
    try:
        chat_id = context.chat_data.get('chat_id')
        target = context.user_data.get('new_member')
        name = str(chat_id) + str(target.id)
        job_removed = remove_job_if_exists(name, context)
        context.job_queue.run_once(alarm, due, name=name, context=context)
        logging.info('Timer successfully set!')
    except Exception as e:
        add_logger_err(e)


def unset_timer(context):
    """Remove the timer."""
    try:
        print(context.chat_data)
        print(context.user_data)
        chat_id = context.chat_data.get('chat_id')
        target = context.user_data.get('new_member')
        name = str(chat_id) + str(target.id)
        job_removed = remove_job_if_exists(name, context)
        if job_removed:
            logging.info('Timer was unset')
        else:
            logging.info('There was no timer')
    except AttributeError:
        logging.info('There was no timer')
    except Exception as e:
        add_logger_err(e)
