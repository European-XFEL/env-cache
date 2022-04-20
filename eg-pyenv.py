import sys
from pathlib import Path

from env_cache import PyenvEnvMaker, EnvsManager

if len(sys.argv) != 3:
    sys.exit("Usage: eg-pyenv.py 3.8.11 path/to/requirements.txt")

py_version, reqs_path = sys.argv[1:]
reqs = Path(reqs_path).read_text('utf-8')

envmgr = EnvsManager(Path('my-envs'), PyenvEnvMaker())
env_dir = envmgr.get_env(py_version, reqs)
