from pathlib import Path
from .config import Workdir
import os

if os.environ.get("IGNORE_WORKDIR", "").lower() in ["1", "true"]:
    workdir = Workdir(db=Path("."), config_path=Path("."), workspace_dir=Path("."))
    config_toml = {"thundra": {}}
else:
    workdir = Workdir.find(Path(os.getcwd()))
    config_toml = workdir.read_config
