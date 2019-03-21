import collections
import itertools

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
class Sample(object):  # translates to Value, attached to a valueset defined by Location, Parameter and Contribution!
    # Aggregate typed valueset references? Each value needs references, too!
    id = attr.ib()
    category = attr.ib(validator=attr.validators.in_(['SOURCE', 'ARTEFACT']))  # Two parameters! correspond to the two views!
    comment = attr.ib()
    location = attr.ib()
    petrography = attr.ib()
    source_id = attr.ib()

    artefact = attr.ib()
    site = attr.ib()


@attr.s
class Analysis(object):
    id = attr.ib()
    analyzed_material = attr.ib()


@attr.s
class Measurement(object):
    sample_id = attr.ib()
    analysis_id = attr.ib()
    parameter = attr.ib()
    value = attr.ib()
    less = attr.ib()
    precision = attr.ib()

    @property
    def method_uid(self):
        return '{0} {1}'.format(self.analysis_id, self.parameter.split()[0]).lower()


class Pofatu(API):
    def dump_sheets(self):
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
            self.dump_sheets()

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
        for key, rows in itertools.groupby(
            sorted(self.iterrows('3 Analytical metadata'), key=lambda r: r[2][:2]),
            lambda r: r[2][:2],
        ):
            for k, (i, head, row) in enumerate(rows):
                if k == 0:
                    m = Method(*row[:8], references=[])
                m.references.append(MethodReference(*row[8:12]))
            yield m

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
        for sid, rows in itertools.groupby(
            sorted(self.iterrows('2 Sample and compositional data'), key=lambda o: o[2][2]),
            lambda o: o[2][2],
        ):
            rows = list(rows)
            if not params:
                params, in_params = collections.OrderedDict(), False
                for j, (name, unit) in enumerate(list(zip(*rows[0][1]))):
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
            sample, measurements = None, []
            for k, (i, head, row) in enumerate(rows):
                if k == 0:
                    d = dict(zip(head[1], row))
                    sample = Sample(
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
                    )
                analysis = Analysis(
                    d['[citation code][ _ ][A], [B], etc.'],
                    (d['Analyzed material 1'], d['Analyzed material 2']),
                )
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

                    if v not in [
                        None,
                        '',
                        'nd',
                        'bdl',
                        '2σ',
                        'LOD',
                    ]:
                        v = float(v)
                        measurements.append((Measurement(
                            sample_id=sample.id,
                            analysis_id=analysis.id,
                            parameter=p,
                            value=float(v),
                            less=less,
                            precision=precision,
                        ), analysis))
            yield sample, measurements

    @util.callcount
    def log_or_raise(self, log, msg):
        if log:
            log.warn(msg)
        else:
            raise ValueError(msg)

    def validate(self, log=None):
        missed_methods = collections.Counter()
        bib = {rec.id: rec for rec in self.iterbib()}
        refs = list(self.iterreferences())
        for ref in refs:
            if ref.id not in bib:
                self.log_or_raise(log, 'Missing source in bib: {0}'.format(ref.id))
        methods = {m.uid: m for m in self.itermethods()}
        dps = list(self.iterdata())
        for dp, measurements in dps:
            l = [m.parameter for m, a in measurements]
            assert len(l) == len(set(l))
            #count = collections.Counter(l)
            #print(dp.id, [k for k, v in count.most_common() if v > 1])
            for mm, _ in measurements:
                if mm.method_uid not in methods:
                    missed_methods.update([mm.method_uid])
        for contrib in self.itercontributions():
            if contrib.id not in bib:
                self.log_or_raise(log, 'Missing source in bib: {0}'.format(contrib.id))
        for k, v in missed_methods.most_common():
            self.log_or_raise(log, 'Missing method: {0} {1}x'.format(k, v))
        return self.log_or_raise.callcount
