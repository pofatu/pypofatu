"""
Create data formats for distribution
"""
import shutil
import pathlib
import collections
import dataclasses

import attr
from csvw import TableGroup, Table
from csvw.db import Database
from clldutils import markup

import pypofatu
from pypofatu.models import (
    Sample, Measurement, Method, MethodReference, MethodNormalization, Contribution, Location, Site,
    Artefact, Analysis, FractionationCorrection,
)


def run(args):  # pylint: disable=C0116
    if not args.repos.dist_dir.exists():
        args.repos.dist_dir.mkdir()  # pragma: no cover
    mdpath = args.repos.dist_dir / 'metadata.json'
    shutil.copy(pathlib.Path(pypofatu.__file__).parent / 'metadata.json', mdpath)

    csvw = CSVW.from_default_md(mdpath, list(args.repos.iterbib()))
    contribs = {}
    for c in args.repos.itercontributions():
        contribs[c.id] = c
        for s in c.source_ids:
            contribs[s] = c

    for e in args.repos.iterbib():
        csvw.add_source(e)

    for a in args.repos.iterdata():
        csvw.add_analysis(a, contribs)

    csvw.write()

    db = Database(csvw.tg, args.repos.db_path)
    if db.fname.exists():
        db.fname.unlink()  # pragma: no cover
    db.write_from_tg()

    header = ['name', 'min', 'max', 'mean', 'median', 'count_analyses']
    t = markup.Table(*header)
    for p in sorted(args.repos.iterparameters(), key=lambda pp: pp.name):
        t.append([getattr(p, h) for h in header])
    args.repos.dist_dir.joinpath('parameters.md').write_text(
        f'# Geochemical Parameters\n\n{t.render()}', encoding='utf8')


