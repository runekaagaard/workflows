from .core import maybe_callable

CONTINUE = 1
RETURN = 2
ADD_FAIL_GUARD = 3
SEND = 4

def do_return(value):
    return {
        'result': maybe_callable(value, lambda: []), 
        'action': RETURN
    }


def do_send(value):
    return {
        'value': value,
        'action': SEND
    }


def do_continue():
    return {'action': CONTINUE}


def do_add_fail_guard(exception, returns):
    return {
        'action': ADD_FAIL_GUARD,
        'exception': exception, 
        'returns': returns,
    }