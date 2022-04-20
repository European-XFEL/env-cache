Get a Python environment for a Python version and requirements.txt file

``env_cache`` manages a collection of Python environments. You request an
environment for a specific Python version and a set of requirements (preferably
with pinned versions, like from ``pip freeze``). It can either create a new
environment with these packages, or retrieve one it already made with the same
arguments.

To get different versions of Python, ``env_cache`` can use
`pyenv <https://github.com/pyenv/pyenv>`_, `conda <https://docs.conda.io/en/latest/>`_,
or `spack <https://spack.io/>`_. It can also work with a single 'fixed' Python
interpreter to create virtualenvs - in this case, only one Python version is
available.

Usage (with pyenv):

.. code-block:: python

    import sys
    from pathlib import Path

    from env_cache import PyenvEnvMaker, EnvsManager

    if len(sys.argv) != 3:
        sys.exit("Usage: eg-pyenv.py 3.8.11 path/to/requirements.txt")

    py_version, reqs_path = sys.argv[1:]
    reqs = Path(reqs_path).read_text('utf-8')

    envmgr = EnvsManager(Path('my-envs'), PyenvEnvMaker())
    env_dir = envmgr.get_env(py_version, reqs)

It returns a `pathlib <https://docs.python.org/3/library/pathlib.html>`_ Path
object (``env_dir`` above) pointing to the environment directory. Python can
be run from ``bin/python`` within this directory.

It also records each time an environment is requested in a crude ``usage.csv``
file in the environment directory. This is meant to help with cleaning up
unused environments, but it may go away or change completely in a future version.

This package is written primarily for internal use at `European XFEL
<https://www.xfel.eu/>`_, so it's fairly rough, and we might make breaking
changes without warning.
