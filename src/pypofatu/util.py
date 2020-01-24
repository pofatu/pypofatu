import functools
import collections

import attr

__all__ = [
    'callcount', 'semicolon_split', 'almost_float', 'almost_int', 'parse_value', 'convert_string']


def convert_string(s):
    if s in [
        'NA',
        '',
        '42',  # That's what excel's "#N/A" comes out as!
    ]:
        return None
    return s


@attr.s
class Row(object):
    index = attr.ib()
    keys = attr.ib()
    values = attr.ib()

    @property
    def dict(self):
        return collections.OrderedDict(zip(self.keys[1], self.values))


def callcount(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.callcount += 1
        return func(*args, **kwargs)
    wrapper.callcount = 0
    return wrapper


def almost_int(f):
    if isinstance(f, str):
        if not f:
            return None
        f = float(f)
        assert f.is_integer()
        f = int(f)
    return f


def almost_float(f):
    if isinstance(f, str):
        if f in ['NA', '*']:
            return None
        if f.endswith(','):
            f = f[:-1]
        if not f:
            return
    elif f is None:
        return None
    return float(f)


def parse_value(v):
    less = False
    if isinstance(v, str):
        v = v.replace('−', '-')
        if v.strip().startswith('<') or v.startswith('≤'):
            v = v.strip()[1:].strip()
            less = True
    if v not in [
        None,
        '',
        'nd',
        'bdl',
        'LOD',
        '-',
        'n.d.',
    ]:
        return float(v), less
    return None, less


def semicolon_split(c):
    if not c:
        return []
    return [n.strip() for n in c.split(';') if n.strip()]
