def handlers_remover(dispatcher, group):
    try:
        while dispatcher.handlers[group]:
            dispatcher.remove_handler(handler=dispatcher.handlers[group][0], group=group)
            print('Handler deleted')
    except KeyError:
        print(f'No handlers in group {group}')