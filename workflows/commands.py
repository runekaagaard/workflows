from . import *

def when(predicate, *commands):
    p = maybe_callable(predicate)
    assert type(p) is bool
    if p:
        yield DO, commands
        yield SEND, True
    else:
        yield SEND, False

def unless(predicate, *commands):
    p = maybe_callable(predicate)
    assert type(p) is bool
    if not p:
        yield DO, commands
        yield SEND, False
    else:
        yield SEND, True

def returns(value):
    yield RETURN, value

def fold(callable, initial=0, key=GLOBAL):
    state = yield GET_STATE, None
    state[key] = callable(state.get(key, initial))
    yield SEND, state

def append(value, key, state=None):
    v = get_state(state, key, [])
    v.append(value)
    set_state(state, key, v)

def read_or(callable, *commands):
    try:
        value = callable()
        yield SEND, value
    except (KeyError, AttributeError, IndexError):
        yield DO, commands
        yield RETURN, None

def call(func, *args):
    yield CALL, lambda: func(*args)
    
def excepts(callable, exception):
    exceptions = maybe_list(exception)
    yield TRY, callable, exceptions

def loop(items, *commands):
    yield LOOP, commands
