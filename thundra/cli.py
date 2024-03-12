from pathlib import Path
from typing import List
from neonize.client import re
from tomli_w import dumps

import argparse, os
import tomllib
import shutil
import sys
import os

from thundra.profiler import Profiler, VirtualEnv


arg = argparse.ArgumentParser()
action = arg.add_subparsers(title="action", dest="action", required=True)
action.add_parser("install")
create = action.add_parser(name="create")
create.add_argument("--name", type=str, nargs=1)

run = action.add_parser(name="run")
run.add_argument(
    "--phone-number", type=str, help="using pairphone as authentication, default qr"
)
run.add_argument("--workspace", type=str, help="Profile ID of workspace")
run.add_argument("--db", type=str, help="Profile ID of db")
run.add_argument("--push-notification", action="store_true", default=False)
test = action.add_parser(name="test")

plugins = action.add_parser("plugin")
types = plugins.add_subparsers(title="type", dest="plugin_action", required=True)
plugin_install = types.add_parser("install")
plugin_uninstall = types.add_parser("uninstall")
plugin_install.add_argument(
    "-r", nargs=1, help="github repository, user/repo", dest="git_url", required=True
)
plugin_uninstall.add_argument(
    "-r", nargs=1, help="github repository, user/repo", dest="git_url", required=True
)

plugin_install.add_argument(
    "-b", type=str, help='branch name e.g "master", "main"', dest="branch"
)
plugin_uninstall.add_argument(
    "-b", type=str, help='branch name e.g "master", "main"', dest="branch"
)
types.add_parser("list")
types.add_parser("info")
profile = action.add_parser("profile")
profile_action = profile.add_subparsers(
    title="action", dest="profile_action", required=True
)
delete_profile = profile_action.add_parser("delete")
delete_profile.add_argument("ids", nargs="*")
profile_action.add_parser("list")
profile_action.add_parser("info").add_argument("id", nargs=1)
parse = arg.parse_args()


def main():
    DIRNAME = os.getcwd().split("/")[-1]
    with open(os.path.dirname(__file__) + "/templates/thundra.toml", "r") as file:
        toml_template = tomllib.loads(file.read())
    match parse.action:
        case "create":
            name = input(f"Name [{DIRNAME}]: ")
            toml_template["thundra"]["name"] = name or DIRNAME
            toml_template["thundra"]["author"] = (
                input(r"Author [krypton-byte]: ") or "krypton-byte"
            )
            toml_template["thundra"]["owner"] = [
                input("Owner [6283172366463]: ") or "6283172366463"
            ]
            toml_template["thundra"]["prefix"] = input(r"Prefix [\\.] : ") or "\\."
            importable_name = re.findall(
                r"[\w\ ]+", re.sub(r"[\ \-]+", "_", toml_template["thundra"]["name"])
            )[0]
            dest = os.getcwd() + "/" + importable_name
            print("🚀 create %r project" % toml_template["thundra"]["name"])
            os.mkdir(importable_name)
            for content in Path(os.path.dirname(__file__) + "/templates").iterdir():
                if content.is_dir():
                    if content.name == "app":
                        shutil.copytree(content, dest, dirs_exist_ok=True)
                else:
                    shutil.copy(content, os.getcwd())
            toml_template["thundra"]["app"] = f"{importable_name}.app:app"
            open("thundra.toml", "w").write(dumps(toml_template))
        case "test":
            from .config import config_toml

            os.environ.update(config_toml["thundra"].get("env", {}))
            from .utils import workdir

            sys.path.insert(0, workdir.workspace_dir.__str__())
            dirs, client = config_toml["thundra"]["app"].split(":")
            app = __import__(dirs)
            sys.path.remove(workdir.workspace_dir.__str__())
            from .test import tree_test

            tree_test()
        case "install":
            from .config import config_toml
            from .plugins import PluginSource

            for package in config_toml["plugins"].values():
                PluginSource(package["username"], package["repository"]).download_head(
                    package["branch"]
                ).install()
        case "run":
            from .utils import workdir

            profiler = Profiler.get_profiler()
            with open(workdir.db / "thundra.toml") as file:
                workdir_db = workdir.db / tomllib.loads(file.read())["thundra"]["db"]
            if parse.workspace:
                profile = profiler.get_profile(parse.workspace)
                workdir.workspace_dir = Path(profile.workspace)
                os.chdir(workdir.workspace)
                if workdir.db.__str__() == ".":
                    workdir.db = Path(profile.db_path()).parent
                    workdir_db = profile.db_path()
            if parse.db:
                profile = profiler.get_profile(parse.db)
                workdir.db = Path(profile.db_path()).parent
                workdir_db = profile.db_path()
            from .config import config_toml

            os.environ.update(config_toml["thundra"].get("env", {}))
            VirtualEnv.get_env().activate(workdir.workspace.__str__())
            from .utils import workdir
            from .agents import agent
            from .command import command
            from .middleware import middleware

            print("🚀 starting %r" % config_toml["thundra"]["name"])
            config_toml["thundra"]["db"] = workdir_db.__str__()
            sys.path.insert(0, workdir.workspace_dir.__str__())
            dirs, client = config_toml["thundra"]["app"].split(":")
            app = __import__(dirs)
            sys.path.remove(workdir.workspace_dir.__str__())
            print(
                f"🤖 {agent.__len__()} Agents, 🚦 {middleware.__len__()} Middlewares, and 📢 {command.__len__()} Commands"
            )
            for attr in dirs.split(".")[1:]:
                app = getattr(app, attr)
            if parse.phone_number:
                app.__getattribute__(client).PairPhone(
                    parse.phone_number, parse.push_notification
                )
            else:
                app.__getattribute__(client).connect()
        case "plugin":
            from .plugins import PluginSource, Plugin

            match parse.plugin_action:
                case "install":
                    username, repo = parse.git_url[0].split("/")
                    plugin = PluginSource(username=username, repository=repo)
                    if not parse.branch:
                        parse.branch = plugin.branch()[0]["name"]
                    plugin.download_head(parse.branch).install()
                case "uninstall":
                    username, repo = parse.git_url[0].split("/")
                    plugins: List[Plugin] = []
                    if parse.branch:
                        plugins.append(
                            Plugin.find_full_args(username, repo, parse.branch)
                        )
                    else:
                        plugins.extend(Plugin.find_by_author_and_name(username, repo))
                    for plugin in plugins:
                        shutil.rmtree(plugin.path)
                        print(f"[deleted] {plugin.name}")
                    if not plugins:
                        print(f"[plugin] {parse.git_url[0]} not found")
                case "list":
                    for plugin in Plugin.get_all_plugins():
                        print(plugin.stringify())
        case "profile":
            profiler = Profiler.get_profiler()
            match parse.profile_action:
                case "list":
                    for profile in profiler:
                        print(
                            f"""
                        {profile.get_id()}:\n\tworkpace: {profile.workspace}\n\t{(f'db: {profile.db_path()}') if profile.db_exist() else ''}\n\tpushname: {profile.pushname}\n\tphone number: {profile.phonenumber}
                        """.strip()
                        )
                case "delete":
                    profiler.delete_profile(*parse.ids)
                case "info":
                    profile = profiler.get_profile(parse.id[0])
                    print(
                        f"""
                        {parse.id[0]}:\n\tworkpace: {profile.workspace}\n\t{(f'db: {profile.db_path()}') if profile.db_exist() else ''}\n\tpushname: {profile.pushname}\n\tphone number: {profile.phonenumber}
                        """.strip()
                    )


if __name__ == "__main__":
    main()
