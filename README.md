# pypofatu

A python package to curate [Pofatu data](https://github.com/pofatu/pofatu-data).

[![Build Status](https://github.com/pofatu/pypofatu/workflows/tests/badge.svg)](https://github.com/pofatu/pypofatu/actions?query=workflow%3Atests)
[![PyPI](https://img.shields.io/pypi/v/pypofatu.svg)](https://pypi.org/project/pypofatu)


## Installation

Install `pypofatu` from [PyPI](https://pypi.org) running
```shell script
pip install pypofatu
```
preferably in a new [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/), to keep your system's Python installation unaffected.

Installing `pypofatu` will also install a command line program `pofatu`, which provides
functionality to curate and query Pofatu data. Run
```shell script
pofatu -h
```
for details on usage.

`pypofatu` operates on data as displayed by the [Pofatu database](https://pofatu.clld.org). This
data curated in a GitHub repository which is accessed by `pypofatu` locally. Thus, in order to use
`pypofatu` you must clone the [`pofatu/pofatu-data`](https://github.com/pofatu/pofatu-data) repository or download
a [release version](https://github.com/pofatu/pofatu-data/releases).


## Curation workflow

Check the data in the repository for consistency:
```shell
pofatu --repos PATH/TO/REPOS check
```

Create a distribution of the data:
```shell
pofatu --repos PATH/TO/REPOS dist
```

A distribution consists of
- a set of CSV files described by CSVW metadata
- an SQLite database created from the CSVW package


## Querying

Exploratory analysis of the data is possible with off-the-shelf tools such as `grep`,
`head` etc. on the UNIX shell. More accurate analysis can be done with tools that exploit the
CSV structure, e.g. the tools from the `csvkit` package. Ultimate control and performance is
possible using the SQLite database.

The `pofatu query` command provides a convenience wrapper to query the database (once it has been
created via `pofatu dist`):

Run
```shell
pofatu --repos tests/repos/ dist
pofatu --repos tests/repos/ query .schema
```
to see the SQL schema of the database or
```shell
pofatu --repos tests/repos/ query "select count(*) from 'measurements.csv'"
INFO    SQLite database at dist/pofatu.sqlite
 count(*)  
----------
 78
```
to run simple queries. More complex queries can be written as SQL to a text file and run with
```shell
cat query.sql | pofatu --repos tests/repos/ query --format pipe -
```

| sample_id | sample_category | location_region | location_subregion | location_latitude | location_longitude | TiO2 [%] | Fe2O3 [%] |
| :-------------------: | :-------------: | :-------------: | :----------------: | :---------------: | :----------------: | :------: | :-------: |
| charleux2014_Eiao-1 | SOURCE | MARQUESAS | EIAO | -8.00 | -140.70 | 4.00 | 12.80 |
| charleux2014_Eiao-101 | SOURCE | MARQUESAS | EIAO | -8.00 | -140.70 | 4.90 | 13.30 |
| charleux2014_Eiao-102 | SOURCE | MARQUESAS | EIAO | -8.00 | -140.70 | 4.40 | 14.80 |
| charleux2014_Eiao-103 | SOURCE | MARQUESAS | EIAO | -8.00 | -140.70 | 4.40 | 14.00 |

