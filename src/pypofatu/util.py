import functools

from pybtex.database import parse_string
import requests
from clldutils.source import Source


def callcount(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.callcount += 1
        return func(*args, **kwargs)
    wrapper.callcount = 0
    return wrapper


def doi2source(doi):
    if not doi.startswith('http'):
        doi = 'https://doi.org/' + doi
    bibtex = requests.get(
        doi, headers={'Accept': 'text/bibliography; style=bibtex'}).content.decode('utf8')
    try:
        return Source.from_entry(*list(parse_string(bibtex, 'bibtex').entries.items())[0])
    except IndexError:
        return
