import pathlib

from pypofatu import Pofatu


def test_Dataset(mocker):
    import os

    ds = Pofatu(pathlib.Path(__file__).parent / 'repos')
    bib = {rec.id: rec for rec in ds.iterbib()}
    assert len(bib) == 151
    dps = list(ds.iterdata())
    assert len(dps) == 8924
    assert len(list(ds.itercontributions())) == 41
    assert len(list(ds.itermethods())) == 1397
    assert ds.validate(log=mocker.Mock(), bib=bib) >= 1
