import itertools
import collections

import attr
from clldutils.apilib import API
from clldutils.source import Source
from csvw.dsv import reader, UnicodeWriter
import xlrd
from pybtex.database import parse_file

from pypofatu.models import *
from pypofatu import util
from pypofatu import errata

SD_VALUE_SUFFIX = ' SD value'
SD_SIGMA_SUFFIX = ' SD sigma'
SHEETS = collections.OrderedDict([(n.split()[0], n) for n in [
    '1 Data source',
    '2 Sample metadata',
    '3 Compositional data',
    '4 Methodological metadata',
    '5 Vocabularies',
]])


def clean_bib_key(s):
    key = s.replace('{', '').replace('}', '')
    return errata.KEYS_IN_BIB.get(key, key)


@attr.s
class Row(object):
    index = attr.ib()
    keys = attr.ib()
    values = attr.ib()

    @property
    def dict(self):
        return collections.OrderedDict(zip(self.keys[1], self.values))


class Pofatu(API):
    def fname_for_sheet(self, sheetname):
        for number, name in SHEETS.items():
            if sheetname[0] == number:
                return '{0}.csv'.format(name.replace(' ', '_'))
        else:
            raise ValueError(sheetname)

    def dump_sheets(self, fname='Pofatu Dataset.xlsx'):
        wb = xlrd.open_workbook(str(self.repos / fname))
        for name in wb.sheet_names():
            sheet = wb.sheet_by_name(name)
            with UnicodeWriter(self.repos / self.fname_for_sheet(name)) as writer:
                for i in range(sheet.nrows):
                    writer.writerow([sheet.cell(i, j).value for j in range(sheet.ncols)])

    def iterbib(self):
        for entry in parse_file(str(self.repos / 'pofatu-references.bib'), bib_format='bibtex').entries.values():
            yield Source.from_entry(clean_bib_key(entry.fields['annotation']), entry)

    def iterrows(self, number_or_name):
        csv_path = self.repos / self.fname_for_sheet(number_or_name)
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
                yield Row(i, head, row)

    def itermethods(self):
        for key, rows in itertools.groupby(
            sorted(self.iterrows('4'), key=lambda r: r.values[:2]),
            lambda r: r.values[:2],
        ):
            for k, row in enumerate(rows):
                if k == 0:
                    m = Method(*row.values[:8], references=[])
                m.references.append(MethodReference(*row.values[8:12]))
            yield m

    def itercontributions(self):
        ids = set()
        for row in self.iterrows('1'):
            row = row.values
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
        for row in self.iterrows('1'):
            for id_, ref, doi in [row.values[7:10], row.values[10:13], row.values[13:16]]:
                id_ = id_.strip()
                if id_:
                    if id_ not in ids:
                        yield Reference(id_, ref, doi)
                        ids[id_] = ref
                    #else:
                    #    assert ids[id_] == ref, '{0} vs {1}'.format(ids[id_], ref)

    def _iter_merged(self, rows):
        for mid, rows_ in itertools.groupby(rows, lambda r: r.values[2]):
            rows_ = list(rows_)
            if len(rows_) > 1:
                # multiple rows for the same method!
                vals = rows_[0].values
                for row in rows_[1:]:
                    for i, v in enumerate(row.values):
                        if v:
                            if vals[i] and vals[i] != v:
                                print(row.values[:3], row.keys[0][i], row.keys[1][i], vals[i], v)
                                # Cancel the measurement!
                                vals[i] = ''
                rows_[0].values = vals
            yield rows_[0]

    def compositional_data(self):
        """
        return a `dict`, grouping compositional data by sample id
        """
        res = collections.OrderedDict()
        for sample_id, rows in itertools.groupby(
            sorted(self.iterrows('3'), key=lambda r_: (r_.values[1], r_.values[2])),
            lambda r_: r_.values[1]
        ):
            sample_id = errata.SAMPLE_IDS.get(sample_id, sample_id)
            res[sample_id] = list(self._iter_merged(rows))
        return res

    def itersamples(self):
        sids = {}
        for r in self.iterrows('2'):
            d = r.dict
            if not d['Sample ID']:
                continue
            if d['Sample ID'] in sids:
                assert sids[d['Sample ID']] == r.values
                # Ignore true duplicates.
                continue
            sids[d['Sample ID']] = r.values
            yield Sample(
                d['Sample ID'],
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
                d['Source ID 1'],
                (d['Analyzed material 1'], d['Analyzed material 2']),
                Artefact(
                    d['Artefact ID'],
                    d['Artefact name'],
                    d['Artefact category'],
                    d['Artefact attributes'],
                    d['Artefact comments'],
                    d['Source ID 2'],
                    d['Fieldwork'],
                ),
                Site(
                    d['Site name'],
                    d['Site code'],
                    d['Site context'],
                    d['Site comments'],
                    d['Stratigraphic position'],
                    d['Source ID 3'],
                ),
            )

    def iterdata(self):
        params = None
        cd = self.compositional_data()
        methods = {m.code: m for m in self.itermethods()}
        aids = {}

        for sample in self.itersamples():
            rows = cd[sample.id]
            if not params:
                params, in_params = collections.OrderedDict(), False
                for j, (name, unit) in enumerate(list(zip(*rows[0].keys[1]))):
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

            for k, row in enumerate(rows):
                d = row.dict
                analysis = Analysis(
                    '{0}-{1}'.format(sample.id, d['Method ID']),
                    method=methods.get(d['Method ID']),
                    sample=sample,
                )
                if analysis.id in aids:
                    raise ValueError(analysis.id)
                aids[analysis.id] = row.values
                for p, j in params.items():
                    if p.endswith(SD_VALUE_SUFFIX) or p.endswith(SD_SIGMA_SUFFIX):
                        continue
                    less, precision = False, None

                    v = d[j]
                    if isinstance(v, str):
                        v = v.replace('−', '-')
                        if v.strip().startswith('<') or v.startswith('≤'):
                            v = v.strip()[1:].strip()
                            less = True

                    if v not in [
                        None,
                        '',
                        'nd',
                        'bdl',
                        'LOD',
                    ]:
                        sd_value_key = '{0}{1}'.format(p, SD_VALUE_SUFFIX)
                        sd_sigma_key = '{0}{1}'.format(p, SD_SIGMA_SUFFIX)
                        v = float(v)
                        analysis.measurements.append(Measurement(
                            parameter=p,
                            value=v,
                            less=less,
                            precision=d[params[sd_value_key]] if sd_value_key in params else None,
                            sigma=d[params[sd_sigma_key]] if sd_sigma_key in params else None,
                        ))
                yield analysis

    @util.callcount
    def log_or_raise(self, log, msg):
        if log:
            log.warn(msg)
        else:
            raise ValueError(msg)

    def validate(self, log=None, bib=None):
        from tqdm import tqdm

        missed_methods = collections.Counter()
        bib = bib if bib is not None else {rec.id: rec for rec in self.iterbib()}
        refs = list(self.iterreferences())
        if bib:
            for ref in refs:
                if ref.id not in bib:
                    self.log_or_raise(log, 'Missing source in bib: {0}'.format(ref.id))

        aids = set()
        for dp in tqdm(self.iterdata()):
            assert dp.id not in aids, dp.id
            aids.add(dp.id)
            l = [m.parameter for m in dp.measurements]
            assert len(l) == len(set(l))

        for contrib in self.itercontributions():
            if bib and contrib.id not in bib:
                self.log_or_raise(log, 'Missing source in bib: {0}'.format(contrib.id))
        for k, v in missed_methods.most_common():
            self.log_or_raise(log, 'Missing method: {0} {1}x'.format(k, v))
        return self.log_or_raise.callcount
