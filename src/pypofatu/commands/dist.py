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
    #
    # FIXME: add metadata, e.g. pypofatu version, repos checkout, use cldfcatalog Repository?
    #

    bibfields = set()
    bib = list(args.repos.iterbib())
    for e in bib:
        bibfields = bibfields | set(e.keys())
    tables, data = {}, {}
    for name, cols in [
        ('samples', ['ID']),
        ('sources', ['ID', 'Entry_Type'] + [f for f in sorted(bibfields) if f not in {'abstract'}]),
        ('references', [
            'Source_ID',
            'Sample_ID',
            {'name': 'scope', 'dc:description': 'The aspect of a sample a reference relates to'}]),
        ('measurements', ['Sample_ID', 'value_string']),
    ]:
        if name == 'measurements':
            for cls, ex in [(Measurement, ['method']), (Method, ['references'])]:
                cols.extend(fields2cols(cls, exclude=ex, prefix=cls == Method).values())
            cols.append('method_reference_samples')
        if name == 'samples':
            for cls, ex in [
                (Sample, ['id', 'source_id', 'location', 'artefact', 'site']),
                (Contribution, ['source_ids', 'contact_mail', 'contributors']),
                (Location, []),
                (Artefact, ['source_ids']),
                (Site, ['source_ids']),
            ]:
                cols.extend(fields2cols(cls, exclude=tuple(ex), prefix=cls != Sample).values())
        tables[name] = add_table(tg, name + '.csv', cols)
        data[name] = collections.OrderedDict() if 'ID' in cols else []

    tables['references'].add_foreign_key('Source_ID', 'sources.csv', 'ID')
    tables['references'].add_foreign_key('Sample_ID', 'samples.csv', 'ID')
    tables['measurements'].add_foreign_key('Sample_ID', 'samples.csv', 'ID')

    contribs = {}
    for c in args.repos.itercontributions():
        contribs[c.id] = c
        for s in c.source_ids:
            contribs[s] = c

    for e in args.repos.iterbib():
        data['sources'][e.id] = {'ID': e.id, 'Entry_Type': e.genre}
        data['sources'][e.id].update(e)

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
            kw = {'Sample_ID': a.sample.id, 'value_string': m.as_string()}
            for cls, inst in [
                (Measurement, m),
                (Method, m.method),
            ]:
                if inst:
                    for f, c in fields2cols(cls, prefix=cls != Measurement).items():
                        kw[c['name']] = getattr(inst, f)
            if m.method:
                kw['method_reference_samples'] = '; '.join(
                    r.as_string() for r in m.method.references)
            data['measurements'].append(kw)

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


def fields2cols(cls, exclude=('source_ids',), prefix=True):
    return collections.OrderedDict(
        (f, attrib2column(c, (cls.__name__.lower() + '_' + f) if prefix else f))
        for f, c in attr.fields_dict(cls).items() if f not in exclude)


def attrib2column(a, name):
    col = {k: v for k, v in a.metadata.items() if not k.startswith('_')} \
        if a.metadata else {'datatype': 'string'}
    col['name'] = name
    return col
