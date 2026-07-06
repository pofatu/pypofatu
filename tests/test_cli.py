from pypofatu.__main__ import main


def test_help(capsys):
    main([])
    out, _ = capsys.readouterr()
    assert 'usage' in out


def test_workflow(tmprepos, capsys):
    main(['--repos', str(tmprepos), 'check'])
    main(['--repos', str(tmprepos), 'dist'])
    assert tmprepos.joinpath('dist').exists()
    assert 'fractionationcorrection' in tmprepos.joinpath('dist', 'methods.csv').read_text()
    capsys.readouterr()
    main(['--repos', str(tmprepos), 'paramstats'])
    out, _ = capsys.readouterr()
    assert 'ppm' in out
    main(['--repos', str(tmprepos), 'query', '.schema'])
    out, _ = capsys.readouterr()
    assert 'samples.csv' in out
    main(['--repos', str(tmprepos), 'query', 'select count(*) from "methods.csv"'])
    out, _ = capsys.readouterr()
    assert '13' in out
