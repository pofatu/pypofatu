from pypofatu.__main__ import main


def test_help(capsys):
    main([])
    out, _ = capsys.readouterr()
    assert 'usage' in out


def test_workflow(tmprepos):
    main(['--repos', str(tmprepos), 'dump'])
    assert tmprepos.joinpath('csv').exists()
    main(['--repos', str(tmprepos), 'check'])
    main(['--repos', str(tmprepos), 'dist'])
    assert tmprepos.joinpath('dist').exists()
