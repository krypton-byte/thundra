from pathlib import Path
import os
import sys
from typing import Optional
from .utils import workdir


def evaluate_module(root_path: Path, workspace: Optional[Path] = None):
    sys.path.append(root_path.__str__())
    for path, _, files in os.walk(root_path):
        path_o = Path(path).relative_to(workspace or workdir.workspace.parent)
        for file in filter(lambda x: x.endswith(".py"), files):
            path_list = (
                path_o.__str__().strip("/").split("/")
                if path_o.__str__() != "."
                else []
            )
            file = file.rstrip(".py")
            path_list.extend(file.split("/"))
            __import__(".".join(path_list))
    sys.path.remove(root_path.__str__())
    # path.reverse()
    # mod = None
    # while path:
    #     if mod is None:
    #         mod = __import__(path.pop())
    #     else:
    #         getattr(mod, path.pop())
