"""
Data model.
"""
import re
import statistics

import attr
from clldutils.misc import slug

from pypofatu import errata
from pypofatu.util import semicolon_split, convert_string, almost_float, fix_excel_ints

__all__ = [
    'Contribution', 'Artefact', 'Measurement', 'Method', 'Site', 'Sample', 'Analysis', 'Location',
    'MethodReference', 'MethodNormalization', 'Parameter', 'FractionationCorrection']

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
    'Probe sample',
]


@attr.s
class Contribution:  # pylint: disable=R0902,R0903
    """
    A set of samples contributed to Pofatu, possibly aggregated from multiple sources.
    """
    id = attr.ib(converter=errata.source_id, validator=attr.validators.matches_re('.+'))
    name = attr.ib(validator=attr.validators.matches_re('.+'))
    description = attr.ib()
    authors = attr.ib()
    affiliation = attr.ib()
    contact_email = attr.ib()
    contributors = attr.ib(converter=semicolon_split)
    source_ids = attr.ib(converter=errata.source_ids)

    @property
    def label(self) -> str:  # pylint: disable=C0116
        return f'{self.name} ({self.id})'


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
    'GEOLOGICAL',
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
    'RETOUCHED FLAKE',
    'SHATTER',
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
    'MAKATEA',
    'TAKAROA',
    'RANGIROA',
    'MAROKAU',
]

ARTEFACT_COLLECTION_TYPE = [
    'SURVEY',
    'EXCAVATION',
    'UNKNOWN',
]


@attr.s
class Artefact:  # pylint: disable=R0902,R0903
    """
    An artefact, i.e. a piece in an archeological collection, from which samples might be derived
    destructively or non-destructively.
    """
    id = attr.ib(validator=attr.validators.matches_re('.+'))
    name = attr.ib()
    category = attr.ib(
        converter=lambda s: convert_string(
            {'OVEN STONE': 'OVENSTONE', 'fLAKE': 'FLAKE', 'abrader': 'ABRADER'}.get(s, s)),
        validator=attr.validators.optional(attr.validators.in_(ARTEFACT_CATEGORY)),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in ARTEFACT_CATEGORY)}},
    )
    attributes = attr.ib(
        converter=lambda s: convert_string(
            {'FRAGMENT (FRAGMENT (DISTAL))': 'FRAGMENT (DISTAL)'}.get(s, s)),
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
    'BURIAL',
    'UNDERWATER',
]


@attr.s
class Site:
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
    def id(self):  # pylint: disable=C0116
        return slug(self.label, lowercase=False)

    @property
    def label(self):  # pylint: disable=C0116
        return f"{' '.join(self.source_ids)} {self.name or ''} {self.code or ''}".strip()


@attr.s
class MethodReference:  # pylint: disable=R0903
    """Reference metadata."""
    sample_name = attr.ib()
    sample_measured_value = attr.ib()
    uncertainty = attr.ib()
    uncertainty_unit = attr.ib()
    number_of_measurements = attr.ib()

    def as_string(self):  # pylint: disable=C0116
        res = self.sample_name
        if self.sample_measured_value:
            if res:
                res += ': '
            res += self.sample_measured_value
        return res


@attr.s
class MethodNormalization:  # pylint: disable=R0903
    """Metadata about normalization via reference samples."""
    reference_sample_name = attr.ib()
    reference_sample_accepted_value = attr.ib()
    citation = attr.ib()


@attr.s
class FractionationCorrection:  # pylint: disable=R0903
    """Fractionation correction settings - currently not reported."""
    parameter = attr.ib()
    reference_sample_name = attr.ib()
    sample_value = attr.ib()
    sample_accepted_value = attr.ib()
    citation = attr.ib()


@attr.s
class Method:  # pylint: disable=R0902
    """Metadata of an analysis method."""
    code = attr.ib(validator=attr.validators.matches_re('.+'))
    parameter = attr.ib(validator=attr.validators.matches_re('.+'))  # specific

    analyzed_material_1 = attr.ib(
        converter=lambda s: (convert_string(s) or '').capitalize() or None,
        validator=attr.validators.optional(attr.validators.in_(ANALYZED_MATERIAL_1)),
        metadata={
            '_parameter_specific': False,
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in ANALYZED_MATERIAL_1)}},
    )
    analyzed_material_2 = attr.ib(
        converter=lambda s: (convert_string(s) or '').capitalize() or None,
        validator=attr.validators.optional(attr.validators.in_(ANALYZED_MATERIAL_2)),
        metadata={
            '_parameter_specific': False,
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in ANALYZED_MATERIAL_2)}},
    )
    sample_preparation = attr.ib(metadata={'_parameter_specific': False})
    chemical_treatment = attr.ib(metadata={'_parameter_specific': False})
    technique = attr.ib(metadata={'_parameter_specific': False})
    laboratory = attr.ib(metadata={'_parameter_specific': False})
    analyst = attr.ib(metadata={'_parameter_specific': False})

    number_of_replicates = attr.ib()
    instrument = attr.ib()  # specific
    date = attr.ib()  # specific
    comment = attr.ib()  # specific
    detection_limit = attr.ib()  # specific
    detection_limit_unit = attr.ib()  # specific
    total_procedural_blank_value = attr.ib()  # specific
    total_procedural_unit = attr.ib()  # specific
    references = attr.ib(default=attr.Factory(list))  # specific
    normalizations = attr.ib(default=attr.Factory(list))
    fractionation_correction = attr.ib(default=None)

    @property
    def label(self) -> str:  # pylint: disable=C0116
        return f'{self.code} {self.parameter}'

    @property
    def id(self) -> str:  # pylint: disable=C0116
        return f'{slug(self.code)}_{slug(self.parameter)}'


