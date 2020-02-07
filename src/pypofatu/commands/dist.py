"""
Create data formats for distribution
"""
import shutil
import pathlib
import collections

import attr
from csvw import TableGroup, Table
from csvw.db import Database
from clldutils import markup

import pypofatu
from pypofatu.models import *  # noqa: F403


def run(args):
    mdpath = args.repos.dist_dir / 'metadata.json'
    shutil.copy(str(pathlib.Path(pypofatu.__file__).parent / 'metadata.json'), str(mdpath))
    tg = TableGroup.from_file(mdpath)
    tg.common_props['dc:identifier'] = 'https://doi.org/10.5281/zenodo.3634436'
    tg.common_props["dc:license"] = "https://creativecommons.org/licenses/by/4.0/"
    tg.common_props["dc:title"] = "Pofatu"
    tg.common_props["dcat:accessURL"] = "https://pofatu.clld.org"

    bibfields = set()
    bib = list(args.repos.iterbib())
    for e in bib:
        bibfields = bibfields | set(e.keys())
    tables, data = {}, {}
    for name, desc, cols, cls, exclude in [
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
            ['references', 'normalizations']),
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
        if cls:
            cols.extend(fields2cols(cls, exclude=exclude or []).values())
        if name == 'samples':
            for cls, ex in [
                (Contribution, ['source_ids', 'contact_mail', 'contributors']),
                (Location, []),
                (Artefact, ['source_ids']),
                (Site, ['source_ids']),
            ]:
                cols.extend(fields2cols(cls, exclude=tuple(ex), prefix=True).values())

        tables[name] = add_table(tg, name + '.csv', cols)
        tables[name].common_props['dc:description'] = desc
        data[name] = collections.OrderedDict() if 'ID' in cols else []

    tables['references'].add_foreign_key('Source_ID', 'sources.csv', 'ID')
    tables['references'].add_foreign_key('Sample_ID', 'samples.csv', 'ID')
    tables['measurements'].add_foreign_key('Sample_ID', 'samples.csv', 'ID')
    tables['measurements'].add_foreign_key('Method_ID', 'methods.csv', 'ID')
    tables['methods_reference_samples'].add_foreign_key(
        'Reference_sample_ID', 'reference_samples.csv', 'ID')
    tables['methods_reference_samples'].add_foreign_key('Method_ID', 'methods.csv', 'ID')
    tables['methods_normalizations'].add_foreign_key('Normalization_ID', 'normalizations.csv', 'ID')
    tables['methods_normalizations'].add_foreign_key('Method_ID', 'methods.csv', 'ID')

    contribs = {}
    for c in args.repos.itercontributions():
        contribs[c.id] = c
        for s in c.source_ids:
            contribs[s] = c

    for e in args.repos.iterbib():
        data['sources'][e.id] = {'ID': e.id, 'Entry_Type': e.genre}
        data['sources'][e.id].update(e)

    mrefs, mnorms = set(), set()

    for a in args.repos.iterdata():
        if a.sample.id not in data['samples']:
            kw = {'ID': a.sample.id}
            for cls, inst in [
                (Sample, a.sample),
                (Contribution, contribs[a.sample.source_id]),
                (Location, a.sample.location),
                (Artefact, a.sample.artefact),
                (Site, a.sample.site),
            ]:
                for f, c in fields2cols(cls, prefix=cls != Sample).items():
                    kw[c['name']] = getattr(inst, f)
            data['samples'][a.sample.id] = kw
        data['references'].append({
            'Source_ID': a.sample.source_id, 'Sample_ID': a.sample.id, 'scope': 'sample'})
        for sid in a.sample.artefact.source_ids:
            data['references'].append({
                'Source_ID': sid, 'Sample_ID': a.sample.id, 'scope': 'artefact'})
        for sid in a.sample.site.source_ids:
            data['references'].append({
                'Source_ID': sid, 'Sample_ID': a.sample.id, 'scope': 'site'})
        for m in a.measurements:
            kw = {
                'Sample_ID': a.sample.id,
                'Method_ID': m.method.id if m.method else '',
                'value_string': m.as_string()}
            for f, c in fields2cols(Measurement).items():
                kw[c['name']] = getattr(m, f)
            data['measurements'].append(kw)

            if m.method:
                kw = {'ID': m.method.id}
                for f, c in fields2cols(Method).items():
                    kw[c['name']] = getattr(m.method, f)
                data['methods'][m.method.id] = kw

                for r in m.method.references:
                    rid = '{0}-{1}'.format(m.method.id, r.sample_name)
                    data['reference_samples'][rid] = {'ID': rid}
                    for f, c in fields2cols(MethodReference).items():
                        data['reference_samples'][rid][c['name']] = getattr(r, f)
                    if (m.method.id, rid) not in mrefs:
                        data['methods_reference_samples'].append({
                            'Method_ID': m.method.id, 'Reference_sample_ID': rid,
                        })
                        mrefs.add((m.method.id, rid))

                for r in m.method.normalizations:
                    rid = '{0}-{1}'.format(m.method.id, r.reference_sample_name)
                    data['normalizations'][rid] = {'ID': rid}
                    for f, c in fields2cols(MethodNormalization).items():
                        data['normalizations'][rid][c['name']] = getattr(r, f)
                    if (m.method.id, rid) not in mnorms:
                        data['methods_normalizations'].append({
                            'Method_ID': m.method.id, 'Normalization_ID': rid,
                        })
                        mnorms.add((m.method.id, rid))

    for name, table in tables.items():
        table.write(data[name].values() if isinstance(data[name], dict) else data[name])
    tg.to_file(mdpath)

    db = Database(tg, args.repos.db_path)
    if db.fname.exists():
        db.fname.unlink()  # pragma: no cover
    db.write_from_tg()

    header = ['name', 'min', 'max', 'mean', 'median', 'count_analyses']
    t = markup.Table(*header)
    for p in sorted(args.repos.iterparameters(), key=lambda pp: pp.name):
        t.append([getattr(p, h) for h in header])
    args.repos.dist_dir.joinpath('parameters.md').write_text(
        '# Geochemical Parameters\n\n{0}'.format(t.render()), encoding='utf8')


def add_table(tg, fname, columns):
    def _column(spec):
        if isinstance(spec, str):
            return dict(name=spec, datatype='string')
        if isinstance(spec, dict):
            return spec
        raise TypeError(spec)  # pragma: no cover

    schema = {'columns': [_column(c) for c in columns]}
    if 'ID' in columns:
        schema['primaryKey'] = ['ID']

    tg.tables.append(Table.fromvalue({'tableSchema': schema, 'url': fname}))
    table = tg.tables[-1]
    table._parent = tg
    return table


def fields2cols(cls, exclude=('source_ids',), prefix=False):
    return collections.OrderedDict(
        (f, attrib2column(c, (cls.__name__.lower() + '_' + f) if prefix else f))
        for f, c in attr.fields_dict(cls).items() if f not in exclude)


def attrib2column(a, name):
    col = {k: v for k, v in a.metadata.items() if not k.startswith('_')} \
        if a.metadata else {'datatype': 'string'}
    col['name'] = name
    return col
