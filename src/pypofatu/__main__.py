import sys

from clldutils.clilib import ArgumentParserWithLogging, command

from pypofatu import Pofatu


@command()
def stats(args):
    locs = set(dp.location.name for dp in args.repos.iterdata())
    for loc in sorted(locs):
        print(loc)
    print('{0} locations'.format(len(locs)))


@command()
def check(args):
    args.repos.validate(log=args.log)


@command()
def dump(args):
    args.repos.dump_sheets(args.args[0] if args.args else 'Pofatu Dataset.xlsx')


def main():  # pragma: no cover
    parser = ArgumentParserWithLogging('pypofatu')
    parser.add_argument(
        '--repos',
        type=Pofatu,
        default=Pofatu('pofatu-data'),
        help='Location of clone of pofatu/pofatu-data (defaults to ./pofatu-data)')
    sys.exit(parser.main())


if __name__ == '__main__':
    main()
