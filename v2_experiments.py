from collections import namedtuple
from functools import wraps


class InvalidArrowException(Exception):
    pass


def run_workflow(func, args, kwargs, state, error_step=None):
    def parse_step(stepped):
        if type(stepped) is tuple:
            return stepped
        else:
            return stepped, ARROWS.continues

    ARROWS = namedtuple('ARROWS', 'continues aborts')("_continues_",
                                                      "_aborts_")
    try:
        for step in func(*args, **kwargs):
            state, arrow = parse_step(step(state, ARROWS))

            if arrow == ARROWS.continues:
                continue
            elif arrow == ARROWS.aborts:
                return state
            else:
                raise InvalidArrowException()
    except Exception as exception:
        if isinstance(exception, InvalidArrowException) or error_step is None:
            raise
        else:
            state, arrow = parse_step(error_step(exception, state, ARROWS))

    return state


def workflow(state, error_step):
    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            return run_workflow(func, args, kwargs, state, error_step)

        return __

    return _


def reduces(reducer):
    return lambda state, arrows: reducer(state)


def aborts():
    return lambda state, arrows: (state, arrows.aborts)


def twelve_sucks(state, arrows):
    return state + 1213


def sums_error(exception, state, arrows):
    return state + 10**6


@workflow(state=0, error_step=sums_error)
def sums(xs):
    for x in xs:
        if x == 12:
            yield twelve_sucks
            continue
        if x > 16:
            raise Exception("Noooo")
            yield aborts()
        yield reduces(lambda state: state + x)


print sums(range(30))
