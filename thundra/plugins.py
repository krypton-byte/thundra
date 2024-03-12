from dataclasses import dataclass
from io import BytesIO
from os import path
from pathlib import Path
from pyoverload import overload, params, override
from typing import Any, Iterable, List, Literal, Optional, Self
import appdirs
import requests
import zipfile
import tomllib
import glob
import secrets

from .utils import workdir

from .config import write_config_toml
from .profiler import VirtualEnv

root = Path(appdirs.user_data_dir("thundra"))
extract_path = VirtualEnv.get_env().activate(workdir.workspace.__str__()).env


class Response404(Exception):
    pass


class PluginZip:
    def __init__(self, fp: BytesIO, username: str, repos: str, branch: str) -> None:
        self.username = username
        self.repos = repos
        self.branch = branch
        self.file = zipfile.ZipFile(fp)
        self.info = self.get_info()

    def get_info(self) -> dict:
        root = self.file.namelist()[0]
        return tomllib.loads(
            self.file.open(root + "thundra-plugin.toml").read().decode()
        )

    def install_dependencies(self):
        import pip

        pip.main(["install", *self.info["plugin"]["dependencies"]])

    def install_extract(self):
        self.file.extractall(extract_path / self.username)

    def install(self):
        self.install_dependencies()
        self.install_extract()
        from .config import config_toml

        name = self.username + "-" + self.file.namelist()[0].strip("/")
        config_toml["plugins"][name] = {
            "username": self.username,
            "repository": self.repos,
            "branch": self.branch,
        }
        write_config_toml(config_toml)


@dataclass
class PluginDirType:
    type: Literal["command", "agent", "middleware"] | str
    dirs: List[str]


@dataclass
class Plugin:
    name: str
    author: str
    branch: str
    dependencies: List[str]
    version: str
    includes: List[PluginDirType]
    path: Path

    def stringify(self):
        return (
            f"name: {self.name}\nauthor: {self.author}\nbranch: {self.branch}\nversion: {self.version}\ndependencies: \n\t-"
            + "\n\t-".join(self.dependencies)
        )

    @classmethod
    def find_full_args(cls, author: str, name: str, branch: str) -> Self:
        with open(
            extract_path / author / f"{name}-{branch}" / "thundra-plugin.toml"
        ) as file:
            config = tomllib.loads(file.read())
            plugin = cls(
                name=config["plugin"]["name"],
                author=config["plugin"]["author"],
                branch=branch,
                dependencies=config["plugin"]["dependencies"],
                version=config["plugin"]["version"],
                includes=[],
                path=extract_path / author / f"{name}-{branch}",
            )
            for plugin_type in ["command", "agent", "middleware"]:
                val = config["plugin"].get(plugin_type)
                if isinstance(val, list):
                    plugin.includes.append(PluginDirType(plugin_type, val))
            return plugin

    @classmethod
    def find_by_author_and_name(cls, author: str, name: str) -> Iterable[Self]:
        g = f"{extract_path}/{author}/{name}-*"
        for full_path in glob.glob(g):
            yield cls.find_full_args(author, name, full_path[len(g) - 1 :])

    @classmethod
    def find_by_author(cls, author: str) -> Iterable[Self]:
        g = Path(f"{extract_path}/{author}/")
        for full_path in g.iterdir():
            if full_path.is_dir():
                yield from cls.find_by_author_and_name(
                    author, "-".join(full_path.name.split("-")[:-1])
                )
        yield from []

    @classmethod
    def get_all_plugins(cls):
        g = Path(f"{extract_path}/")
        for full_path in g.iterdir():
            if full_path.is_dir():
                yield from cls.find_by_author(full_path.name)
        yield from []


class PluginSource(requests.Session):
    def __init__(self, username: str, repository: str) -> None:
        super().__init__()
        self.git_username = username
        self.repository = repository

    def latest_version(self) -> dict:
        req = self.get(
            f"https://api.github.com/repos/{self.git_username}/{self.repository}/releases"
        )
        if req.status_code == 200:
            return req.json()[0]
        raise Response404()

    def download_release(self, version: str) -> PluginZip:
        req = requests.get(
            f"https://github.com/{self.git_username}/{self.repository}/archive/refs/tags/{version}.zip"
        )
        if req.status_code == 200:
            return PluginZip(
                BytesIO(req.content), self.git_username, self.repository, version
            )
        raise Response404(version)

    def download_head(self, branch: str) -> PluginZip:
        req = requests.get(
            f"https://github.com/{self.git_username}/{self.repository}/archive/refs/heads/{branch}.zip"
        )
        if req.status_code == 200:
            return PluginZip(
                BytesIO(req.content), self.git_username, self.repository, branch
            )
        raise Response404(branch)

    def branch(self) -> List:
        return requests.get(
            f"https://api.github.com/repos/{self.git_username}/{self.repository}/branches"
        ).json()
