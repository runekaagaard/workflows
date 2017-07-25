from collections import namedtuple
from functools import wraps


class WorkflowsException(Exception):
    pass


class InvalidArrowError(WorkflowsException):
    pass


ARROWS = namedtuple('ARROWS', 'continues aborts')(
    "_workflows_arrow_continues_", "_workflows_arrow_aborts_")


def parse_step(stepped, arrows):
    if type(stepped) is tuple and stepped[1] in arrows:
        return stepped
    else:
        return stepped, arrows.continues


def worker(func, args, kwargs, state, arrows, error_step=None):
    try:
        for step in func(*args, **kwargs):
            state, arrow = parse_step(step(state), arrows)
            if arrow == arrows.continues:
                continue
            elif arrow == arrows.aborts:
                return state
            else:
                raise InvalidArrowError()
    except Exception as exception:
        if isinstance(exception, WorkflowsException) or error_step is None:
            raise
        else:
            state, arrow = parse_step(error_step(exception, state), arrows)
            if not arrow in arrows:
                raise InvalidArrowError()

    return state


def workflow(state, error_step=None, arrows=ARROWS, worker=worker):
    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            return worker(func, args, kwargs, state, arrows, error_step)

        return __

    return _


def reduces(reducer):
    return lambda state: reducer(state)


def aborts():
    return lambda state: (state, ARROWS.aborts)


twelve_sucks = lambda state: state + 1213


def sums_error(exception, state):
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
