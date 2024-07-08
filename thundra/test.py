from typing import Any, Dict
from .workdir import config_toml
import os


def ptree(start: Any, tree: Dict[Any, Any], indent_width: int = 4):
    """
    Prints a tree structure starting from the specified node.

    :param start: The starting node of the tree.
    :type start: Any
    :param tree: The tree structure represented as a dictionary.
    :type tree: Dict[Any, Any]
    :param indent_width: The width of each indentation level, defaults to 4.
    :type indent_width: int, optional
    """

    def _ptree(
        start: Any,
        parent: Any,
        tree: Dict[Any, Any],
        grandpa: Any = None,
        indent: str = "",
    ):
        """
        Recursively prints the tree structure.

        :param start: The starting node of the tree.
        :type start: Any
        :param parent: The parent node of the current node.
        :type parent: Any
        :param tree: The tree structure represented as a dictionary.
        :type tree: Dict[Any, Any]
        :param grandpa: The grandparent node of the current node, defaults to None.
        :type grandpa: Any, optional
        :param indent: The indentation string, defaults to "".
        :type indent: str, optional
        """
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
        if tree[parent]["child"]:
            child = tree[parent]["child"][-1]
            print(indent + "└" + "─" * indent_width, end="")
            _ptree(start, child, tree, parent, indent + " " * 5)

    parent = start
    print(tree[start]["name"])
    _ptree(start, parent, tree)


def tree_test():
    """
    Test function to generate and print a tree structure.

    This function creates a tree structure representing different types of items and then prints the tree.

    """
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
