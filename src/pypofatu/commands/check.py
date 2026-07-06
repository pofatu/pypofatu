"""
Run consistency checks on the raw/csv data.
"""


def run(args):  # pylint: disable=C0116
    args.repos.validate(log=args.log)
