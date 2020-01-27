import re

import attr
from clldutils.misc import slug

from pypofatu import errata
from pypofatu.util import *  # noqa: F403

__all__ = [
    'Contribution', 'Artefact', 'Measurement', 'Method', 'Site', 'Sample', 'Analysis', 'Location',
    'MethodReference']


@attr.s
class Contribution(object):
    """
    A set of samples contributed to Pofatu, possibly aggregated from multiple sources.
    """
    id = attr.ib(converter=errata.source_id)
    name = attr.ib()
    description = attr.ib()
    authors = attr.ib()
    affiliation = attr.ib()
    contact_email = attr.ib()
    contributors = attr.ib(converter=semicolon_split)
    source_ids = attr.ib(converter=errata.source_ids)

    @property
    def label(self):
        return '{0.name} ({0.id})'.format(self)


ARTEFACT_CATEGORY = [
    'ADZE',
    'ADZE BUTT',
    'ADZE FLAKE',
    'ADZE PREFORM',
    'ADZE ADZE PREFORM',
    'CHISEL',
    'COBBLE',
    'COBBLE (KILIKILI)',
    'CORE',
    'FLAKE',
    'FLAKE (ADZE BLANK)',
    'FLAKE (ADZE KNAPPING)',
    'FLAKE (DEBITAGE)',
    'FLAKE (RETOUCHED)',
    'RAW MATERIAL',
    'ARCHITECTURAL',
    'GRINDSTONE',
    'OVENSTONE',
    'HAMMERSTONE',
    'NATURAL PEBBLE',
    'ABRADER',
    'PAVING STONE',
    'FLAKE TOOL',
    'PICK',
    # Errors:
    'NATURAL DYKE',  # Wrong column!
]

ARTEFACT_ATTRIBUTES = [
    'COMPLETE',
    'FRAGMENT',
    'FRAGMENT (PROXIMAL)',
    'FRAGMENT (MESIAL)',
    'FRAGMENT (DISTAL)',
    'NATURAL DYKE',
    'NATURAL BOULDER/COBBLE',
    'NATURAL PRISM',
    # Errors?:
    'Blade',
    'Blade+mid',
]

ARTEFACT_COLLECTION_TYPE = [
    'SURVEY',
    'EXCAVATION',
]


@attr.s
class Artefact(object):
    """
    An artefact, i.e. a piece in an archeological collection, from which samples might be derived
    destructively or non-destructively.
    """
    id = attr.ib()
    name = attr.ib()
    category = attr.ib(
        converter=lambda s: convert_string({'OVEN STONE': 'OVENSTONE', 'fLAKE': 'FLAKE'}.get(s, s)),
        validator=attr.validators.optional(attr.validators.in_(ARTEFACT_CATEGORY)),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in ARTEFACT_CATEGORY)}},
    )
    attributes = attr.ib(
        converter=convert_string,
        validator=attr.validators.optional(attr.validators.in_(ARTEFACT_ATTRIBUTES)),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in ARTEFACT_ATTRIBUTES)}},
    )
    comment = attr.ib()
    source_ids = attr.ib(converter=errata.source_ids)
    collector = attr.ib()
    collection_type = attr.ib(
        converter=lambda s: s.upper() if s else None,
        validator=attr.validators.optional(attr.validators.in_(ARTEFACT_COLLECTION_TYPE)),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in ARTEFACT_COLLECTION_TYPE)}},
    )
    fieldwork_date = attr.ib()
    collection_location = attr.ib()
    collection_comment = attr.ib()


SITE_CONTEXT = [
    'DOMESTIC',
    'QUARRY',
    'CEREMONIAL',
    'WORKSHOP',
    'NATURAL',
    'AGRICULTURAL',
    'ROCKSHELTER',
    'MIDDEN',
    'FUNERAL',
    'DEFENSIVE',
]


@attr.s
class Site(object):
    """
    An archeological site from which artefacts have be collected.
    """
    name = attr.ib(converter=convert_string)
    code = attr.ib()
    source_ids = attr.ib(converter=errata.source_ids)

    context = attr.ib(
        converter=convert_string,
        validator=attr.validators.optional(attr.validators.in_(SITE_CONTEXT)),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in SITE_CONTEXT)}},
    )
    comment = attr.ib()
    stratigraphic_position = attr.ib()
    stratigraphy_comment = attr.ib()

    @property
    def id(self):
        return slug(self.label, lowercase=False)

    @property
    def label(self):
        return '{0} {1} {2}'.format(
            ' '.join(self.source_ids), self.name or '', self.code or '').strip()


