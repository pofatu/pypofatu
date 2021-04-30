import shutil
import pathlib

import pytest


@pytest.fixture
def tmprepos(tmp_path):
    shutil.copytree(pathlib.Path(__file__).parent / 'repos', tmp_path / 'repos')
    return tmp_path / 'repos'
