"""
While errors in the data should typically be fixed upstream, i.e. in the data repository, some
fixing can be done programmatically, when creating distribution formats of the data.
"""
import itertools

from clldutils import text

CITATION_KEYS = {
    'Weisler 1993 Phd': 'weisler1993',
}


def source_id(c: str) -> str:
    """Map known, incorrect citation keys."""
    return CITATION_KEYS.get(c, c)


def source_ids(s) -> list[str]:
    """Replace known, incorrect citation keys."""
    if isinstance(s, str):
        for k, v in CITATION_KEYS.items():
            s = s.replace(k, v)
    if not isinstance(s, (list, tuple, set)):
        s = text.split_text(s or '', ',;', strip=True)
    return [source_id(ss) for ss in itertools.chain(*[source_id(t).split() for t in s]) if ss]
