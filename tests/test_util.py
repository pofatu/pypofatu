import pytest

from pypofatu.util import *


@pytest.mark.parametrize(
    'in_,out',
    [
        ('1.00', '1'),
        ('1.01', '1.01'),
        ('x', 'x'),
    ]
)
def test_fix_excel_ints(in_, out):
    assert fix_excel_ints(in_) == out


@pytest.mark.parametrize(
    'in_,out',
    [
        ('NA', None),
        ('*', None),
        ('', None),
        ('1.5,', 1.5),
    ]
)
def test_almost_float(in_, out):
    if isinstance(out, float):
        assert almost_float(in_) == pytest.approx(out)
    else:
        assert almost_float(in_) == out


@pytest.mark.parametrize(
    'in_,out',
    [
        ('1', (1, False)),
        ('<1.0', (1, True)),
    ]
)
def test_parse_value(in_, out):
    assert parse_value(in_) == out


def test_callcount():
    @callcount
    def f():
        pass

    f()
    assert f.callcount == 1
