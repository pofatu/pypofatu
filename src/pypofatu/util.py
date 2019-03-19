import functools


def callcount(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.callcount += 1
        return func(*args, **kwargs)
    wrapper.callcount = 0
    return wrapper
