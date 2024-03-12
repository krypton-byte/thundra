from .utils import log
from logging import NOTSET, DEBUG
from .config import config_toml
import os


def ptree(start, tree, indent_width=4):
    def _ptree(start, parent, tree, grandpa=None, indent=""):
        if parent != start:
            if grandpa is None:  # Ask grandpa kids!
                print(tree[parent]["name"], end="")
            else:
                print(tree[parent]["name"])
        if parent not in tree:
            return
        for child in tree[parent]["child"][:-1]:
            print(indent + "├" + "─" * indent_width, end="")
            _ptree(start, child, tree, parent, indent + "│" + " " * 4)
        # print(tree, parent)
        if tree[parent]["child"]:
            child = tree[parent]["child"][-1]
            print(indent + "└" + "─" * indent_width, end="")
            _ptree(start, child, tree, parent, indent + " " * 5)  # 4 -> 5

    parent = start
    print(tree[start]["name"])
    _ptree(start, parent, tree)


def tree_test():
    from .middleware import middleware
    from .command import command
    from .agents import agent

    dtree = {
        -1: {"name": config_toml["thundra"]["name"], "child": [0, 1, 2]},
        0: {"name": "Agents", "child": []},
        1: {"name": "Middlewares", "child": []},
        2: {"name": "Commands", "child": []},
    }
    start = 3
    for item in agent:
        idn = start
        dtree[0]["child"].append(idn)
        dtree.update({idn: {"name": item.agent.__name__, "child": []}})
        start += 1
    for item in middleware:
        idn = start
        dtree[1]["child"].append(idn)
        dtree.update({idn: {"name": item.name, "child": []}})
        start += 1
    for item in command.values():
        idn = start
        dtree[2]["child"].append(idn)
        dtree.update({idn: {"name": item.name, "child": []}})
        start += 1
    ptree(-1, dtree)
    print(
        f"🤖 {agent.__len__()} Agents, 🚦 {middleware.__len__()} Middlewares, and 📢 {command.__len__()} Commands"
    )
