import random

from workflows import workflow
from workflows.commands import *

@workflow
def fib(n):
    yield when(n == 0, returns(0))
    yield unless(n != 1, returns(1))
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
        yield fold(lambda x: x*arg, initial=1, key='product')
        yield fold(lambda x: x+arg, key='sum')

print sum_and_product(2, 4, 8, 16, 32)

@workflow
def use_cfg(cfg):
    def log(msg):
        print msg

    x, y = yield read_or(lambda: (cfg['x'], cfg['y']))
    yield returns((x, y))

print use_cfg({'x': 10, 'y': 20})
import sys; sys.exit()


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
