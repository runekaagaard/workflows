from collections import namedtuple
from functools import wraps, update_wrapper
import threading
import inspect


class WorkflowsException(Exception):
    pass


class InvalidArrowError(WorkflowsException):
    pass


ARROWS = namedtuple('ARROWS', 'continues aborts')(
    "_workflows_arrow_continues_", "_workflows_arrow_aborts_")
Stepped = namedtuple('Stepped', 'state send arrow')


def stepped(state, send=None, arrow=ARROWS.continues):
    return Stepped(state=state, send=send, arrow=arrow)
    

def parse_conditions(condition_s, args, kwargs, err_msg):
    for i, condition in enumerate(listify(condition_s), 1):
        assert condition(*args, **
                         kwargs) is not False, unicode(err_msg).format(
                             i, unicode(inspect.getsource(condition)))


def aborts():
    return lambda state: stepped(state, arrow=ARROWS.aborts)


def appends(x):
    def step(state):
        state.append(x)
        return state

    return step


def calls(func, *args, **kwargs):
    return lambda state: stepped(state, send=func(*args, **kwargs))


twelve_sucks = lambda state: state + 1213


def bar(a, b):
    return a + b


def listify(func_s):
    if callable(func_s):
        return [func_s]
    else:
        return func_s


def square_pre(xs):
    assert len(xs) < 10


def chain_wrap(func, wrapper_s):
    wrapped = func
    for wrapper in listify(wrapper_s):
        wrapped = wrapper(wrapped)

    #update_wrapper(func, wrapped)
    
    return wrapped


def worker(state, generator, wrap_generator, wrap_step):
    state = state() if callable(state) else state
    generator = chain_wrap(generator, wrap_generator)
    send = None
    while True:
        try:
            steps = generator.send(send)
        except StopIteration:
            return state
        for step in listify(steps):
            step = chain_wrap(step, wrap_step)
            state, send, arrow = step(state), None, ARROWS.continues
            if isinstance(state, Stepped):
                state, send, arrow = state

            if arrow == ARROWS.continues:
                continue
            elif arrow == ARROWS.aborts:
                return state
            else:
                raise InvalidArrowError(arrow)
    
    return state


def wf_kwargs(kwargs, keys, values):
    def _(key, value):
        wf_key = 'wf_' + key
        if wf_key in kwargs:
            tmp = kwargs[wf_key]
            del kwargs[wf_key]
            return tmp
        else:
            return value
        
    return [_(x, y) for x, y in zip(keys, values)]


def empty_workflow(state, worker=worker, generator_wrapper=lambda x: x, 
                   step_wrapper=lambda x: x):
    
    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            worker2, state2, generator_wrapper2, step_wrapper2= wf_kwargs(
                kwargs, 
                ['worker', 'state', 'generator_wrapper', 'step_wrapper'], 
                [worker, state, generator_wrapper, step_wrapper],
            )
            return worker2(state2, func(*args, **kwargs), generator_wrapper2, 
                           step_wrapper2)
        
        return __
    
    return _


def include(func, *args, **kwargs):
    def _(state):
        return func(*args, wf_state=state, **kwargs)
        
    return _


def sums_error(generator):
    try:
        for step in generator:
            yield step
    except Exception as e:
        yield lambda s: s - 10000000


def sums_wrapper(step):
    #return step
    return lambda state: step(state) + 4


@empty_workflow(state=0, 
                generator_wrapper=[sums_error],
                step_wrapper=sums_wrapper
)
def sums(xs):
    for x in xs:
        if x == 12:
            yield twelve_sucks
            continue
        if x > 16:
            raise Exception("Noooo")
            yield aborts()
        yield lambda s: s + x


@empty_workflow(state=list)
def append_two_and_three():
    yield appends(2)
    yield appends(3)


@empty_workflow(
    state=list, 
    #pre=lambda xs: len(xs) < 20, 
    #post=lambda s: len(s) < 310
)
def square(xs):
    yield include(append_two_and_three)

    for x in xs:
        yield appends((yield calls(bar, x, 10)))
        yield lambda s: s + [x**2]
        yield appends(x**2), appends(x**3)

    yield include(append_two_and_three)


print sums(range(30))
#print sums(range(30))
#print square(range(5))
#print square(range(10))

