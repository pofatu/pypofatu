"""
Pofatu API
"""
import logging
import sqlite3
import functools
import itertools
import contextlib
import collections
from collections.abc import Generator, Iterator
from typing import Union, Optional

import attr
from clldutils.apilib import API
from clldutils.source import Source
from csvw.dsv import reader
from simplepybtex.database import parse_file
from tqdm import tqdm

from pypofatu.models import (
    Method, MethodNormalization, MethodReference, Contribution, Sample, Location, Artefact, Site,
    Analysis, Measurement, Parameter, FractionationCorrection,
)
from pypofatu import util

SD_VALUE_SUFFIX = ' SD value'
SD_SIGMA_SUFFIX = ' SD sigma'
CSVS = collections.OrderedDict([(n.split('_', maxsplit=1)[0], n + '.csv') for n in [
    '1_Data_source',
    '2_Sample_metadata',
    '3_Compositional_data',
    '4_Methodological_metadata',
    '5_Vocabularies',
]])
RowType = collections.OrderedDict[str, Union[str, None]]
GroupKeyType = Union[str, tuple[str]]


@contextlib.contextmanager
def _dbcursor(conn):
    try:
        yield conn.cursor()
    finally:
        conn.rollback()


class Pofatu(API):
    """
    Represents the pofatu-data repository.
    """
    def __init__(self, repos):
        super().__init__(repos)
        self.raw_dir = self.repos / 'raw'
        self.csv_dir = self.repos / 'csv'
        self.dist_dir = self.repos / 'dist'
        self.db_path = self.dist_dir / 'pofatu.sqlite'
        self.bib_path = self.raw_dir / 'pofatu-references.bib'

    def query(self, sql: str) -> tuple[list, list]:
        """Query the database."""
        with contextlib.closing(sqlite3.connect(str(self.db_path))) as conn:
            with _dbcursor(conn) as cu:
                cu.execute(sql)
                return cu.description, cu.fetchall()

    def iterbib(self) -> Generator[Source, None, None]:
        """Yield references."""
        for entry in parse_file(str(self.bib_path), bib_format='bibtex').entries.values():
            if 'annotation' in entry.fields:
                entry.fields.pop('annotation')
            if 'annote' in entry.fields:
                entry.fields.pop('annote')
            yield Source.from_entry(entry.key, entry)

    def iterrows(self, number) -> Generator[RowType, None, None]:
        """Yield rows from a CSV file."""
        for row in reader(self.csv_dir / CSVS[str(number)], dicts=True):
            yield collections.OrderedDict((k, None if v == 'NA' else v) for k, v in row.items())

    def itergroupedrows(
            self,
            what,
            groupkeys,
            sortkeys=None,
    ) -> Generator[tuple[GroupKeyType, Iterator[RowType]]]:
        """Yield grouped rows."""
        def _key(key, d: dict):
            if isinstance(key, str):
                return d[key]
            return tuple(d[k] for k in key)

        yield from itertools.groupby(
            sorted(self.iterrows(what), key=functools.partial(_key, sortkeys or groupkeys)),
            functools.partial(_key, groupkeys))

    def itermethods(self) -> Generator[Method, None, None]:
        """Yield methods."""
        def get_method(mid: str, pid: str, d: RowType) -> Method:
            return Method(
                code=mid,
                parameter=pid,
                analyzed_material_1=d['Analyzed material 1'],
                analyzed_material_2=d['Analyzed material 2'],
                sample_preparation=d['Sample preparation'],
                chemical_treatment=d['Chemical treatment'],
                number_of_replicates=d['Number of replicates'],
                technique=d['Technique'],
                instrument=d['Instrument'],
                laboratory=d['Laboratory'],
                analyst=d['Analyst'],
                date=d['Analysis date'],
                comment=d['Analysis comment'],
                detection_limit=d['Detection limit'],
                detection_limit_unit=d['Detection limit unit'],
                total_procedural_blank_value=d['Blank value'],
                total_procedural_unit=d['Blank value unit'],
                fractionation_correction=FractionationCorrection(
                    parameter=d['Fractionation correction parameter'],
                    reference_sample_name=d['Fractionation correction reference sample name'],
                    sample_value=d['Fractionation correction sample value'],
                    sample_accepted_value=d['Fractionation correction sample accepted value'],
                    citation=d['Fractionation correction citation'],
                )
            )

        def _compare_method_data(m1, m2):
            m1 = attr.asdict(m1)
            m2 = attr.asdict(m2)
            for k, v in m1.items():
                if k not in ('references', 'normalizations'):
                    if v:
                        assert v == m2[k], f'{v}: {k} != {m2[k]}'

        for (mid, pid), rows in self.itergroupedrows('4', ('Method ID', 'Parameter')):
            assert mid and pid, (mid, pid)
            for k, row in enumerate(rows):
                if k == 0:
                    m = get_method(mid, pid, row)
                else:  # Make sure relevant properties of subsequent rows match the first one.
                    _compare_method_data(get_method(mid, pid, row), m)

                mr = MethodReference(
                    sample_name=row['Reference sample name'],
                    sample_measured_value=row['Reference sample measured value'],
                    uncertainty=row['Reference uncertainty'],
                    uncertainty_unit=row['Reference uncertainty unit'],
                    number_of_measurements=row['Reference n measurements'],
                )
                if any(attr.astuple(mr)) and mr not in m.references:
                    m.references.append(mr)
                mn = MethodNormalization(
                    reference_sample_name=row['Normalization reference sample name'],
                    reference_sample_accepted_value=row[
                        'Normalization sample accepted value'],
                    citation=row['Normalization citation'],
                )
                if any(attr.astuple(mn)) and mn not in m.normalizations:
                    m.normalizations.append(mn)
            yield m

    def itercontributions(self) -> Generator[Contribution, None, None]:
        """Yield contributions."""
        for cid, rows in self.itergroupedrows('1', 'Dataset ID'):
            kw = {'id': cid, 'source_ids': set()}
            for row in rows:
                kw['source_ids'].add(row['Source ID 1'])
                for i, key in [
                    ('Title', 'name'),
                    ('Abstract', 'description'),
                    ('Authors(s)', 'authors'),
                    ('Institution of the author', 'affiliation'),
                    ('Creator', 'contributors'),
                    ('Contact info', 'contact_email'),
                ]:
                    if row[i]:
                        assert (key not in kw) or (kw[key] == row[i]), (kw.get(key), row[i])
                        kw[key] = row[i]
            yield Contribution(**kw)

    def iter_compositional_data(self) -> Generator[tuple[str, list[RowType]], None, None]:
        """
        return a `dict`, grouping anlyses of samples by sample id
        """
        # Note: We already sort by Method ID, too, since we want to group by it in _iter_merged!
        for sample_id, rows in self.itergroupedrows('3', 'Sample ID', ('Sample ID', 'Method ID')):
            rows = list(rows)
            mids = set(r['Method ID'] for r in rows)
            assert len(mids) == len(rows), \
                f'multiple measurements for sample {sample_id} with same method ID: {mids}'
            yield sample_id.replace(chr(8208), '-'), rows

    def itersamples(self) -> Generator[Sample, None, None]:
        """Yield samples."""
        sids = {}
        for d in self.iterrows('2'):
            assert d['Sample ID'] not in sids, f"duplicate sample ID: {d['Sample ID']}"
            sids[d['Sample ID']] = list(d.values())
            yield Sample(
                id=d['Sample ID'],
                sample_name=d['Sample name'],
                sample_category=d['Sample category'],
                sample_comment=d['Sample comment'],
                location=Location(
                    region=d['Location 1'],
                    subregion=d['Location 2'],
                    locality=d['Location 3'],
                    comment=d['Location comment'],
                    latitude=d['Latitude'],
                    longitude=d['Longitude'],
                    elevation=d['Elevation'],
                ),
                petrography=d['Petrography'],
                source_id=d['Source ID 1'],
                artefact=Artefact(
                    id=d['Artefact ID'],
                    name=d['Artefact name'],
                    category=d['Artefact category'],
                    attributes=d['Artefact attributes'],
                    comment=d['Artefact comments'],
                    source_ids=d['Source ID 2'],
                    collector=d['Collector'],
                    collection_type=d['Fieldwork'],
                    fieldwork_date=d['Fieldwork date'],
                    collection_location=d['Collection storage location'],
                    collection_comment=d['Collection comment'],
                ),
                site=Site(
                    name=d['Site name'],
                    code=d['Site code'],
                    context=d['Site context'],  # sample sepcific
                    comment=d['Site comments'],  # sample sepcific
                    stratigraphic_position=d['Stratigraphic position'],  # sample sepcific
                    stratigraphy_comment=d['Stratigraphy comments'],
                    source_ids=d['Source ID 3'],
                ),
            )

    def iterdata(self) -> Generator[Analysis, None, None]:
        """Yield the data bundled into analyses."""
        params = None
        cd = collections.OrderedDict(self.iter_compositional_data())
        methods = {(m.code, m.parameter): m for m in self.itermethods()}
        aids = {}

        for sample in self.itersamples():
            rows = cd[sample.id]
            if not params:
                params = [
                    c for c in rows[0]
                    if c not in {'Source ID 1', 'Sample ID', 'Method ID', 'Note'}]

            for row in rows:
                analysis = Analysis(f"{sample.id}-{row['Method ID']}", sample=sample)
                assert analysis.id not in aids, 'duplicate analysis id'
                aids[analysis.id] = row.values
                for p in params:
                    if p.endswith(SD_VALUE_SUFFIX) or p.endswith(SD_SIGMA_SUFFIX):
                        continue
                    v, less = util.parse_value(row[p])
                    if v is not None:
                        sd_value_key = f'{p}{SD_VALUE_SUFFIX}'
                        sd_sigma_key = f'{p}{SD_SIGMA_SUFFIX}'
                        m = methods.get((row['Method ID'], p.split()[0]))
                        analysis.measurements.append(Measurement(
                            parameter=p.replace(' %', ' [%]').replace(' ppm', ' [ppm]'),
                            method=m,
                            value=v,
                            less=less,
                            value_sd=row.get(sd_value_key),
                            sd_sigma=row.get(sd_sigma_key),
                        ))
                yield analysis

    def iterparameters(self) -> Generator[Parameter, None, None]:
        """Yield parameters."""
        data = collections.defaultdict(list)
        for a in self.iterdata():
            for m in a.measurements:
                data[m.parameter].append(m.value)
        for n, vals in data.items():
            yield Parameter.from_values(n, vals)

    @util.callcount
    def log_or_raise(self, log: Optional[logging.Logger], msg: str):
        """Log a message or raise a ValueError."""
        if log:
            log.warning(msg)
        else:
            raise ValueError(msg)  # pragma: no cover

    def validate(
            self,
            log: Optional[logging.Logger] = None,
            bib: Optional[dict[str, Source]] = None
    ) -> int:
        """Validate the data, returning the number of calls to log_or_raise."""
        def md(m):
            return {
                col.name: getattr(m, col.name) for col in attr.fields(Method)
                if col.metadata.get('_parameter_specific') is False}

        def _compare_method_data(m1, m2):
            m1 = {k: v for k, v in m1.items() if k != 'laboratory'}
            m2 = {k: v for k, v in m2.items() if k != 'laboratory'}
            if m1 != m2:  # pragma: no cover
                print(m1)
                print(m2)
                print('---')
                raise ValueError('conflicting method data')

        methods = {}
        for m in self.itermethods():
            m_ = md(m)
            if m.code in methods:
                _compare_method_data(m_, methods[m.code])
            methods[m.code] = m_

        missed_methods = collections.Counter()
        bib = bib if bib is not None else {rec.id: rec for rec in self.iterbib()}
        aids = set()
        for dp in tqdm(self.iterdata()):
            assert dp.id not in aids, dp.id
            assert dp.sample.artefact.id, f'missing artefact ID in sample {dp.sample.id}'
            aids.add(dp.id)
            for m in dp.measurements:
                missed_methods.update([not m.method])
            if dp.sample.source_id not in bib:  # pragma: no cover
                self.log_or_raise(
                    log, f'{dp.sample.source_id}: sample source missing in bib')
            for sid in dp.sample.artefact.source_ids:
                if sid not in bib:  # pragma: no cover
                    self.log_or_raise(log, f'{sid}: artefact source missing in bib')
            for sid in dp.sample.site.source_ids:
                if sid not in bib:  # pragma: no cover
                    self.log_or_raise(log, f'{sid}: artefact source missing in bib')

        all_sources = set()
        for contrib in self.itercontributions():
            assert contrib.source_ids, f'{contrib}'
            if bib and contrib.id not in bib:  # pragma: no cover
                self.log_or_raise(log, f'Missing source in bib: {contrib.id}')
            # We relate samples to contributions by matching Sample.source_id with
            # Contribution.source_ids. Thus, the latter must be disjoint sets!
            shared_sources = all_sources.intersection(contrib.source_ids)
            assert not shared_sources, \
                f'Source ID appears for multiple contributions: {shared_sources}'
            all_sources = all_sources | set(contrib.source_ids)

        if missed_methods[True]:
            self.log_or_raise(
                log,
                f'Missing methods: {missed_methods[True]} of {missed_methods[False]} measurements')
        return self.log_or_raise.callcount
