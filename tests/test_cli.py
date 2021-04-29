from pypofatu.__main__ import main


def test_help(capsys):
    main([])
    out, _ = capsys.readouterr()
    assert 'usage' in out
