import argparse, os
import tomllib
from typing import Dict, Optional
from tomli_w import dumps
from .utils import workdir


from .config import config_toml
import shutil
from pathlib import Path
import sys

arg = argparse.ArgumentParser()
action = arg.add_subparsers(title="action", dest="action", required=True)
create = action.add_parser(name="create")
create.add_argument("--name", type=str, nargs=1)

run = action.add_parser(name="run")

test = action.add_parser(name="test")

plugins = action.add_parser("plugin")
types=plugins.add_subparsers(title="type", dest="type", required=True)
types.add_parser("install")
types.add_parser("uninstall")
types.add_parser("info")

parse = arg.parse_args()



def main():
    DIRNAME = os.getcwd().split('/')[-1]
    with open(os.path.dirname(__file__) + '/templates/thundra.toml', 'r') as file:
        toml_template = tomllib.loads(file.read())
    match parse.action:
        case "create":
            name = input(f"Name [{DIRNAME}]: ")
            toml_template['thundra']['name'] = name or DIRNAME
            toml_template['thundra']['author'] = input(r'Author [krypton-byte]: ') or 'krypton-byte'
            toml_template['thundra']['owner'] = [input('Owner [6283172366463]: ') or '6283172366463']
            toml_template['thundra']['prefix'] = input(r'Prefix [\\.] : ') or '\\.'
            open("thundra.toml", "w").write(dumps(toml_template))
            dest = os.getcwd()
            for content in Path(os.path.dirname(__file__) +'/templates').iterdir():
                if content.is_dir():
                    shutil.copytree(content, dest + '/' + content.name)
                else:
                    shutil.copy(content, dest)
        case "test":
            sys.path.insert(0, workdir.__str__())
            dirs, client = config_toml['thundra']['app'].split(':')
            app = __import__(dirs)
            sys.path.remove(workdir.__str__())
            from .test import tree_test
            tree_test()
        case "run":
            sys.path.insert(0, workdir.__str__())
            dirs, client = config_toml['thundra']['app'].split(':')
            app = __import__(dirs)
            sys.path.remove(workdir.__str__())
            app.__getattribute__(client).connect()
        case "plugin":
            print("NotImplemented yet")



if __name__ == '__main__':
    main()
                
