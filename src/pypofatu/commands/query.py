"""
Query Pofatu data.
"""
import sys

from clldutils.clilib import Table, add_format


def register(parser):  # pylint: disable=C0116
    parser.add_argument(
        'query',
        metavar='QUERY',
        help="SQL query to execute. Pass '-' to read from stdin. "
             "Pass '.schema' to print the db schema to screen.")
    add_format(parser, 'simple')


def run(args):  # pylint: disable=C0116
    args.log.info('SQLite database at %s', args.repos.db_path)
    if args.query == '.schema':
        for r in args.repos.query("select sql from sqlite_master where type = 'table'")[1]:
            print(r[0])
        return

    desc, res = args.repos.query(sys.stdin.read() if args.query == '-' else args.query)
    with Table(args, *[d[0] for d in desc]) as t:
        for row in res:
            t.append(row)
