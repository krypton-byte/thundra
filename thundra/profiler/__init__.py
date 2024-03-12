from dataclasses import dataclass
from os import path
from pathlib import Path
import secrets
from typing import Dict, List
import tomllib
import appdirs
import json

from ..evaluater import evaluate_module
from ..utils import workdir

APP_DATA = Path(appdirs.user_data_dir("thundra"))
if not APP_DATA.exists():
    APP_DATA.mkdir()


class ProfileNotExist(Exception):
    pass


VENV_CONFIG = APP_DATA / "env.json"
if not VENV_CONFIG.exists():
    open(VENV_CONFIG, "w").write("[]")
PLUGINS_PATH = APP_DATA / "plugins"
if not PLUGINS_PATH.exists():
    PLUGINS_PATH.mkdir()


class EnvNotExist(Exception):
    pass


@dataclass
class Env:
    workspace: Path
    env: Path

    def __post_init__(self):
        if not self.env.exists():
            self.env.mkdir()


class VirtualEnv(Dict[str, str]):
    def save(self):
        with open(VENV_CONFIG, "w") as file:
            file.write(json.dumps(self))

    @classmethod
    def get_env(cls):
        return cls(json.loads(open(VENV_CONFIG, "r").read()))

    def activate(
        self, workspace: str, autocreate: bool = True, load_plugin: bool = True
    ) -> Env:
        env_str = self.get(workspace)
        env = None
        if isinstance(env_str, str):
            if not Path(env_str).exists():
                Path(env_str).mkdir(parents=True)
            env = Env(workspace=Path(workspace), env=Path(env_str))
        if env_str is None:
            if autocreate:
                env = Env(
                    workspace=workdir.workspace,
                    env=PLUGINS_PATH
                    / f"{workdir.workspace.name}-{secrets.token_urlsafe(5)}",
                )
                self[workspace] = env.env.__str__()
                self.save()
        if env:
            if load_plugin:
                evaluate_module(env.env, env.env)
            return env
        raise EnvNotExist()


@dataclass
class Profile:
    workspace: str
    phonenumber: str
    pushname: str
    duplicate_count: int = 0

    def __post_init__(self) -> None:
        with open(self.workspace + "/thundra.toml") as file:
            self.conf = tomllib.loads(file.read())

    def get_id(self) -> str:
        return self.get_name().replace(" ", "_") + (
            f"#{self.duplicate_count}" if self.duplicate_count else ""
        )

    def get_name(self) -> str:
        return self.conf["thundra"]["name"]

    def db_exist(self):
        return (Path(self.workspace) / self.conf["thundra"]["db"]).exists()

    def db_path(self):
        return f"{self.workspace}/{self.conf['thundra']['db']}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(workspace=%r, id=%r,name=%r, author=%r)" % (
            self.workspace,
            self.get_id(),
            self.conf["thundra"]["name"],
            self.conf["thundra"]["author"],
        )


class Profiler(List[Profile]):
    dir_path = Path(appdirs.user_data_dir("thundra"))
    path = dir_path / "profile.json"

    @classmethod
    def add_profile(cls, profile: Profile):
        if not cls.dir_path.exists():
            cls.dir_path.mkdir()
        if cls.path.exists():
            data = json.loads(open(cls.path, "r").read())
        else:
            data = {}
        if profile.workspace not in data:
            data.update(
                {
                    profile.workspace: {
                        "phonenumber": profile.phonenumber,
                        "pushname": profile.pushname,
                    }
                }
            )
            with open(cls.path, "w") as file:
                json.dump(data, file)

    def save(self):
        with open(self.path, "w") as file:
            json.dump(
                {
                    profile.workspace: {
                        "phonenumber": profile.phonenumber,
                        "pushname": profile.pushname,
                    }
                    for profile in self
                },
                file,
            )

    @classmethod
    def get_profiler(cls):
        names = []
        profiles = []
        if not cls.path.exists():
            return cls()
        for key, val in json.loads(open(cls.path, "r").read()).items():
            args = {"workspace": key, **val}
            profile = Profile(**args)
            profile.duplicate_count = names.count(profile.get_name())
            names.append(profile.get_name())
            profiles.append(profile)
        return cls(
            [
                Profile(**{"workspace": key, **val})
                for key, val in json.loads(open(cls.path, "r").read()).items()
            ]
        )

    def delete_profile(self, *alias: str):
        new_list = [profile for profile in self if profile.get_id() not in alias]
        if len(new_list) != len(self):
            Profiler(new_list).save()

    def get_profile(self, alias: str) -> Profile:
        for profile in self:
            if profile.get_id() == alias:
                return profile
        raise ProfileNotExist()
