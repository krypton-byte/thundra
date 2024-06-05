from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Literal, Self
import appdirs
import requests
import zipfile
import tomllib
import glob
import shutil
from .workdir import workdir, config_toml
from .profiler import VirtualEnv

root = Path(appdirs.user_data_dir("thundra"))
extract_path = VirtualEnv.get_env().activate(workdir.workspace.__str__()).env


class Response404(Exception):
    """Raised when a 404 response is encountered."""
    pass


class PluginZip:
    def __init__(
        self, fp: BytesIO, username: str, repos: str, branch: str, sha: str
    ) -> None:
        """
        Initializes the PluginZip object.

        :param fp: A BytesIO object containing the plugin ZIP file.
        :type fp: BytesIO
        :param username: The username of the plugin's author.
        :type username: str
        :param repos: The name of the plugin's repository.
        :type repos: str
        :param branch: The branch from which the plugin is downloaded.
        :type branch: str
        :param sha: The SHA hash of the plugin.
        :type sha: str
        """    
        self.username = username
        self.repos = repos
        self.branch = branch
        self.sha = sha
        self.file = zipfile.ZipFile(fp)
        self.info = self.get_info()

    def get_info(self) -> Dict[str, Any]:
        """
        Retrieves information about the plugin from its ZIP file.

        :return: Information about the plugin.
        :rtype: dict
        """        
        root = self.file.namelist()[0]
        return tomllib.loads(
            self.file.open(root + "thundra-plugin.toml").read().decode()
        )

    def install_dependencies(self):
        """
        Installs the plugin's dependencies using pip.
        """        
        import pip
        pip.main(["install", *self.info["plugin"]["dependencies"]])

    def install_extract(self):
        """
        Extracts the contents of the plugin ZIP file.
        """        
        self.file.extractall(extract_path / self.username)

    def install(self):
        """
        Installs the plugin by installing dependencies and extracting its contents.
        """        
        duplicate = list(Plugin.find_by_author_and_name(self.username, self.repos))
        self.install_dependencies()
        self.install_extract()
        name = self.username + "-" + self.repos
        if not config_toml.get("plugins"):
            config_toml["plugins"] = {}
        config_toml["plugins"][name] = {
            "username": self.username,
            "repository": self.repos,
            "sha": self.sha,
            "branch": self.branch,
        }
        workdir.write_config_toml(config_toml)
        for lib in duplicate:
            if (
                self.username != lib.path.parent.name
                and self.repos != lib.repo_name
                and self.sha != lib.sha
            ):
                lib.uninstall()


@dataclass
class PluginDirType:
    type: Literal["command", "agent", "middleware"] | str
    dirs: List[str]


@dataclass
class Plugin:
    name: str
    author: str
    sha: str
    dependencies: List[str]
    version: str
    includes: List[PluginDirType]
    path: Path

    def stringify(self) -> str:
        """
        Converts the plugin information into a string.

        :return: A string representation of the plugin.
        :rtype: str
        """        
        return (
            f"name: {self.name}\nauthor: {self.author}\nsha: {self.sha}\nversion: {self.version}\ndependencies: \n\t-"
            + "\n\t-".join(self.dependencies)
        )

    def uninstall(self):
        """
        Uninstalls the plugin by removing its directory and updating the configuration file.
        """        
        shutil.rmtree(self.path)
        name = self.path.parent.name + "-" + self.repo_name
        config_toml["plugins"].pop(name)
        workdir.write_config_toml(config_toml)

    @classmethod
    def find_full_args(cls, author: str, name: str, sha: str) -> Self:
        """
        Finds a plugin with the specified author, name, and SHA hash.

        :param author: The author of the plugin.
        :type author: str
        :param name: The name of the plugin.
        :type name: str
        :param sha: The SHA hash of the plugin.
        :type sha: str
        :return: A Plugin object.
        :rtype: Self
        """        
        with open(
            extract_path / author / f"{name}-{sha}" / "thundra-plugin.toml"
        ) as file:
            config = tomllib.loads(file.read())
            plugin = cls(
                name=config["plugin"]["name"],
                author=config["plugin"]["author"],
                sha=sha,
                dependencies=config["plugin"]["dependencies"],
                version=config["plugin"]["version"],
                includes=[],
                path=extract_path / author / f"{name}-{sha}",
            )
            for plugin_type in ["command", "agent", "middleware"]:
                val = config["plugin"].get(plugin_type)
                if isinstance(val, list):
                    plugin.includes.append(PluginDirType(plugin_type, val))
            return plugin

    @property
    def repo_name(self) -> str:
        """
        Retrieves the name of the plugin's repository.

        :return: The name of the repository.
        :rtype: str
        """        
        return re.search(r"(.*)\-(\w+)", self.path.name).group(1)  # type: ignore

    @classmethod
    def find_by_author_and_name(cls, author: str, name: str) -> Iterable[Self]:
        """
        Finds plugins by author and name.

        :param author: The author of the plugins.
        :type author: str
        :param name: The name of the plugins.
        :type name: str
        :return: An iterable of Plugin objects.
        :rtype: Iterable[Self]
        """        
        g = f"{extract_path}/{author}/{name}-*"
        for full_path in glob.glob(g):
            branch = re.search(r"(.*)\-(\w+)", full_path.split("/")[-1])
            if branch:
                yield cls.find_full_args(author, name, branch.group(2))

    @classmethod
    def find_by_author(cls, author: str) -> Iterable[Self]:
        """
        Finds plugins by author.

        :param author: The author of the plugins.
        :type author: str
        :return: An iterable of Plugin objects.
        :rtype: Iterable[Self]
        :yield: Each found Plugin object.
        :rtype: Iterator[Iterable[Self]]
        """        
        g = Path(f"{extract_path}/{author}/")
        for full_path in g.iterdir():
            if full_path.is_dir():
                yield from cls.find_by_author_and_name(
                    author, "-".join(full_path.name.split("-")[:-1])
                )
        yield from []

    @classmethod
    def get_all_plugins(cls):
        """
        Retrieves all plugins.

        :yield: Each found Plugin object.
        :rtype: _type_
        """        
        g = Path(f"{extract_path}/")
        for full_path in g.iterdir():
            if full_path.is_dir():
                yield from cls.find_by_author(full_path.name)
        yield from []


