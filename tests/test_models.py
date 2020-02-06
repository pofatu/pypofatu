from pypofatu.models import *


def test_Method():
    c = Method('CODE', 'PARAM', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')
    assert c.id and c.label


def test_MethodReference():
    c = MethodReference('n', '5.5', '', '', '')
    assert 'n' in c.as_string()


def test_Measurement():
    m = Measurement(method='M', parameter='P', value=4.5, less=False, value_sd=1, sd_sigma='2')
    assert m.as_string() == '4.5±1.0 2σ'


def test_Location():
    l = Location('R', 'SR', 'L', '', 3.5, 4.5, 3)
    assert l.name and l.id and l.label

def test_Contribution():
    c = Contribution('ID', 'NAME', '', '', '', '', '', '')
    assert 'NAME' in c.label


def test_Site():
    s = Site(
        name='N',
        code='C',
        source_ids='',
        context='NATURAL',
        comment='',
        stratigraphic_position='',
        stratigraphy_comment='')
    assert s.id == 'NC'
