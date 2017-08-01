from collections import namedtuple
from functools import wraps
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


def run_step(step,
             state,
             args,
             kwargs,
             arrows,
             error_step,
             worker,
             pre,
             post,
             exception=None):
    def parse_step(state_or_stepped, arrows):
        if isinstance(state_or_stepped, Stepped):
            if state_or_stepped.arrow not in arrows:
                raise InvalidArrowError(arrow)
            return state_or_stepped
        else:
            return stepped(state_or_stepped)

    if hasattr(step, 'is_workflow'):
        return parse_step(
            step.wf_undecorate2(lambda: state, error_step, arrows, worker, pre,
                                post)(step.wf_undecorate1)(*args, **kwargs),
            arrows)
    else:
        return parse_step(
            step(*([state] if exception is None else [state, exception])),
            arrows)

def run_step2(step, state):
    def parse_step(state_or_stepped, arrows):
        if isinstance(state_or_stepped, Stepped):
            if state_or_stepped.arrow not in arrows:
                raise InvalidArrowError(arrow)
            return state_or_stepped
        else:
            return stepped(state_or_stepped)
    
    return getattr(step, 'wf_run_step', step)(state)
    

def parse_conditions(condition_s, args, kwargs, err_msg):
    for i, condition in enumerate(listify(condition_s), 1):
        assert condition(*args, **
                         kwargs) is not False, unicode(err_msg).format(
                             i, unicode(inspect.getsource(condition)))


def worker(func, args, kwargs, state, arrows, error_step, pre, post):
    def output(state, post):
        parse_conditions(post, (state, ), {},
                         "Postcondition nr. {} failed: {}")
        return state

    parse_conditions(pre, args, kwargs, "Precondition nr. {} failed: {}")
    try:
        generator = func(*args, **kwargs)
        send = None
        while True:
            try:
                steps = generator.send(send)
            except StopIteration:
                return output(state, post)
            for step in listify(steps):
                state, send, arrow = run_step(step, state, args, kwargs,
                                              ARROWS, error_step, worker, pre,
                                              post)
                if arrow == arrows.continues:
                    continue
                elif arrow == arrows.aborts:
                    return output(state, post)
                else:
                    raise InvalidArrowError(arrow)
    except Exception as exception:
        if isinstance(exception, WorkflowsException) or error_step is None:
            raise
        else:
            state, send, arrow = run_step(error_step, state, args, kwargs,
                                          ARROWS, error_step, worker, pre,
                                          post, exception)
            return output(state, post)






def workflow(state,
             error_step=None,
             arrows=ARROWS,
             worker=worker,
             pre=lambda *args, **kwargs: None,
             post=lambda state: None):
    def _(func):
        func.is_workflow = True
        func.wf_undecorate1 = func
        func.wf_undecorate2 = workflow

        @wraps(func)
        def __(*args, **kwargs):
            return worker(func, args, kwargs,
                          state() if callable(state) else state, arrows,
                          error_step, pre, post)

        return __

    return _


def reduces(reducer):
    return lambda state: reducer(state)


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


def sums_error(state, exception):
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
        yield lambda s: s + x


def listify(func_s):
    if callable(func_s):
        return [func_s]
    else:
        return func_s


def square_pre(xs):
    assert len(xs) < 10


from functools import update_wrapper

def chain_wrap(func, wrapper_s):
    wrapped = func
    for wrapper in listify(wrapper_s):
        wrapped = wrapper(wrapped)

    #update_wrapper(func, wrapped)
    
    return wrapped


def worker2(state, generator, wrap_generator, wrap_step):
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

def empty_workflow(state, worker=worker2, generator_wrapper=lambda x: x, 
                   step_wrapper=lambda x: x):
    
    def _(func):
        func.wf_state = state
        @wraps(func)
        def __(*args, **kwargs):
            state, = wf_kwargs(kwargs, ['state'], [func.wf_state])
            print state
            return worker(state, func(*args, **kwargs), generator_wrapper, 
                          step_wrapper)
        
        return __
    
    return _

def include(func, *args, **kwargs):
    def _(state):
        return func(*args, wf_state=state, **kwargs)
        
    return _


@empty_workflow(state=lambda *a, **ka: [])
def append_two_and_three(xs):
    print "YOYO"
    yield appends(2)
    yield appends(3)


@empty_workflow(
    state=list, 
    #pre=lambda xs: len(xs) < 20, 
    #post=lambda s: len(s) < 310
)
def square(xs):
    yield include(append_two_and_three, xs)

    for x in xs:
        yield appends((yield calls(bar, x, 10)))
        yield lambda s: s + [x**2]
        yield appends(x**2), appends(x**3)

    yield include(append_two_and_three, xs)


#print sums(range(30))
#print sums(range(30))
print square(range(5))
#print square(range(10))

