"""Get a Python environment for a Python version and requirements.txt file"""
import abc
import csv
import getpass
import re
import socket
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from shutil import rmtree, which
from subprocess import run, PIPE
from tempfile import mkdtemp

__version__ = "0.1"


class EnvMaker(abc.ABC):
    @abc.abstractmethod
    def describe(self, py_version) -> str:
        """Make a description of this Python version, to go in requirements.txt"""
        pass

    @abc.abstractmethod
    def make_env(self, env_dir, py_version):
        """Create a new environment with the given Python version"""
        pass


class FixedPythonEnvMaker(EnvMaker):
    def __init__(self, python_exe):
        self.python_exe = which(python_exe)
        self.version = self._get_version()

    def _get_version(self):
        res = run([self.python_exe, '--version'], check=True, stdout=PIPE)
        m = re.match("Python\s+(\S+)$", res.stdout.decode('utf-8'))
        if not m:
            raise ValueError(
                f"python --version output ({res.stdout}) not as expected"
            )
        return m[1]

    def _check_version(self, version):
        if version != self.version:
            raise ValueError(f"Specified Python is {self.version}, not {version}")

    def describe(self, py_version):
        self._check_version(py_version)
        return f"{py_version} ({self.python_exe})"

    def make_env(self, in_dir, py_version):
        self._check_version(py_version)
        run([self.python_exe, '-m', 'venv', '--clear', in_dir], check=True)


class PyenvEnvMaker(EnvMaker):
    def __init__(self, pyenv_exe='pyenv'):
        self.pyenv_exe = pyenv_exe

    def describe(self, py_version) -> str:
        return f"{py_version} from pyenv"

    def make_env(self, env_dir, py_version):
        run([
            self.pyenv_exe, 'install', '--skip-existing', py_version
        ], check=True)
        py_prefix = run([
            self.pyenv_exe, 'prefix', py_version
        ], check=True, stdout=PIPE).stdout.decode('utf-8').strip()
        python_exe = Path(py_prefix, 'bin', 'python')
        run([python_exe, '-m', 'venv', '--clear', env_dir], check=True)


class CondaEnvMaker(EnvMaker):
    def __init__(self, conda_exe='conda'):
        self.conda_exe = conda_exe

    def describe(self, py_version):
        return f"{py_version} from conda"

    def make_env(self, in_dir, py_version):
        run([
            self.conda_exe, 'create', '-yp', in_dir, f"python={py_version}"
        ], check=True)


class SpackEnvMaker(EnvMaker):
    def __init__(self, spack_exe='spack'):
        self.spack_exe = spack_exe

    def describe(self, py_version) -> str:
        return f"{py_version} from spack"

    def make_env(self, env_dir, py_version):
        run([
            self.spack_exe, 'install', f'python@{py_version}'
        ], check=True)
        find_results = run([
            self.spack_exe, 'find', '-p', f'python@{py_version}'
        ], check=True, stdout=PIPE).stdout.decode('utf-8')
        py_prefix = [
            l for l in find_results.splitlines()
            if l.startswith('python@')
        ][0].split()[-1]
        python_exe = Path(py_prefix, 'bin', 'python')
        run([python_exe, '-m', 'venv', '--clear', env_dir], check=True)


class EnvsManager:
    def __init__(self, path: Path, env_maker: EnvMaker):
        self.path = path
        self.env_maker = env_maker

        (path / '.envs').mkdir(parents=True, exist_ok=True)

    def reqs_w_python(self, reqs: str, py_version):
        if reqs.startswith("# Python: "):
            reqs = reqs.partition('\n')[2]
        return f"# Python: {self.env_maker.describe(py_version)}\n{reqs}"

    def delete_env(self, reqs_hash: str):
        env_dir = self.path / reqs_hash
        real_env_dir = env_dir.resolve()
        env_dir.unlink()
        rmtree(real_env_dir)

    def get_env(self, py_version, reqs: str):
        reqs = self.reqs_w_python(reqs, py_version)
        reqs_hash = sha256(reqs.encode('utf-8')).hexdigest()[:12]
        env_dir = self.path / reqs_hash
        if env_dir.is_dir():
            print("Using existing environment", env_dir)
            with (env_dir / 'usage.csv').open('a', encoding='utf-8') as f:
                csv.writer(f).writerow(usage_record())
            return env_dir

        # Create the environment, but don't expose it using the hash of
        # requirements.txt until we've installed packages. This should prevent
        # anyone trying to use a half-created environment.
        real_env_dir = Path(mkdtemp(
            dir=(self.path / '.envs'), prefix=f'py-{py_version}-'
        )).resolve()
        print(f"Creating new environment at {real_env_dir}...")
        self.env_maker.make_env(real_env_dir, py_version)
        try:
            reqs_txt = real_env_dir / 'requirements.txt'
            reqs_txt.write_text(reqs, 'utf-8')
            print("Installing packages with pip....")
            env_python = real_env_dir / 'bin' / 'python'
            run([env_python, '-m', 'pip', 'install', '-r', reqs_txt], check=True)
            new_link = real_env_dir.with_suffix('.link')
            new_link.symlink_to(real_env_dir)
            new_link.replace(env_dir)
        except:
            print("Error creating, removing...")
            rmtree(real_env_dir)
            raise

        print(f"Linked new environment as {env_dir}")

        with (env_dir / 'usage.csv').open('w', encoding='utf-8') as f:
            cw = csv.writer(f)
            cw.writerow(['timestamp', 'user', 'hostname'])
            cw.writerow(usage_record())

        return env_dir


def usage_record():
    """Make one row for usage.csv"""
    return [
        datetime.now(tz=timezone.utc).isoformat(),
        getpass.getuser(),
        socket.gethostname(),
    ]


if __name__ == '__main__':
    reqs_txt = Path(sys.argv[1])
    fixed_py = FixedPythonEnvMaker('python3')
    print("Fixed Python version:", fixed_py.version)
    EnvsManager(Path('my-envs'), fixed_py).get_env(
        fixed_py.version, reqs_txt.read_text('utf-8')
    )
