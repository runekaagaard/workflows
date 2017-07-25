from collections import namedtuple
from functools import wraps


class InvalidArrowException(Exception):
    pass


def run_workflow(func, args, kwargs, state, error_step=None):
    ARROWS = namedtuple('ARROWS', 'continues aborts')("_continues_",
                                                      "_aborts_")
    for step in func(*args, **kwargs):
        try:
            state, arrow = step(state, ARROWS)
            if isinstance(arrow, Exception):
                setattr(arrow, 'state', state)
                raise arrow
        except Exception as exception:
            if error_step is None:
                raise
            else:
                state, arrow = error_step(exception, state, ARROWS)

        if arrow == ARROWS.continues:
            continue
        elif arrow == ARROWS.aborts:
            return state
        else:
            raise InvalidArrowException()

    return state


def workflow(state, error_step):
    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            return run_workflow(func, args, kwargs, state, error_step)

        return __

    return _


def reduces(reducer):
    return lambda state, arrows: (reducer(state), arrows.continues)


def aborts():
    return lambda state, arrows: (state, arrows.aborts)


def raises(exception):
    return lambda state, arrows: (state, exception)


def twelve_sucks(state, arrows):
    return state + 1213, arrows.continues


def sums_error(exception, state, arrows):
    return state + 10**6, arrows.continues


@workflow(state=0, error_step=sums_error)
def sums(xs):
    for x in xs:
        if x == 12:
            yield twelve_sucks
            continue
        if x > 16:
            yield raises(Exception("Noooo"))
            yield aborts()
        yield reduces(lambda state: state + x)


print sums(range(30))
