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


def mark_takes_no_arguments(func):
    func.takes_no_arguments = True
    return func


def takes_no_arguments(func):
    mark_takes_no_arguments(func)
    return func


def contract(pre_conditions, post_conditions):
    """
    Pre is before. Post is after.
    """

    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            parse_conditions(
                pre_conditions, args, kwargs, title='Preconditions')
            result = func(*args, **kwargs)
            parse_conditions(
                post_conditions, [result], {}, title='Postconditions')
            return result

        return __

    return _


def processing(pre_process, post_process):
    "Procemanns"

    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            args, kwargs = pre_process(*args, **kwargs)
            return post_process(func(*args, **kwargs))

        return __

    return _


@takes_no_arguments
def add_one(func):
    @wraps(func)
    def _(*args, **kwargs):
        return func(*args, **kwargs) + 1

    return _


def compose(*workflows):
    def extract_kwargs(workflow, kwargs):
        return {x: kwargs[x] for x in inspect.getargspec(workflow).args}

    def _(*args, **kwargs):
        assert len(args) == 0, "Only keywords allowed."

        def __(func):
            @wraps(func)
            def ___(*a, **k):
                return func(*a, **k)

            for workflow in reversed(workflows):
                if hasattr(workflow, 'takes_no_arguments'):
                    ___ = workflow(___)
                else:
                    ___ = workflow(**extract_kwargs(workflow, kwargs))(___)
                ___.__doc__ += workflow.__doc__ or ""

            return ___

        return __

    return _


someworkflow = compose(contract, processing, add_one)
print someworkflow


@someworkflow(
    pre_conditions=[lambda x: x == 2],
    post_conditions=lambda r: r == 15,
    pre_process=lambda x: ([x + 1], {}),
    post_process=lambda x: x + 1, )
def somefunc(x):
    """
    Very important: x must be 2!
    """
    return x + 10


print somefunc(2)
help(somefunc)
