import logging
import time

from .miscellaneous import add_logger_err

logger = logging.getLogger('timer').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def alarm(context):
    """Blocks the target when time runs out"""
    try:
        chat_id, target = context.job.context
        until_date = int(time.time())+31
        context.bot.kick_chat_member(chat_id=chat_id, user_id=target.id, until_date=until_date)
        logging.info(f'{target.username or target.first_name} ran out of time and was banned')
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

def set_timer(update, context, due, target):
    """Add a job to the queue."""
    try:
        chat_id = update.message.chat_id
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(alarm, due, context=(chat_id, target), name=str(chat_id))

        text = 'Timer successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)
    except Exception as e:
        add_logger_err(e)


def unset_timer(update, context):
    """Remove the job if the user changed their mind."""
    try:
        chat_id = update.message.chat_id
        job_removed = remove_job_if_exists(str(chat_id), context)
    except Exception as e:
        add_logger_err(e)
