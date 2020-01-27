import shutil
import pathlib

import pytest


@pytest.fixture
def tmprepos(tmpdir):
    shutil.copytree(str(pathlib.Path(__file__).parent / 'empty_repos'), str(tmpdir.join('repos')))
    return pathlib.Path(str(tmpdir)) / 'repos'
