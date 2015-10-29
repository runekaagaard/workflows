from collections import namedtuple
from .actions import *
from .core import maybe_callable

DEFAULT = '___DEFAULT___'
NOT_FOUND = '___NOT_FOUND___'

def feature(on_next=None, on_stop=None):
    return {
        'on_next': on_next,
        'on_stop': on_stop,
    }


def get_state(state):
    if DEFAULT in state:
        return state[DEFAULT]
    else:
        return state or None


def case(test, returns):
    def on_next(state):
        if test is True:
            return do_return(maybe_callable(returns, lambda: []))
        else:
            return do_continue()
    
    return feature(on_next=on_next)


def returns(value):
    def on_next(state):
        return do_return(value)
    
    return feature(on_next=on_next)


def fold(func, name=DEFAULT, initial=0):
    def on_next(state):
        value = state.get(name, NOT_FOUND)
        if value == NOT_FOUND:
            state[name] = initial
        if DEFAULT in state and name != DEFAULT:
            raise Exception('If one fold is named, then all most be named.')

        state[name] = func(state[name])
        return do_continue()

    def on_stop(state):
        return do_return(get_state(state))

    return feature(on_next=on_next, on_stop=on_stop)


def add_fail_guard(exception, returns=None):
    def on_next(state):
        return do_add_fail_guard(exception, returns)
    
    return feature(on_next=on_next)


def check(value, test=None, returns=None):
    if test is None:
        test = lambda x: x is not None
    if returns is None:
        returns = lambda state: None

    def on_next(state):
        if test(value) is True:
            return do_send(value)
        else:
            return do_return(maybe_callable(returns, [get_state(state)]))

    return feature(on_next=on_next)
