from functools import wraps

from .actions import CONTINUE, RETURN, ADD_FAIL_GUARD, SEND
from .features import DEFAULT, get_state
from .core import maybe_callable

def workflow(f):
    @wraps(f)
    def _workflow(*args, **kwargs):
        state = {}
        fail_guards = {}
        send = None

        try:
            generator = f(*args, **kwargs)
            while True:
                config = generator.send(send)
                on_next = config.get('on_next')
                if on_next is not None:
                    result = config['on_next'](state)
                    if result['action'] == CONTINUE:
                        continue
                    elif result['action'] == RETURN:
                        return result['result']
                    elif result['action'] == ADD_FAIL_GUARD:
                        fail_guards[result['exception']] = result['returns']
                    elif result['action'] == SEND:
                        send = result['value']
                    else:
                        raise Exception("Unsupported action {}.".format(
                            result['action']))
        except StopIteration:
            on_stop = config.get('on_stop')
            if on_stop is not None:
                result = config['on_stop'](state)
                if result['action'] == RETURN:
                    return result['result']
                else:
                    raise Exception("Unsupported action {}.".format(
                        result['action']))
        except Exception as e:
            cls = e.__class__
            if cls in fail_guards:
                return maybe_callable(fail_guards[cls], 
                                      lambda: [get_state(state)])
            else:
                raise

    return _workflow

