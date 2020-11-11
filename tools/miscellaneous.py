import logging

logger = logging.getLogger('main_bot').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def handlers_remover(dispatcher, handler_type, user_id, group):
    try:
        for handler in dispatcher.handlers[group]:
            if handler.__name__ == str(handler_type) + str(user_id):
                try:
                    dispatcher.remove_handler(handler=handler, group=group)
                    logging.info(f'{handler.__name__} removed from group {group}')
                except Exception as e:
                    print(repr(e))
    except KeyError:
        logging.info(f'No handlers in group {group}')
        return KeyError
    except AttributeError:
        logging.info(f'Unnamed handler in group {group}')
    except Exception as e:
        logging.info(repr(e))
    # try:
    #     while dispatcher.handlers[group]:
    #         dispatcher.remove_handler(handler=dispatcher.handlers[group][0], group=group)
    #         # logging.info('Handler deleted')
    # except KeyError:
    #     pass
    #     # logging.info(f'No handlers in group {group}')

def add_logger_err(e):
    error_msg = repr(e)
    return logging.exception(error_msg)

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
