import collections

from clldutils.apilib import API
from clldutils.source import Source
from csvw.dsv import reader, UnicodeWriter
import xlrd
import attr
from pybtex.database import parse_file

from pypofatu import errata
from pypofatu import util


def semicolon_split(c):
    if not c:
        return []
    return [n.strip() for n in c.split(';') if n.strip()]


@attr.s
class Contribution(object):
    id = attr.ib()
    name = attr.ib()
    description = attr.ib()
    authors = attr.ib()
    contributors = attr.ib(converter=semicolon_split)

    @property
    def label(self):
        return '{0.name} ({0.id})'.format(self)


@attr.s
class Reference(object):
    id = attr.ib(converter=lambda c: errata.CITATION_KEYS.get(c, c))
    reference = attr.ib()
    doi = attr.ib()


@attr.s
class Sample(object):
    source_id = attr.ib()


@attr.s
class Artefact(object):
    name = attr.ib()
    description = attr.ib()
    category = attr.ib()
    comment = attr.ib()
    source_ids = attr.ib(converter=semicolon_split)


@attr.s
class Site(object):  # new resource type, like villages in dogonlanguages!
    name = attr.ib()
    context = attr.ib()
    stratigraphic_position = attr.ib()
    comment = attr.ib()
    source_ids = attr.ib(converter=semicolon_split)


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
    ref_sample_name = attr.ib()
    ref_sample_measured_value = attr.ib()
    ref_uncertainty = attr.ib()
    ref_uncertainty_unit = attr.ib()

    @property
    def label(self):
        res = '{0.code} {0.parameter}'.format(self)
        if self.ref_sample_name:
            res += ' {0}'.format(self.ref_sample_name)
        return res


def almost_float(f):
    if isinstance(f, str):
        if f.endswith(','):
            f = f[:-1]
        if not f:
            return
    return float(f)


@attr.s
class Location(object):  # translates to Language.
    loc1 = attr.ib()
    loc2 = attr.ib()
    loc3 = attr.ib()
    comment = attr.ib()
    latitude = attr.ib(converter=almost_float)
    longitude = attr.ib(converter=almost_float)
    elevation = attr.ib()

    @property
    def name(self):
        res = ' / '.join([c for c in [self.loc1, self.loc2, self.loc3, self.comment] if c])
        if self.latitude is not None and self.longitude is not None:
            res += ' ({0:.4f}, {1:.4f}, {2})'.format(
                self.latitude, self.longitude, self.elevation or '-')
        return res


@attr.s
class Datapoint(object):  # translates to Value, attached to a valueset defined by Location, Parameter and Contribution!
    # Aggregate typed valueset references? Each value needs references, too!
    id = attr.ib()
    category = attr.ib(validator=attr.validators.in_(['SOURCE', 'ARTEFACT']))  # Two parameters! correspond to the two views!
    comment = attr.ib()
    location = attr.ib()
    petrography = attr.ib()
    sample = attr.ib(converter=Sample)
    artefact = attr.ib()
    site = attr.ib()
    analyzed_material = attr.ib()
    method_id = attr.ib()
    data = attr.ib()  # maps params to UnitParameter, but provide custom UnitValue class! with float value!

    @property
    def uid(self):
        return '{0.id}-{0.method_id}'.format(self)


