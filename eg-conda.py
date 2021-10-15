import sys
from pathlib import Path

from env_cache import CondaEnvMaker, EnvsManager

if len(sys.argv) != 3:
    sys.exit("Usage: eg-conda.py 3.8.11 path/to/requirements.txt")

py_version, reqs_path = sys.argv[1:]
envmgr = EnvsManager(Path('my-envs'), CondaEnvMaker())
envmgr.get_env(py_version, Path(reqs_path).read_text('utf-8'))
