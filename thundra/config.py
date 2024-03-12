from dataclasses import dataclass
from typing import Optional, Dict
import tomllib, os
import tomli_w
from .utils import workdir

with open(workdir.workspace / "thundra.toml", "r") as file:
    config_toml = tomllib.loads(file.read())


def write_config_toml(config: dict):
    with open(workdir.workspace / "thundra.toml", "wb") as file:
        tomli_w.dump(config, file)


def config_format(config: Optional[Dict] = None, path="") -> dict:
    result = {}
    if config is None:
        with open(workdir.workspace / "thundra.toml", "r") as file:
            config = tomllib.loads(file.read())
    for k, v in config.items():
        if isinstance(v, dict):
            result.update(config_format(v, path=path + k + "." if path else k + "."))
        elif isinstance(v, list):
            result.update({f"{path}{k}[{i}]": val for i, val in enumerate(v)})
        else:
            result.update({f"{path}{k}": v})
    return result


@dataclass
class Config:
    prefix: str = "."


config = Config()