class Pofatu(API):
    def _dump_sheets(self):
        wb = xlrd.open_workbook(str(self.repos / 'Pofatu Dataset.xlsx'))
        for name in wb.sheet_names():
            sheet = wb.sheet_by_name(name)
            with UnicodeWriter(self.repos / '{0}.csv'.format(name.replace(' ', '_'))) as writer:
                for i in range(sheet.nrows):
                    writer.writerow([sheet.cell(i, j).value for j in range(sheet.ncols)])

    def iterbib(self):
        for entry in parse_file(str(self.repos / 'POFATU-references.bib')).entries.values():
            yield Source.from_entry(entry.fields['annote'], entry)

    def iterrows(self, name):
        csv_path = self.repos / '{0}.csv'.format(name.replace(' ', '_'))
        if not csv_path.exists():
            self._dump_sheets()

        head = [None, None]
        for i, row in enumerate(reader(csv_path)):
            row = [None if c == 'NA' else c for c in row]
            if i == 2:
                head[0] = row
            if i == 3:
                head[1] = row
            elif i > 4:
                yield i, head, row

    def itermethods(self):
        ids = {}
        for i, head, row in self.iterrows('3 Analytical metadata'):
            m = Method(*row[:12])
            if m.label not in ids:
                yield m
                ids[m.label] = row
            else:
                if ids[m.label] != row:
                    raise ValueError(m.label)

    def itercontributions(self):
        ids = set()
        for i, head, row in self.iterrows('1 Data Source'):
            if row[0] and row[0] not in ids:
                yield Contribution(
                    id=row[0],  # Dataset code
                    name=row[1],  # Title
                    description=row[2],  # Abstract
                    authors=row[3],  # add affilitations from row[4]
                    contributors=row[5],  # add contact from row[6]
                )
                ids.add(row[0])

    def iterreferences(self):
        ids = {}
        for i, head, row in self.iterrows('1 Data Source'):
            for id_, ref, doi in [row[7:10], row[10:13], row[13:16]]:
                id_ = id_.strip()
                if id_:
                    if id_ not in ids:
                        yield Reference(id_, ref, doi)
                        ids[id_] = ref
                    else:
                        assert ids[id_] == ref

    def iterdata(self):
        params = None
        for i, head, row in self.iterrows('2 Data'):
            if not params:
                params, in_params = collections.OrderedDict(), False
                for j, (name, unit) in enumerate(list(zip(*head))):
                    if in_params:
                        param = name
                        if unit:
                            param += ' [{0}]'.format(unit)
                        if param in params:
                            raise ValueError(param)
                        if param:
                            params[param] = j
                    if name == 'PARAMETER':
                        in_params = True
            data = []
            for p, j in params.items():
                less, precision = False, None
                v = row[j]
                if isinstance(v, str):
                    v = v.replace('−', '-')
                    if v.strip().startswith('<') or v.startswith('≤'):
                        v = v.strip()[1:].strip()
                        less = True
                    elif '±' in v:
                        v, _, precision = v.partition('±')
                        precision = float(precision)

                if v in [
                    None,
                    '',
                    'nd',
                    'bdl',
                    '2σ',
                    'LOD',
                ]:
                    v = None
                else:
                    v = float(v)
                data.append((p, (v, less, precision)))
            d = dict(zip(head[1], row))
            yield Datapoint(
                d['Pofatu ID'],
                d['Sample category'],
                d['Sample comment'],
                Location(
                    d['Location 1'],
                    d['Location 2'],
                    d['Location 3'],
                    d['Location comment'],
                    d['Latitude'],
                    d['Longitude'],
                    d['Elevation'],
                ),
                d['Petrography'],
                d['Citation code 1 [Data]'],
                Artefact(
                    d['Artefact name'],
                    d['Artefact description'],
                    d['Artefact category'],
                    d['Artefact comments'],
                    d['Citation code 2 [Artefact]'],
                ),
                Site(
                    d['Site name'],
                    d['Site context'],
                    d['Stratigraphic position'],
                    d['Site comments'],
                    d['Citation 3 [Site]'],
                ),
                (d['Analyzed material 1'], d['Analyzed material 2']),
                d['[citation code][ _ ][A], [B], etc.'],
                collections.OrderedDict(data),
            )

    @util.callcount
    def log_or_raise(self, log, msg):
        if log:
            log.warn(msg)
        else:
            raise ValueError(msg)

    def validate(self, log=None):
        bib = {rec.id: rec for rec in self.iterbib()}
        refs = list(self.iterreferences())
        for ref in refs:
            if ref.id not in bib:
                self.log_or_raise('Missing source in bib: {0}'.format(ref.id))
        dps = list(self.iterdata())
        for contrib in self.itercontributions():
            if contrib.id not in bib:
                self.log_or_raise('Missing source in bib: {0}'.format(contrib.id))
        list(self.itermethods())
        return self.log_or_raise.callcount
