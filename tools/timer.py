import logging
import time

logger = logging.getLogger('timer').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def alarm(context):
    """Blocks the target when time runs out"""
    chat_id, target = context.job.context
    until_date = int(time.time())+5
    updater.bot.kick_chat_member(chat_id=chat_id, user_id=target.id, until_date=until_date)
    logging.info(f'{target.username or target.first_name} ran out of time and was banned')


def remove_job_if_exists(name, context):
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_timer(update, context, due, target):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(alarm, due, context=(chat_id, target), name=str(chat_id))

        text = 'Timer successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)
    except Exception as e:
        update.message.reply_text('Usage: /set <seconds>')


def unset_timer(update, context):
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
