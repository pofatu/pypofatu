"""
Create data formats for distribution
"""
import statistics
import collections

from termcolor import colored
from clldutils.clilib import Table, add_format


def register(parser):
    add_format(parser, default='simple')


def run(args):
    data = collections.defaultdict(list)

    for a in args.repos.iterdata():
        for m in a.measurements:
            data[m.parameter].append(m.value)

    with Table(args, 'parameter', 'min', 'max', 'mean', 'median', 'n_analyses') as t:
        for p in sorted(data):
            vals = data[p]
            t.append([p, min(vals), max(vals), statistics.mean(vals), statistics.median(vals), len(vals)])