@attr.s
class Location:  # translates to Language.
    """A location, identified by a geographic coordinate and some metadata."""
    region = attr.ib()
    subregion = attr.ib()
    locality = attr.ib()
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
    def id(self) -> str:
        """An identifier for the location."""
        return slug(self.label)

    @property
    def label(self) -> str:
        """A short name for the loation."""
        return ' / '.join([c for c in [self.region, self.subregion, self.locality] if c])

    @property
    def name(self) -> str:
        """A name for the location."""
        res = ' / '.join(
            [c for c in [self.region, self.subregion, self.locality, self.comment] if c])
        if self.latitude is not None and self.longitude is not None:
            res += f' ({self.latitude:.4f}, {self.longitude:.4f}, {self.elevation or "-"})'
        return res


SAMPLE_CATEGORY = [
    'SOURCE',
    'ARTEFACT',
    'ARTEFACT USED AS SOURCE',
]


@attr.s
class Sample:  # pylint: disable=R0903,R0902
    """A sample, on which chemical analyses have been performed."""
    id = attr.ib(
        validator=attr.validators.matches_re(r"[a-zA-Z0-9_\-'/(). ]+"),
        converter=lambda s: s.replace(chr(8208), '-'),
    )
    sample_name = attr.ib(
        converter=fix_excel_ints,
        validator=attr.validators.matches_re('.+'),
    )
    sample_category = attr.ib(
        converter=lambda s: s.upper() if s else None,
        validator=attr.validators.in_(SAMPLE_CATEGORY),
        metadata={
            'datatype': {
                'base': 'string',
                'format': '|'.join(re.escape(c) for c in SAMPLE_CATEGORY)}},
    )
    sample_comment = attr.ib()
    petrography = attr.ib()
    source_id = attr.ib(
        converter=errata.source_id,
        validator=attr.validators.matches_re('.+'),
    )
    location = attr.ib()
    artefact = attr.ib()
    site = attr.ib()


@attr.s
class Analysis:  # pylint: disable=R0903
    """Results of an analysis of a sample."""
    id = attr.ib(validator=attr.validators.matches_re('.+'))
    sample = attr.ib(default=None)
    measurements = attr.ib(default=attr.Factory(list))


@attr.s
class Measurement:  # pylint: disable=R0903
    """Result of measuring a parameter using a method."""
    method = attr.ib()
    parameter = attr.ib(validator=attr.validators.matches_re('.+'))
    value = attr.ib(
        converter=float,
        validator=attr.validators.instance_of(float),
        metadata={'datatype': 'decimal'},
    )
    less = attr.ib(
        validator=attr.validators.instance_of(bool),
        metadata={'datatype': {'base': 'boolean', 'format': 'yes|no'}},
    )
    value_sd = attr.ib(
        converter=almost_float,
        validator=attr.validators.optional(attr.validators.instance_of(float)),
        metadata={'datatype': 'float'},
    )
    sd_sigma = attr.ib(
        converter=lambda s: int(s.replace('σ', '').replace('sigma', '')) if s else None,
        validator=attr.validators.optional(attr.validators.in_([1, 2])),
        metadata={'datatype': {'base': 'integer', 'minimum': 1, 'maximum': 2}},
    )

    def as_string(self) -> str:
        """String representation of a measurement including accuracy."""
        res = ('\u2264' if self.less else '') + str(self.value)
        if self.value_sd:
            res += f'±{self.value_sd}'
        if self.sd_sigma:
            res += f' {self.sd_sigma}σ'
        return res


@attr.s
class Parameter:  # pylint: disable=R0903
    """Summary stats about a parameter and associated measurements."""
    name = attr.ib(validator=attr.validators.matches_re('.+'))
    min = attr.ib(validator=attr.validators.instance_of(float))
    max = attr.ib(validator=attr.validators.instance_of(float))
    mean = attr.ib(validator=attr.validators.instance_of(float))
    median = attr.ib(validator=attr.validators.instance_of(float))
    count_analyses = attr.ib(validator=attr.validators.instance_of(int))

    @classmethod
    def from_values(cls, name: str, vals: list[float]) -> 'Parameter':
        """Initialize a parameter from measured values."""
        return cls(
            name=name,
            min=min(vals),
            max=max(vals),
            mean=statistics.mean(vals),
            median=statistics.median(vals),
            count_analyses=len(vals),
        )
