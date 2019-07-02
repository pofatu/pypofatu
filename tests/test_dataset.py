from pathlib import Path

from pypofatu import Pofatu


def test_Dataset(mocker):
    ds = Pofatu(Path(__file__).parent / 'repos')
    bib = {rec.id: rec for rec in ds.iterbib()}
    assert len(bib) == 103
    refs = list(ds.iterreferences())
    assert len(refs) == 106
    dps = list(ds.iterdata())
    assert len(dps) == 3827
    assert len(list(ds.itercontributions())) == 30
    assert len(list(ds.itermethods())) == 1032
    assert ds.validate(log=mocker.Mock()) == 46
