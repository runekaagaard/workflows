# coding=utf-8
import inspect
from functools import wraps

def listify(func_s):
    if callable(func_s):
        return [func_s]
    else:
        return func_s


def parse_conditions(condition_s, args, kwargs, title):
    err_msg = unicode(title) + u" nr. {} failed: {}"
    for i, condition in enumerate(listify(condition_s), 1):
        assert condition(*args, **
                         kwargs) is not False, unicode(err_msg).format(
                             i, unicode(inspect.getsource(condition)))



def contract(pre_conditions, post_conditions):
    """
    Pre is before. Post is after.
    """
    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            parse_conditions(pre_conditions, args, kwargs, 
                             title='Preconditions')
            result = func(*args, **kwargs)
            parse_conditions(post_conditions, [result], {}, 
                             title='Postconditions')
            return result
        return __
    return _


def processing(pre_process, post_process=2):
    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            args, kwargs = pre_process(*args, **kwargs)
            return post_process(func(*args, **kwargs))
        return __
    return _


def compose(*workflows):
        def __(*args, **kwargs):
            assert len(args) == 0, "Only keywords allowed."
            last_wf = lambda x: x
            for workflow in workflows:
                wf_kwargs = {}
                for arg in inspect.getargspec(workflow).args:
                    wf_kwargs[arg] = kwargs[arg]
                last_wf = workflow(**wf_kwargs)
            return last_wf
        return __

someworkflow = compose(contract, processing)
print someworkflow

@someworkflow(
    pre_conditions=lambda x: x == 2,
    post_conditions=lambda r: r == 14,
    pre_process=lambda x: ([x + 1], {}),
    post_process=lambda x: x + 1,
)
def somefunc(x):
    """
    Very important: x must be 2!
    """
    return x + 10

print somefunc(2)
