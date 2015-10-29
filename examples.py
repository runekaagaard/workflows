import random

from workflows import workflow
from workflows.features import *

@workflow
def fib(n):
    yield case(n == 0, 0)
    yield case(n == 1, lambda: n)
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
        yield fold(lambda x: x*arg, name='product', initial=1)
        yield fold(lambda x: x+arg, name='sum')

print sum_and_product(2, 4, 8, 16, 32)


@workflow
def handle_errors_1():
    yield add_fail_guard(KeyError, 92)
    yield add_fail_guard(AttributeError, lambda state: state)

    yield fold(lambda x: x + 42)
    yield fold(lambda x: x + 42)

    x = {}
    x['foo']
    
print handle_errors_1()


@workflow
def handle_errors_2():
    yield add_fail_guard(KeyError, 92)
    yield add_fail_guard(AttributeError, lambda state: state)

    yield fold(lambda x: x + 42)
    yield fold(lambda x: x + 42)

    x = {}
    x.e
    
print handle_errors_2()


@workflow
def check_existence(cfg):
    x = yield check(cfg.get('x'))
    y = yield check(cfg.get('y'), lambda y: y>50, lambda state: 777)
    yield returns(x+y)

print check_existence({'x': 1111, 'y': 889})


@workflow
def check_existence_2(cfg):
    x = yield check(cfg.get('x'))
    y = yield check(cfg.get('y'), lambda y: y>50, 777)
    yield returns(x+y)

print check_existence_2({'x': 1111, 'y': 889})