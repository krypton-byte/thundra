from subprocess import call
from pathlib import Path
import shlex
workdir = Path(__file__).parent.parent
call(shlex.split("sphinx-apidoc -o docs/source thundra thundra.core thundra.profiler thundra.storage"))
call(shlex.split("make html"), cwd=workdir / "docs")