"""
Query Pofatu data.
"""
from clldutils.clilib import Table, add_format


def register(parser):
    parser.add_argument(
        'query',
        metavar='QUERY',
        help="SQL query to execute. Pass '.schema' to print the db schema to screen.")
    add_format(parser, 'plain')


def run(args):
    args.log.info('SQLite database at {0}'.format(args.repos.db_path))
    if args.query == '.schema':
        for r in args.repos.query("select sql from sqlite_master where type = 'table'").fetchall():
            print(r[0])
        return

    res = args.repos.query(args.query)
    with Table(args, *[d[0] for d in res.description]) as t:
        for row in res.fetchall():
            t.append(row)
