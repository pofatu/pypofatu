import itertools

from clldutils import text

CITATION_KEYS = {
    'Weisler 1993 Phd': 'weisler1993',
}


def source_id(c):
    return CITATION_KEYS.get(c, c)


def source_ids(s):
    if isinstance(s, str):
        for k, v in CITATION_KEYS.items():
            s = s.replace(k, v)
    if not isinstance(s, (list, tuple, set)):
        s = text.split_text(s or '', ',;', strip=True)
    return [source_id(ss) for ss in itertools.chain(*[source_id(t).split() for t in s]) if ss]
