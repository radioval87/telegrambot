import logging

logger = logging.getLogger('errors').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def handlers_remover(dispatcher, group):
    try:
        while dispatcher.handlers[group]:
            dispatcher.remove_handler(handler=dispatcher.handlers[group][0], group=group)
            print('Handler deleted')
    except KeyError:
        print(f'No handlers in group {group}')

def add_logger_err(e):
    error_msg = repr(e)
    return logger.exception(error_msg)

def detect_msg_type(message):
    if message.text:
        return 'Text'
    elif message.document:
        if message.document.mime_type:
            return message.document.mime_type
        return 'Unknown document'
    elif message.photo:
        return 'Photo'
    else:
        return 'Unknown'