import pytest

from pypofatu.util import *


@pytest.mark.parametrize(
    'in_,out',
    [
        ('NA', None),
        ('*', None),
        ('1.5,', 1.5),
    ]
)
def test_almost_float(in_, out):
    if isinstance(out, float):
        assert almost_float(in_) == pytest.approx(out)
    else:
        assert almost_float(in_) == out