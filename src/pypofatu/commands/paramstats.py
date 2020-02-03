"""
Create data formats for distribution
"""
from clldutils.clilib import Table, add_format


def register(parser):
    add_format(parser, default='simple')


def run(args):
    header = ['name', 'min', 'max', 'mean', 'median', 'count_analyses']
    with Table(args, *header) as t:
        for p in sorted(args.repos.iterparameters(), key=lambda pp: pp.name):
            t.append([getattr(p, h) for h in header])
