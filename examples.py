import random

from workflows import workflow
from workflows.features import *

@workflow
def fib(n):
    # unless is opposite of when.
    yield when(n == 0, returns(0))
    yield when(n == 1, returns(1))
    yield returns(fib(n-1) + fib(n-2))

print fib(10)


@workflow
def sums(*args):
    for arg in args:
        yield fold(lambda x: x+arg)

print sums(2, 4, 8, 16, 32)


@workflow
def sum_and_product(*args):
    for arg in args:
        yield fold(lambda x: x*arg, initial=1, name='product')
        yield fold(lambda x: x+arg, name='sum')

print sum_and_product(2, 4, 8, 16, 32)


@workflow
def x_dot_y(cfg):
    x = yield read_or(lambda: cfg['x'], do(log, 'X is missing'), returns(None))
    x, y = yield read_or(lambda: [cfg['x'], cfg['y']], returns())
    
    print x, y


@workflow
def register_users(users):
    @excepts(Exception)
    def collect_exception(exception):
        yield append(str(exception), name='errors')
    
    @allways
    def write_log(state):
        logger.log(state.get('errors', []), state.get('successes', []))

    yield collect_exception
    yield write_log

    for user in loop(users, collect_exception):
        if user.is_registered is True:
            yield append('Person is already registered', name='errors')
        else:
            user.register()
            yield append('Person was registered', name='successes')
