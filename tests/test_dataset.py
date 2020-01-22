import pathlib

from pypofatu import Pofatu


def test_Dataset(mocker):
    import os

    ds = Pofatu(pathlib.Path(__file__).parent / 'repos')
    if 'TRAVIS' not in os.environ:
        bib = {rec.id: rec for rec in ds.iterbib()}
        assert len(bib) == 103
    else:
        bib = False
    refs = list(ds.iterreferences())
    assert len(refs) == 107
    dps = list(ds.iterdata())
    assert len(dps) == 3827
    assert len(list(ds.itercontributions())) == 30
    assert len(list(ds.itermethods())) == 1032
    assert ds.validate(log=mocker.Mock(), bib=bib) == 46
