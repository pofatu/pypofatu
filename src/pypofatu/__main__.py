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
    ds = args.repos
    dps = list(ds.iterdata())
    assert len(dps) == 4347
    assert len(list(ds.iterreferences())) == 106
    assert len(list(ds.itercontributions())) == 30
    assert len(list(ds.itermethods())) == 1384


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
