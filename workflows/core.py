def maybe_callable(value, args):    
    return value(*args()) if callable(value) else value