@attr.s
class MethodReference(object):
    sample_name = attr.ib()
    sample_measured_value = attr.ib()
    uncertainty = attr.ib()
    uncertainty_unit = attr.ib()
    number_of_measurements = attr.ib()

    def as_string(self):
        res = self.sample_name
        if self.sample_measured_value:
            if res:
                res += ': '
            res += self.sample_measured_value
        return res


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
    detection_limit = attr.ib()
    detection_limit_unit = attr.ib()
    total_procedural_blank_value = attr.ib()
    total_procedural_unit = attr.ib()
    references = attr.ib(default=attr.Factory(list))

    @property
    def label(self):
        res = '{0.code} {0.parameter}'.format(self)
        return res

    @property
    def id(self):
        return '{0}_{1}'.format(slug(self.code), slug(self.parameter))


@attr.s
class Location(object):  # translates to Language.
    loc1 = attr.ib(metadata={'titles': 'region'})
    loc2 = attr.ib(metadata={'titles': 'subregion'})
    loc3 = attr.ib()
    comment = attr.ib()
    latitude = attr.ib(
        converter=almost_float,
        validator=attr.validators.optional(attr.validators.instance_of(float)),
        metadata={'datatype': {'base': 'decimal', 'maximum': 90, 'minimum': -90}}
    )
    longitude = attr.ib(
        converter=almost_float,
        validator=attr.validators.optional(attr.validators.instance_of(float)),
        metadata={'datatype': {'base': 'decimal', 'maximum': 180, 'minimum': -180}}
    )
    elevation = attr.ib(converter=lambda s: None if s == 'NA' else s)

    @property
    def id(self):
        return slug(self.label)

    @property
    def label(self):
        return ' / '.join([c for c in [self.loc1, self.loc2, self.loc3] if c])

    @property
    def name(self):
        res = ' / '.join([c for c in [self.loc1, self.loc2, self.loc3, self.comment] if c])
        if self.latitude is not None and self.longitude is not None:
            res += ' ({0:.4f}, {1:.4f}, {2})'.format(
                self.latitude, self.longitude, self.elevation or '-')
        return res


SAMPLE_CATEGORY = [
    'SOURCE',
    'ARTEFACT',
    'ARTEFACT USED AS SOURCE',
]

ANALYZED_MATERIAL_1 = [
    'Whole rock',
    'Fused disk',
    'Volcanic glass',
    'Mineral',
]

ANALYZED_MATERIAL_2 = [
    'Core sample',
    'Sample surface',
    'Powder',
]


@attr.s
class Sample(object):
    id = attr.ib()
    category = attr.ib(
        converter=lambda s: s.upper() if s else None,
        validator=attr.validators.optional(attr.validators.in_(SAMPLE_CATEGORY)),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in SAMPLE_CATEGORY)}},
    )
    comment = attr.ib()
    petrography = attr.ib()
    source_id = attr.ib(converter=errata.source_id)
    analyzed_material_1 = attr.ib(
        converter=convert_string,
        validator=attr.validators.optional(attr.validators.in_(ANALYZED_MATERIAL_1)),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in ANALYZED_MATERIAL_1)}},
    )
    analyzed_material_2 = attr.ib(
        converter=convert_string,
        validator=attr.validators.optional(attr.validators.in_(ANALYZED_MATERIAL_2)),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in ANALYZED_MATERIAL_2)}},
    )
    location = attr.ib()
    artefact = attr.ib()
    site = attr.ib()


@attr.s
class Analysis(object):
    id = attr.ib()
    sample = attr.ib(default=None)
    measurements = attr.ib(default=attr.Factory(list))


@attr.s
class Measurement(object):
    method = attr.ib()
    parameter = attr.ib()
    value = attr.ib(
        converter=float,
        validator=attr.validators.instance_of(float),
        metadata={'datatype': 'decimal'},
    )
    less = attr.ib(
        validator=attr.validators.instance_of(bool),
        metadata={'datatype': {'base': 'boolean', 'format': 'yes|no'}},
    )
    precision = attr.ib(
        converter=almost_float,
        validator=attr.validators.optional(attr.validators.instance_of(float)),
        metadata={'datatype': 'decimal'},
    )
    sigma = attr.ib(
        converter=lambda s: int(s.replace('σ', '')) if s else None,
        validator=attr.validators.optional(attr.validators.in_([1, 2])),
        metadata={'datatype': {'base': 'integer', 'minimum': 1, 'maximum': 2}},
    )

    def as_string(self):
        res = '{0}{1}'.format('\u2264' if self.less else '', self.value)
        if self.precision:
            res += '±{0}'.format(self.precision)
        if self.sigma:
            res += '{0}σ'.format(self.sigma)
        return res
