from pathlib import Path
from tomli_w import dumps

import argparse, os
import tomllib
import shutil
import sys

from thundra.profiler import Profiler


arg = argparse.ArgumentParser()
action = arg.add_subparsers(title="action", dest="action", required=True)
create = action.add_parser(name="create")
create.add_argument("--name", type=str, nargs=1)

run = action.add_parser(name="run")
run.add_argument("--phone-number", type=str, help="using pairphone as authentication, default qr")
run.add_argument("--push-notification", action="store_true", default=False)
test = action.add_parser(name="test")

plugins = action.add_parser("plugin")
types = plugins.add_subparsers(title="type", dest="type", required=True)
types.add_parser("install")
types.add_parser("uninstall")
types.add_parser("info")
profile = action.add_parser("profile")
profile_action = profile.add_subparsers(title="action", dest="profile_action", required=True)
delete_profile = profile_action.add_parser("delete")
delete_profile.add_argument("ids", nargs="*")
profile_action.add_parser("list")
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
            open("thundra.toml", "w").write(dumps(toml_template))
            dest = os.getcwd()
            print("🚀 create %r project" % toml_template["thundra"]["name"])
            for content in Path(os.path.dirname(__file__) + "/templates").iterdir():
                if content.is_dir():
                    shutil.copytree(content, dest + "/" + content.name)
                else:
                    shutil.copy(content, dest)
        case "test":
            from .utils import workdir
            from .config import config_toml

            sys.path.insert(0, workdir.__str__())
            dirs, client = config_toml["thundra"]["app"].split(":")
            app = __import__(dirs)
            sys.path.remove(workdir.__str__())
            from .test import tree_test

            tree_test()
        case "run":
            from .utils import workdir
            from .config import config_toml
            from .agents import agent
            from .command import command
            from .middleware import middleware

            print("🚀 starting %r" % config_toml["thundra"]["name"])
            sys.path.insert(0, workdir.__str__())
            dirs, client = config_toml["thundra"]["app"].split(":")
            app = __import__(dirs)
            sys.path.remove(workdir.__str__())
            print(
                f"🤖 {agent.__len__()} Agents, 🚦 {middleware.__len__()} Middlewares, and 📢 {command.__len__()} Commands"
            )
            if parse.phone_number:
                app.__getattribute__(client).PairPhone(
                    parse.phone_number, parse.push_notification
                )
            else:
                app.__getattribute__(client).connect()
        case "plugin":
            from .config import config_toml
            from thundra.config import config_format

            # print(config_format(config_toml))
            import re
            print("NotImplemented yet")
        case "profile":
            match parse.profile_action:
                case "list":
                    for profile in Profiler.get_profiler():
                        print(f"""
                        {profile.get_id()}:\n\tworkpace: {profile.workspace}\n\t{(f'db: {profile.db_path()}') if profile.db_exist() else ''}\n\tpushname: {profile.pushname}\n\tphone number: {profile.phonenumber}
                        """.strip())
                case "delete":
                    Profiler.get_profiler().delete_profile(*parse.ids)
if __name__ == "__main__":
    main()
