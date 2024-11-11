from shutil import which
from subprocess import run, PIPE, STDOUT
import sys

import pytest

from env_cache import (EnvsManager, FixedPythonEnvMaker, PyenvEnvMaker)

@pytest.mark.skipif(sys.version_info.releaselevel != 'final', reason='pre-release Python')
def test_fixed_python(tmp_path):
    vi = sys.version_info
    version = f"{vi.major}.{vi.minor}.{vi.micro}"

    mgr = EnvsManager(tmp_path, FixedPythonEnvMaker(sys.executable))
    env = mgr.get_env(version, "flit_core==3.10.1")
    assert env.is_relative_to(tmp_path)
    env_py = env / 'bin' / 'python'
    assert env_py.is_file()
    r = run([env_py, '-c', 'import flit_core'], stdout=PIPE, stderr=STDOUT)
    if r.stdout:
        print(r.stdout)
    assert r.returncode == 0

    # Asking for an env with the same specifications should reuse it
    env_again = mgr.get_env(version, "flit_core==3.10.1")
    assert env_again == env


def test_fixed_python_wrong_version(tmp_path):
    mgr = EnvsManager(tmp_path, FixedPythonEnvMaker(sys.executable))
    # Assume this test will never run on Python 3.2.1
    with pytest.raises(ValueError, match="not 3.2.1"):
        mgr.get_env("3.2.1", "")


@pytest.mark.skipif(which('pyenv') is None, reason="pyenv not available")
def test_pyenv(tmp_path):
    version = "3.11.10"
    mgr = EnvsManager(tmp_path, PyenvEnvMaker())
    env = mgr.get_env(version, "flit_core==3.10.1")
    assert env.is_relative_to(tmp_path)
    env_py = env / 'bin' / 'python'
    assert env_py.is_file()
    r = run([env_py, '-c', 'import flit_core'], stdout=PIPE, stderr=STDOUT)
    if r.stdout:
        print(r.stdout)
    assert r.returncode == 0

    # Asking for an env with the same specifications should reuse it
    env_again = mgr.get_env(version, "flit_core==3.10.1")
    assert env_again == env
