import attr

from pypofatu import errata

__all__ = [
    'Contribution', 'Artefact', 'Reference', 'Measurement', 'Method', 'Site', 'Sample', 'Analysis',
    'Location', 'MethodReference', 'source_id', 'sample_name',
]


def semicolon_split(c):
    if not c:
        return []
    return [n.strip() for n in c.split(';') if n.strip()]


def source_id(c):
    return errata.CITATION_KEYS.get(c, c)


@attr.s
class Contribution(object):
    id = attr.ib(converter=source_id)
    name = attr.ib()
    description = attr.ib()
    authors = attr.ib()
    contributors = attr.ib(converter=semicolon_split)

    @property
    def label(self):
        return '{0.name} ({0.id})'.format(self)


def sample_name(c, sid):
    if (sid, c) in errata.SAMPLE_NAMES:
        return errata.SAMPLE_NAMES[(sid, c)]
    return errata.SAMPLE_NAMES.get(c, c)


@attr.s
class Reference(object):
    id = attr.ib(converter=source_id)
    reference = attr.ib()
    doi = attr.ib()


@attr.s
class Artefact(object):
    id = attr.ib()
    name = attr.ib()
    category = attr.ib()
    attributes = attr.ib()
    comment = attr.ib()
    source_ids = attr.ib(converter=semicolon_split)
    collection_type = attr.ib()


@attr.s
class Site(object):  # new resource type, like villages in dogonlanguages!
    name = attr.ib()
    code = attr.ib()
    context = attr.ib()
    comment = attr.ib()
    stratigraphic_position = attr.ib()
    source_ids = attr.ib(converter=semicolon_split)


@attr.s
class MethodReference(object):
    sample_name = attr.ib()
    sample_measured_value = attr.ib()
    uncertainty = attr.ib()
    uncertainty_unit = attr.ib()


@attr.s
class Method(object):
    code = attr.ib()
    parameter = attr.ib()
    technique = attr.ib()
    instrument = attr.ib()
    laboratory = attr.ib()
    analyst = attr.ib()
    date = attr.ib()
    comment = attr.ib()
    references = attr.ib()

    @property
    def label(self):
        res = '{0.code} {0.parameter}'.format(self)
        return res

    @property
    def uid(self):
        return self.label.lower()


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


@attr.s
class Location(object):  # translates to Language.
    loc1 = attr.ib()
    loc2 = attr.ib()
    loc3 = attr.ib()
    comment = attr.ib()
    latitude = attr.ib(converter=almost_float)
    longitude = attr.ib(converter=almost_float)
    elevation = attr.ib(converter=lambda s: None if s == 'NA' else s)

    @property
    def name(self):
        res = ' / '.join([c for c in [self.loc1, self.loc2, self.loc3, self.comment] if c])
        if self.latitude is not None and self.longitude is not None:
            res += ' ({0:.4f}, {1:.4f}, {2})'.format(
                self.latitude, self.longitude, self.elevation or '-')
        return res


@attr.s
class Sample(object):  # translates to Value, attached to a valueset defined by Location, Parameter and Contribution!
    # Aggregate typed valueset references? Each value needs references, too!
    id = attr.ib()
    category = attr.ib(
        converter=lambda s: '' if s == '*' else s.upper(),
        validator=attr.validators.in_([
            '',
            'SOURCE',
            'ARTEFACT',
            'ARTEFACT USED AS SOURCE',
        ]))  # Two parameters! correspond to the two views!
    comment = attr.ib()
    location = attr.ib()
    petrography = attr.ib()
    source_id = attr.ib()
    analyzed_material = attr.ib()

    artefact = attr.ib()
    site = attr.ib()


@attr.s
class Analysis(object):
    id = attr.ib()
    method = attr.ib(default=None)
    sample = attr.ib(default=None)
    measurements = attr.ib(default=attr.Factory(list))


@attr.s
class Measurement(object):
    parameter = attr.ib()
    value = attr.ib(converter=float)
    less = attr.ib()
    precision = attr.ib(converter=lambda s: float(s) if s else None)
    sigma = attr.ib(
        converter=lambda s: int(s.replace('σ', '')) if s else None,
        validator=attr.validators.optional(attr.validators.in_([1, 2]))
    )

    def as_string(self):
        res = '{0}{1}'.format('\u2264' if self.less else '', self.value)
        if self.precision:
            res += '±{0}'.format(self.precision)
        if self.sigma:
            res += '{0}σ'.format(self.sigma)
        return res

    @property
    def method_uid(self):
        return '{0} {1}'.format(self.analysis_id, self.parameter.split()[0]).lower()
