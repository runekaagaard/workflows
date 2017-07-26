from collections import namedtuple
from functools import wraps
import threading


class WorkflowsException(Exception):
    pass


class InvalidArrowError(WorkflowsException):
    pass


ARROWS = namedtuple('ARROWS', 'continues aborts')(
    "_workflows_arrow_continues_", "_workflows_arrow_aborts_")
Stepped = namedtuple('Stepped', 'state send arrow')


def stepped(state, send=None, arrow=ARROWS.continues):
    return Stepped(state=state, send=send, arrow=arrow)


def parse_step(state_or_stepped, arrows):
    if isinstance(state_or_stepped, Stepped):
        return state_or_stepped
    else:
        return stepped(state_or_stepped)


def worker(func, args, kwargs, state, arrows, error_step=None):
    try:
        generator = func(*args, **kwargs)
        send = None
        while True:
            try:
                step = generator.send(send)
            except StopIteration:
                break
            state, send, arrow = parse_step(step(state), arrows)
            if arrow == arrows.continues:
                continue
            elif arrow == arrows.aborts:
                return state
            else:
                raise InvalidArrowError(arrow)
    except Exception as exception:
        if isinstance(exception, WorkflowsException) or error_step is None:
            raise
        else:
            state, send, arrow = parse_step(
                error_step(exception, state), arrows)
            if not arrow in arrows:
                raise InvalidArrowError(arrow)

    return state


def workflow(state, error_step=None, arrows=ARROWS, worker=worker):
    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            return worker(func, args, kwargs,
                          state()
                          if callable(state) else state, arrows, error_step)

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
    def step(state):
        state.append(x)
        return state

    return step


def calls(func, *args, **kwargs):
    return lambda state: stepped(state, send=func(*args, **kwargs))


local = threading.local()
local.state = State()
S = local.state

twelve_sucks = lambda state: state + 1213


def sums_error(exception, state):
    return state + 10**6


def bar(a, b):
    return a + b


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


@workflow(state=list)
def square(xs):
    for x in xs:
        foo = yield calls(bar, x, 10)
        yield append(foo)
        yield S.append(x**2)
        yield lambda s: s + [x**2]
        yield append(x**2)


print sums(range(30))
print sums(range(30))
print square(range(5))
print square(range(5))
