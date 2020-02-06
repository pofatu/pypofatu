from pypofatu.__main__ import main


def test_help(capsys):
    main([])
    out, _ = capsys.readouterr()
    assert 'usage' in out


def test_workflow(tmprepos, capsys):
    main(['--repos', str(tmprepos), 'dump'])
    assert len(list((tmprepos / 'csv').glob('*.csv'))) == 5

    main(['--repos', str(tmprepos), 'check'])
    out, _ = capsys.readouterr()
    assert not out

    main(['--repos', str(tmprepos), 'paramstats'])
    out, _ = capsys.readouterr()
    assert 'median' in out

    main(['--repos', str(tmprepos), 'dist'])
    assert (tmprepos / 'dist' / 'pofatu.sqlite').exists()

    main(['--repos', str(tmprepos), 'query', '.schema'])
    out, _ = capsys.readouterr()
    assert 'CREATE' in out

    main(['--repos', str(tmprepos), 'query', 'select id, sample_name from "samples.csv"'])
    out, _ = capsys.readouterr()
    assert 'Charleux-2014-JPA_Eiao-1' in out
