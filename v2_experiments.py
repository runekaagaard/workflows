from collections import namedtuple


class InvalidArrowException(Exception):
    pass


def run_workflow(func, args, state, error_step=None):
    ARROWS = namedtuple('ARROWS', 'continues aborts')("_continues_",
                                                      "_aborts_")
    for step in func(args):
        try:
            state, arrow = step(state, ARROWS)
            if isinstance(arrow, Exception):
                setattr(arrow, 'state', state)
                raise arrow
        except Exception as exception:
            if error_step is None:
                raise
            else:
                state, arrow = error_step(exception, state, ARROWS)

        if arrow == ARROWS.continues:
            continue
        elif arrow == ARROWS.aborts:
            return state
        else:
            raise InvalidArrowException()

    return state


def reduces(reducer):
    return lambda state, arrows: (reducer(state), arrows.continues)


def aborts():
    return lambda state, arrows: (state, arrows.aborts)


def sums(xs):
    for x in xs:
        if x > 12:
            yield aborts()
        yield reduces(lambda state: state + x)


print run_workflow(sums, range(20), 0)
