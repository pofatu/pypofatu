"""

"""
from clldutils.clilib import PathType


def register(parser):
    parser.add_argument(
        '--dataset',
        help="Excel file to dump sheets to csv tables",
        default=None,
        type=PathType(type='file'))


def run(args):
    args.repos.dump_sheets(args.dataset)
