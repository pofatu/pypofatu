"""
Utilities
"""
import functools
from typing import Union, Callable

__all__ = [
    'callcount', 'semicolon_split', 'almost_float', 'parse_value', 'convert_string',
    'fix_excel_ints']


def fix_excel_ints(s: str) -> str:
    """
    Fix ints exported as floats from excel.

    >>> fix_excel_ints('1.00')
    '1'
    """
    try:
        n = float(s)
        if n.is_integer():
            return str(int(n))
        return s
    except ValueError:
        return s


def convert_string(s: Union[None, str]) -> Union[str, None]:
    """Convert a string to None, if it represents a null value."""
    if s in [
        None,
        'NA',
        '',
        '*',
        '42',  # That's what excel's "#N/A" comes out as!
    ]:
        return None
    return s


def callcount(func: Callable) -> Callable:
    """Adds a counter for invocations to a callable."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.callcount += 1
        return func(*args, **kwargs)
    wrapper.callcount = 0
    return wrapper


def almost_float(f) -> Union[None, float]:
    """Converts a string to a float - or None if that fails."""
    if f is None:
        return None
    if isinstance(f, str):
        if f in ['NA', '*']:
            return None
        if f.endswith(','):
            f = f[:-1]
        if not f:
            return None
    return float(f)


def parse_value(v) -> tuple[Union[float, None], bool]:
    """Parse a value into a float and a bool signaling whether a less-than operator is prefixed."""
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


def semicolon_split(c: str) -> list[str]:
    """Split a string on semicolon."""
    return [n.strip() for n in c.split(';') if n.strip()] if c else []
