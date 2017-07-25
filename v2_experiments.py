from collections import namedtuple
from functools import wraps
import threading


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


import operator


class State(object):
    def __init__(self):
        self.ops = []

    def __add__(self, x):
        self.ops.append(lambda state: operator.__add__(state, x))
        return self

    def __radd__(self, x):
        self.ops.append(lambda state: operator.__add__(state, x))
        return self

    def __sub__(self, x):
        self.ops.append(lambda state: operator.__sub__(state, x))
        return self

    def __rsub__(self, x):
        self.ops.append(lambda state: operator.__sub__(state, x))
        return self

    def __gt__(self, x):
        self.ops.append(lambda state: state > x)
        return self

    def append(self, x):
        def get(state, x):
            state.append(x)
            return state

        self.ops.append(lambda state: get(state, x))
        return self

    def __call__(self, state):
        for op in self.ops:
            state = op(state)

        self.ops = []
        return state


def append(x):
    return lambda state: state + [x]


local = threading.local()
local.state = State()
S = local.state

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
        #yield lambda s: s + x
        yield S + x


@workflow(state=[])
def square(xs):
    for x in xs:
        yield S.append(x**2)
        yield lambda s: s + [x**2]
        yield append(x**2)


print sums(range(30))
print square(range(5))
