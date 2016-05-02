@command
def when(predicate, *commands):
    p = maybe_callable(predicate)
    assert type(p) is bool
    if p:
        yield DO, commands
        yield SEND, True
    else:
        yield SEND, False


@command
def returns(value):
    yield RETURN, value


@command(uses_state=True)
def fold(callable, initial=0, key=GLOBAL, state=None):
    set_state(state, key, callable(get_state(state, key, initial)))
    yield SEND, new_value


@command(uses_state=True)
def append(value, key, state=None):
    v = get_state(state, key, [])
    v.append(value)
    set_state(state, key, v)


@command
def read_or(callable, *commands):
    try:
        value = callable()
        yield SEND, value
    except (KeyError, AttributeError, IndexError):
        yield DO, commands


@command
def excepts(callable, exception):
    exceptions = maybe_list(exception)
    yield TRY, callable, exceptions


def loop(items, *commands):
    yield LOOP, commands