@dataclasses.dataclass
class CSVW:
    """
    Represents a CSVW-described set of CSV files.
    """
    mdpath: pathlib.Path
    tg: TableGroup
    tables: dict = dataclasses.field(default_factory=dict)
    data: dict = dataclasses.field(default_factory=dict)
    mrefs: set = dataclasses.field(default_factory=set)
    mnorms: set = dataclasses.field(default_factory=set)

    @classmethod
    def from_default_md(cls, mdpath: pathlib.Path, bib: list) -> 'CSVW':
        """Initialize the dataset with the default metadata."""
        tg = TableGroup.from_file(mdpath)
        tg.common_props['dc:identifier'] = 'https://doi.org/10.5281/zenodo.3634436'
        tg.common_props["dc:license"] = "https://creativecommons.org/licenses/by/4.0/"
        tg.common_props["dc:title"] = "Pofatu"
        tg.common_props["dcat:accessURL"] = "https://pofatu.clld.org"
        res = cls(mdpath, tg)

        bibfields = set()
        for e in bib:
            bibfields = bibfields | set(e.keys())
        for name, desc, cols, cls_, exclude in [
            (
                'samples',
                'Samples of archeological interest which have been analysed geochemically',
                ['ID'],
                Sample,
                ['id', 'source_id', 'location', 'artefact', 'site']),
            (
                'sources',
                'Bibliographical sources',
                ['ID', 'Entry_Type'] + [f for f in sorted(bibfields) if f not in {'abstract'}],
                None,
                None),
            (
                'references',
                'Bibliographical references for aspects of a sample',
                [
                    'Source_ID',
                    'Sample_ID',
                    {
                        'name': 'scope',
                        'dc:description': 'The aspect of a sample described by the reference'}],
                None,
                None),
            (
                'measurements',
                'Individual measurements of geochemical parameters for a sample',
                ['Sample_ID', 'value_string', 'Method_ID'],
                Measurement,
                ['method']),
            (
                'methods',
                'Metadata about the methodology used for a measurement',
                ['ID'],
                Method,
                ['references', 'normalizations', 'fractionation_correction']),
            (
                'methods_reference_samples',
                'Association table between methods and reference samples',
                ['Method_ID', 'Reference_sample_ID'],
                None,
                None),
            (
                'reference_samples',
                'Reference samples used to ensure analytical accuracy and reproducibility',
                ['ID'],
                MethodReference,
                None),
            (
                'methods_normalizations',
                'Association table between methods and normalization reference samples',
                ['Method_ID', 'Normalization_ID'],
                None,
                None),
            (
                'normalizations',
                'Reference samples used for normalization',
                ['ID'],
                MethodNormalization,
                None),
        ]:
            if cls_:
                cols.extend(_fields2cols(cls_, exclude=exclude or []).values())
            if name == 'methods':
                cols.extend(_fields2cols(FractionationCorrection, prefix=True).values())

            if name == 'samples':
                for cls_, ex in [
                    (Contribution, ['source_ids', 'contact_mail', 'contributors']),
                    (Location, []),
                    (Artefact, ['source_ids']),
                    (Site, ['source_ids']),
                ]:
                    cols.extend(_fields2cols(cls_, exclude=tuple(ex), prefix=True).values())

            res.tables[name] = res._add_table(name + '.csv', cols)
            res.tables[name].common_props['dc:description'] = desc
            res.data[name] = collections.OrderedDict() if 'ID' in cols else []

        res.tables['references'].add_foreign_key('Source_ID', 'sources.csv', 'ID')
        res.tables['references'].add_foreign_key('Sample_ID', 'samples.csv', 'ID')
        res.tables['measurements'].add_foreign_key('Sample_ID', 'samples.csv', 'ID')
        res.tables['measurements'].add_foreign_key('Method_ID', 'methods.csv', 'ID')
        res.tables['methods_reference_samples'].add_foreign_key(
            'Reference_sample_ID', 'reference_samples.csv', 'ID')
        res.tables['methods_reference_samples'].add_foreign_key('Method_ID', 'methods.csv', 'ID')
        res.tables['methods_normalizations'].add_foreign_key(
            'Normalization_ID', 'normalizations.csv', 'ID')
        res.tables['methods_normalizations'].add_foreign_key('Method_ID', 'methods.csv', 'ID')
        return res

    def add_source(self, e):
        """Add a source."""
        self.data['sources'][e.id] = {'ID': e.id, 'Entry_Type': e.genre}
        self.data['sources'][e.id].update(e)

    def add_analysis(self, a: Analysis, contribs):
        """Add data from an Analysis object."""
        if a.sample.id not in self.data['samples']:
            kw = {'ID': a.sample.id}
            for cls, inst in [
                (Sample, a.sample),
                (Contribution, contribs[a.sample.source_id]),
                (Location, a.sample.location),
                (Artefact, a.sample.artefact),
                (Site, a.sample.site),
            ]:
                for f, c in _fields2cols(cls, prefix=cls != Sample).items():
                    kw[c['name']] = getattr(inst, f)
            self.data['samples'][a.sample.id] = kw
        self.data['references'].append({
            'Source_ID': a.sample.source_id, 'Sample_ID': a.sample.id, 'scope': 'sample'})
        for sid in a.sample.artefact.source_ids:
            self.data['references'].append({
                'Source_ID': sid, 'Sample_ID': a.sample.id, 'scope': 'artefact'})
        for sid in a.sample.site.source_ids:
            self.data['references'].append({
                'Source_ID': sid, 'Sample_ID': a.sample.id, 'scope': 'site'})
        for m in a.measurements:
            kw = {
                'Sample_ID': a.sample.id,
                'Method_ID': m.method.id if m.method else '',
                'value_string': m.as_string()}
            for f, c in _fields2cols(Measurement).items():
                kw[c['name']] = getattr(m, f)
            self.data['measurements'].append(kw)

            if m.method:
                self._add_method(m)

    def _add_method(self, m: Measurement):
        kw = {'ID': m.method.id}
        for cls, inst in [
            (Method, m.method),
            (FractionationCorrection, m.method.fractionation_correction),
        ]:
            for f, c in _fields2cols(cls, prefix=cls != Method).items():
                kw[c['name']] = getattr(inst, f)

        self.data['methods'][m.method.id] = kw

        for r in m.method.references:
            rid = f'{m.method.id}-{r.sample_name}'
            self.data['reference_samples'][rid] = {'ID': rid}
            for f, c in _fields2cols(MethodReference).items():
                self.data['reference_samples'][rid][c['name']] = getattr(r, f)
            if (m.method.id, rid) not in self.mrefs:
                self.data['methods_reference_samples'].append({
                    'Method_ID': m.method.id, 'Reference_sample_ID': rid,
                })
                self.mrefs.add((m.method.id, rid))

        for r in m.method.normalizations:
            rid = f'{m.method.id}-{r.reference_sample_name}'
            self.data['normalizations'][rid] = {'ID': rid}
            for f, c in _fields2cols(MethodNormalization).items():
                self.data['normalizations'][rid][c['name']] = getattr(r, f)
            if (m.method.id, rid) not in self.mnorms:
                self.data['methods_normalizations'].append({
                    'Method_ID': m.method.id, 'Normalization_ID': rid,
                })
                self.mnorms.add((m.method.id, rid))

    def write(self):
        """Write the files of the dataset to disk."""
        for name, table in self.tables.items():
            table.write(
                self.data[name].values() if isinstance(self.data[name], dict) else self.data[name])
        self.tg.to_file(self.mdpath)

    def _add_table(self, fname, columns):
        def _column(spec):
            if isinstance(spec, str):
                return {'name': spec, 'datatype': 'string'}
            if isinstance(spec, dict):
                return spec
            raise TypeError(spec)  # pragma: no cover

        schema = {'columns': [_column(c) for c in columns]}
        if 'ID' in columns:
            schema['primaryKey'] = ['ID']

        self.tg.tables.append(Table.fromvalue({'tableSchema': schema, 'url': fname}))
        table = self.tg.tables[-1]
        table._parent = self.tg  # pylint: disable=W0212
        return table


def _fields2cols(cls, exclude=('source_ids',), prefix=False):
    return collections.OrderedDict(
        (f, _attrib2column(c, (cls.__name__.lower() + '_' + f) if prefix else f))
        for f, c in attr.fields_dict(cls).items() if f not in exclude)


def _attrib2column(a, name):
    col = {k: v for k, v in a.metadata.items() if not k.startswith('_')} \
        if a.metadata else {'datatype': 'string'}
    col['name'] = name
    return col
