from __future__ import annotations
from dataclasses import dataclass
from os import path
from pathlib import Path
import secrets
from typing import Dict, List
import tomllib
import appdirs
import json

from ..evaluater import evaluate_module

APP_DATA = Path(appdirs.user_data_dir("thundra"))
if not APP_DATA.exists():
    APP_DATA.mkdir(parents=True, exist_ok=True)


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
    """
    Represents a virtual environment configuration.

    This class extends a dictionary to store virtual environment configurations.
    It provides methods for saving, loading, and activating virtual environments.

    Example usage:

    ```python
    env = VirtualEnv.get_env()
    env.activate(workspace="my_workspace")
    ```

    """

    def save(self):
        """
        Save the virtual environment configuration to a file.

        This method saves the virtual environment configuration to a JSON file.

        """

        with open(VENV_CONFIG, "w") as file:
            file.write(json.dumps(self))

    @classmethod
    def get_env(cls) -> "VirtualEnv":
        """
        Get the virtual environment configuration.

        This method loads the virtual environment configuration from a file.

        :return: Virtual environment configuration.
        :rtype: VirtualEnv

        """
        return cls(json.loads(open(VENV_CONFIG, "r").read()))

    def activate(
        self, workspace: str, autocreate: bool = True, load_plugin: bool = True
    ) -> Env:
        """
        Activate a virtual environment.

        This method activates a virtual environment based on the provided workspace.
        If the virtual environment does not exist, it can be automatically created.

        :param workspace: Name of the workspace.
        :type workspace: str
        :param autocreate: Whether to create the virtual environment if it does not exist, defaults to True
        :type autocreate: bool, optional
        :param load_plugin: Whether to load plugins in the virtual environment, defaults to True
        :type load_plugin: bool, optional
        :raises EnvNotExist: If the virtual environment does not exist and autocreate is False.
        :return: Activated virtual environment.
        :rtype: Env

        """

        env_str = self.get(workspace)
        env = None

        if isinstance(env_str, str):
            if not Path(env_str).exists():
                Path(env_str).mkdir(parents=True)
            env = Env(workspace=Path(workspace), env=Path(env_str))

        if env_str is None:
            from ..workdir import workdir

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
    """
    Represents a user profile.

    This class stores information about a user's workspace, phone number, push name, and duplicate count.
    It provides methods to retrieve profile details and check the existence of a database associated with the profile.

    Example usage:

    ```python
    profile = Profile(workspace="my_workspace", phonenumber="123456789", pushname="John Doe")
    print(profile.get_id())  # Output: John_Doe
    print(profile.get_name())  # Output: My_Profile
    ```

    """

    workspace: str
    phonenumber: str
    pushname: str
    duplicate_count: int = 0

    def __post_init__(self) -> None:
        """
        Initialize the profile object.

        This method reads the Thundra configuration file for the workspace and loads its contents into the profile.

        """
        with open(Path(self.workspace) / "thundra.toml") as file:
            self.conf: Dict = tomllib.loads(file.read())

    def get_id(self) -> str:
        """
        Get the profile ID.

        This method constructs the profile ID based on the push name and duplicate count.

        :return: Profile ID.
        :rtype: str

        """
        return self.get_name().replace(" ", "_") + (
            f"#{self.duplicate_count}" if self.duplicate_count else ""
        )

    def get_name(self) -> str:
        """
        Get the profile name.

        This method retrieves the profile name from the Thundra configuration.

        :return: Profile name.
        :rtype: str

        """
        return self.conf["thundra"]["name"]

    def db_exist(self) -> bool:
        """
        Check if the database exists.

        This method checks whether the database associated with the profile exists in the workspace.

        :return: True if the database exists, False otherwise.
        :rtype: bool

        """
        return (Path(self.workspace) / self.conf["thundra"]["db"]).exists()

    def db_path(self) -> str:
        """
        Get the path to the database.

        This method returns the path to the database associated with the profile.

        :return: Path to the database.
        :rtype: str

        """
        return f"{self.workspace}/{self.conf['thundra']['db']}"

    def __repr__(self) -> str:
        """
        Return a string representation of the profile.

        This method returns a string containing the workspace, ID, name, and author of the profile.

        :return: String representation of the profile.
        :rtype: str

        """
        return f"{self.__class__.__name__}(workspace=%r, id=%r,name=%r, author=%r)" % (
            self.workspace,
            self.get_id(),
            self.conf["thundra"]["name"],
            self.conf["thundra"]["author"],
        )


from typing import List
from pathlib import Path
import appdirs
import json


class Profiler(List[Profile]):
    """
    Represents a list of user profiles.

    This class provides methods to add, save, retrieve, and delete user profiles.

    Example usage:

    ```python
    profiler = Profiler.get_profiler()
    profiler.add_profile(Profile(workspace="my_workspace", phonenumber="123456789", pushname="John Doe"))
    profiler.save()
    ```

    """

    dir_path = Path(appdirs.user_data_dir("thundra"))
    path = dir_path / "profile.json"

    @classmethod
    def add_profile(cls, profile: Profile):
        """
        Add a new profile.

        This method adds a new profile to the profiler and saves it to the profile file.

        :param profile: Profile to be added.
        :type profile: Profile

        """
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
        """
        Save the profiles to the profile file.

        This method saves the profiles to the profile file.

        """
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
    def get_profiler(cls) -> Profiler:
        """
        Get the profiler.

        This method retrieves the profiler from the profile file.

        :return: Profiler containing user profiles.
        :rtype: Profiler

        """
        names = []
        profiles = []
        if not cls.path.exists():
            return cls()
        for key, val in json.loads(open(cls.path, "r").read()).items():
            try:
                args = {"workspace": key, **val}
                profile = Profile(**args)
                profile.duplicate_count = names.count(profile.get_name())
                names.append(profile.get_name())
                profiles.append(profile)
            except Exception:
                pass
        return cls(profiles)

    def delete_profile(self, *alias: str):
        """
        Delete profiles.

        This method deletes profiles from the profiler and saves the changes.

        :param alias: Aliases of profiles to be deleted.
        :type alias: str

        """
        new_list = [profile for profile in self if profile.get_id() not in alias]
        if len(new_list) != len(self):
            Profiler(new_list).save()

    def get_profile(self, alias: str) -> Profile:
        """
        Get a profile by alias.

        This method retrieves a profile from the profiler by its alias.

        :param alias: Alias of the profile.
        :type alias: str
        :raises ProfileNotExist: If the profile does not exist.
        :return: Retrieved profile.
        :rtype: Profile

        """
        for profile in self:
            if profile.get_id() == alias:
                return profile
        raise ProfileNotExist()
