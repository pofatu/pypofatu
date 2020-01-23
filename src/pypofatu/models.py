import attr
from clldutils.misc import slug

from pypofatu import errata
from pypofatu.util import *

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


@attr.s
class Artefact(object):
    """
    An artefact, i.e. a piece in an archeological collection, from which samples might be derived
    destructively or non-destructively.
    """
    id = attr.ib()
    name = attr.ib()
    category = attr.ib(
        converter=lambda s: convert_string({
            'OVEN STONE': 'OVENSTONE',
            'fLAKE': 'FLAKE',
        }.get(s, s)),
        validator=attr.validators.optional(attr.validators.in_([
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
        ]))
    )
    attributes = attr.ib(
        converter=convert_string,
        validator=attr.validators.optional(attr.validators.in_([
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
        ]))
    )
    comment = attr.ib()
    source_ids = attr.ib(converter=errata.source_ids)
    collector = attr.ib()
    collection_type = attr.ib()
    fieldwork_date = attr.ib()
    collection_location = attr.ib()
    collection_comment = attr.ib()


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
        validator=attr.validators.optional(attr.validators.in_([
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
        ]))
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
    loc1 = attr.ib()
    loc2 = attr.ib()
    loc3 = attr.ib()
    comment = attr.ib()
    latitude = attr.ib(converter=almost_float)
    longitude = attr.ib(converter=almost_float)
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


@attr.s
class Sample(object):  # translates to Value, attached to a valueset defined by Location, Parameter and Contribution!
    # Aggregate typed valueset references? Each value needs references, too!
    id = attr.ib()
    category = attr.ib(
        converter=lambda s: s.upper(),
        validator=attr.validators.in_([
            '',
            'SOURCE',
            'ARTEFACT',
            'ARTEFACT USED AS SOURCE',
        ]))  # Two parameters! correspond to the two views!
    comment = attr.ib()
    location = attr.ib()
    petrography = attr.ib()
    source_id = attr.ib(converter=errata.source_id)
    analyzed_material_1 = attr.ib(
        converter=convert_string,
        validator=attr.validators.optional(attr.validators.in_([
            'Whole rock',
            'Fused disk',
            'Volcanic glass',
            'Mineral',
        ]))
    )
    analyzed_material_2 = attr.ib(
        converter=convert_string,
        validator=attr.validators.optional(attr.validators.in_([
            'Core sample',
            'Sample surface',
            'Powder',
        ]))
    )
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
