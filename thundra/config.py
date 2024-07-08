from dataclasses import dataclass
import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Dict
import tomllib
from cachetools.func import ttl_cache
import tomli_w
from cachetools import cached, TTLCache


cache = TTLCache(maxsize=1024, ttl=60)


@dataclass
class Config:
    prefix: str
    owner: List[str]


@dataclass
class Workdir:
    db: Path
    config_path: Path
    workspace_dir: Optional[Path] = None
    config: Optional[Config] = None

    def write_config_toml(self, config: dict):
        """
        Writes the provided configuration dictionary to a TOML file.

        :param config: The configuration dictionary to write to the file.
        :type config: dict
        """
        with open(self.config_path, "wb") as file:
            tomli_w.dump(config, file)

    @property
    def read_config(self) -> dict:
        """
        Reads the configuration from a TOML file and returns it as a dictionary.

        :return: The configuration dictionary read from the TOML file.
        :rtype: dict
        """
        with open(self.config_path, "r") as file:
            return tomllib.loads(file.read())

    def get_config(self) -> Config:
        """
        Reads the configuration from a TOML file and returns it as a Config object.
        The result is cached to improve performance on subsequent calls.

        :return: A Config object containing the configuration data.
        :rtype: Config
        """
        if self.config is None:
            with open(self.config_path, "r") as file:
                cf_format = tomllib.loads(file.read())
                self.config = Config(
                    prefix=cf_format["thundra"]["prefix"],
                    owner=cf_format["thundra"]["owner"],
                )
        return self.config

    def config_format(self, config: Optional[Dict] = None, path="") -> dict:
        """
        Recursively formats a configuration dictionary into a flat dictionary with keys representing the
        hierarchical structure of the original dictionary.

        :param config: The configuration dictionary to format. If None, the method uses `self.read_config`.
                    Defaults to None.
        :type config: Optional[Dict], optional
        :param path: The base path for nested keys in the formatted dictionary. Defaults to an empty string.
        :type path: str, optional
        :return: A flat dictionary with keys representing the hierarchical structure of the original dictionary.
        :rtype: dict
        """
        result = {}
        if config is None:
            config = self.read_config
        for k, v in config.items():
            if isinstance(v, dict):
                result.update(
                    self.config_format(v, path=path + k + "." if path else k + ".")
                )
            elif isinstance(v, list):
                result.update({f"{path}{k}[{i}]": val for i, val in enumerate(v)})
            else:
                result.update({f"{path}{k}": v})
        return result

    @classmethod
    def find(cls, path: Path) -> "Workdir":
        """
        Finds the working directory by searching for specific configuration files
        ('thundra-dev.toml' or 'thundra.toml') in the provided path and its parent directories.

        This method traverses up the directory tree starting from the provided path, looking
        for either 'thundra-dev.toml' or 'thundra.toml' configuration files. If one of these
        files is found, a Workdir instance is created with the path of the directory containing
        the configuration file.

        :param path: The starting path from which to search for the configuration file.
        :type path: Path
        :raises TypeError: If no configuration file is found in the directory tree.
        :return: A Workdir instance with the found configuration file path.
        :rtype: Workdir
        """
        cwd = path.parts
        dir_path = path
        for i in range(len(cwd) - 1):
            if (dir_path / "thundra-dev.toml").exists():
                return Workdir(
                    db=dir_path,
                    workspace_dir=dir_path,
                    config_path=dir_path / "thundra-dev.toml",
                )
            if (dir_path / "thundra.toml").exists():
                return Workdir(
                    db=dir_path,
                    workspace_dir=dir_path,
                    config_path=dir_path / "thundra.toml",
                )
            dir_path = dir_path.parent
        raise TypeError("Workdir Not Found")

    @property
    def workspace(self) -> Path:
        """
        Returns the workspace directory if it is set; otherwise, returns the database workspace directory.

        :return: The path to the workspace directory.
        :rtype: Path
        """
        return self.workspace_dir or self.db_workspace

    @property
    def db_workspace(self) -> Path:
        """
        Returns the path to the database workspace directory.

        :return: The path to the database workspace directory.
        :rtype: Path
        """
        return self.db
