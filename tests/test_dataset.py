import logging

import pytest

from pypofatu.dataset import Pofatu


@pytest.fixture
def dataset(tmprepos):
    return Pofatu(tmprepos)


def test_Dataset_iterbib(dataset):
    assert list(dataset.iterbib())


def test_Dataset_validate(dataset, caplog):
    with caplog.at_level(logging.INFO):
        dataset.validate(log=logging.getLogger(__name__))
    assert len(caplog.records) == 1

    dataset.bib_path.write_text('', encoding='utf8')
    with caplog.at_level(logging.INFO):
        dataset.validate(log=logging.getLogger(__name__))
    assert len(caplog.records) == 20
