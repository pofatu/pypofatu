# pypofatu

A python package to curate [Pofatu data](https://github.com/pofatu/pofatu-data).

[![Build Status](https://travis-ci.org/pofatu/pypofatu.svg?branch=master)](https://travis-ci.org/pofatu/pypofatu)
[![codecov](https://codecov.io/gh/pofatu/pypofatu/branch/master/graph/badge.svg)](https://codecov.io/gh/pofatu/pypofatu)
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

`pypofatu` operates on data of the [Pofatu database](https://pofatu.clld.org). This
data is accessed locally. Thus, in order to use `pypofatu` you must clone the
[`pofatu/pofatu-data`](https://github.com/pofatu/pofatu-data) repository or download
a [release version](https://github.com/pofatu/pofatu-data/releases).
