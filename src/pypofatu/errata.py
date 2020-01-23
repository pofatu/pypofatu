from clldutils import text

KEYS_IN_BIB = {
    'Maxwell-2017-HNZPT': 'Hoffmann-2017-HNZPT',
    'Ishimura-2007-JSS': 'Ishimura-2006-JSS',
}

CITATION_KEYS = {
    'Maxwell-2017-JICA': 'Maxwell-2018-JICA',
    'McCoy-1993-Kahoolawe': 'McCoy-1993-Puumoiwi',
    'Hunt-1998-JPS': 'Hunt-1988-JPS',
    'Walter-1990-Phd': 'Walter-1990-PhD',
    'Frankhauser-2009-Fiji': 'Clark-2009-Fiji',
    'Hermann-2013-Phd': 'Hermann-2013-PHD',
    'McAlister-2017-PLOS': 'McAlister-2017-PO',
    'Ishimura-2007-JSS': 'Ishimura-2006-JSS',
    'Anderson 1981a': 'Anderson-1981-JRSNZ',
    'Barber & Walter 2002': 'Barber-2002-ANZ',
    'Gay 2004': 'Gay-2004-BA',
    'Weisler 1993 Phd': 'Weisler-1993-Phd',
    'Simpson-2018-JASr': 'Simpson-2018-JASR',
    'Metraux-1940-ETHNOLOGY': 'Metraux-1940-Easter',
    'Metraux-1940-Ethnology': 'Metraux-1940-Easter',
    'McAlister-2017-PLOSONE': 'McAlister-2017-PO',
    'Collerson-2007-SCIENCE': 'Collerson-2007-Science',
    'Johnson-2011-TUTUILA': 'Johnson-2011-Tutuila',
}

SAMPLE_NAMES = {
    'Hakaea-#3': 'HAKAEA-3',
    'Hakaea-#4': 'HAKAEA-4',
    'Hakaea-#5': 'HAKAEA-5',
    'Hakaea-adze': 'HAKAEA-ADZE',
    'Hakaea-preform': 'HAKAEA-PREFORM',
    'Hatiheu-preform': 'HATIHEU-PREFORM',
    'Nani-2': 'NANI-2',
    'Nani-3': 'NANI-3',
    ('Sinton-1997-Database', 'AN-21'): 'AN21'
}

SAMPLE_IDS = {
    'Golitko-2013-Sepik_WNB257/ANU9000': 'Golitko-2013-Sepik_WNB257',
}


def sample_name(c, sid):
    if (sid, c) in SAMPLE_NAMES:
        return SAMPLE_NAMES[(sid, c)]
    return SAMPLE_NAMES.get(c, c)


def source_id(c):
    return CITATION_KEYS.get(c, c)


def source_ids(s):
    if not isinstance(s, (list, tuple, set)):
        s = text.split_text(s or '', ',;', strip=True)
    return [source_id(ss) for ss in s]