class PluginSource(requests.Session):
    def __init__(self, username: str, repository: str) -> None:
        """
        Initializes a PluginSource object.

        :param username: The username of the repository owner.
        :type username: str
        :param repository: The name of the repository.
        :type repository: str
        """        
        super().__init__()
        self.git_username = username
        self.repository = repository

    def latest_version(self) -> Dict:
        """
        Retrieves information about the latest version of the repository.

        :raises Response404: If the repository does not exist or has no releases.
        :return: Information about the latest version.
        :rtype: dict
        """        
        req = self.get(
            f"https://api.github.com/repos/{self.git_username}/{self.repository}/releases"
        )
        if req.status_code == 200:
            return req.json()[0]
        raise Response404()

    def download_head(self, branch: str) -> PluginZip:
        """
        Downloads the latest version of the repository from the specified branch.

        :param branch: The branch name.
        :type branch: str
        :raises Response404: If the branch does not exist.
        :return: A PluginZip object representing the downloaded plugin.
        :rtype: PluginZip
        """        
        req = requests.get(
            f"https://github.com/{self.git_username}/{self.repository}/archive/refs/heads/{branch}.zip"
        )
        if req.status_code == 200:
            return PluginZip(
                BytesIO(req.content),
                self.git_username,
                self.repository,
                self.get_last_commit_sha(branch),
                branch,
            )
        raise Response404(branch)

    def branch(self) -> List:
        """
        Retrieves a list of branches in the repository.

        :return: A list of branches.
        :rtype: List
        """        
        return requests.get(
            f"https://api.github.com/repos/{self.git_username}/{self.repository}/branches"
        ).json()

    def get_last_commit_sha(self, branch: str) -> str:
        """
        Retrieves the SHA hash of the last commit on the specified branch.

        :param branch: The branch name.
        :type branch: str
        :return: The SHA hash of the last commit.
        :rtype: str
        """        
        data = self.get(
            f"https://api.github.com/repos/{self.git_username}/{self.repository}/commits/{branch}"
        ).json()
        print(
            "[!] last update date %s by @%s"
            % (
                datetime.fromisoformat(data["commit"]["author"]["date"]).strftime("%D"),
                data["commit"]["author"]["name"],
            )
        )
        return data["sha"]

    def download_from_sha(self, sha: str, branch: str) -> PluginZip:
        """
        Downloads a plugin from a specific commit SHA on a branch.

        :param sha: The commit SHA.
        :type sha: str
        :param branch: The branch name.
        :type branch: str
        :return: A PluginZip object representing the downloaded plugin.
        :rtype: PluginZip
        """        
        return PluginZip(
            BytesIO(
                self.get(
                    f"https://codeload.github.com/{self.git_username}/{self.repository}/zip/{sha}"
                ).content
            ),
            self.git_username,
            self.repository,
            branch,
            sha,
        )

