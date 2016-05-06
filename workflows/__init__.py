from functools import wraps

DO = 1
SEND = 2
CALL = 3
RETURN = 4
TRY = 5
LOOP = 6
GET_STATE = 7

GLOBAL = "__GLOBAL__"
DONT_RETURN = "__DONT_RETURN__"


def workflow(f):
    @wraps(f)
    def _workflow(*args, **kwargs):
        state = {}
        excepts = {}

        global send_command, send
        send = None
        send_command = None

        def process(command, value):
            global send_command, send
            if command == SEND:
                send = value
            elif command == DO:
                for _value in value:
                    for __value, __command in _value:
                        result = process(__value, __command)
                        if result != DONT_RETURN:
                            return result
            elif command == RETURN:
                return value
            elif command == GET_STATE:
                send_command = state
            elif command == CALL:
                value()
            else:
                raise Exception("Unknown command")

            return DONT_RETURN
        try:
            generator = f(*args, **kwargs)
            while True:
                commands = generator.send(send)
                send = None
                try:
                    while True:
                        command, value = commands.send(send_command)
                        send_command = None
                        result = process(command, value)
                        if result != DONT_RETURN:
                            return result
                except StopIteration:
                    pass
        except StopIteration:
            try:
                return state[GLOBAL]
            except:
                return state

    return _workflow

def maybe_callable(value, *args):    
    return value(*args()) if callable(value) else value