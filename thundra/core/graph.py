from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generator


class Graph(ABC):
    def graph(self):
        cols = [
            f'<tr><td align="left" port="r0">{col} </td></tr>'
            for col in self.get_all_names()
        ]
        data = f'"{self.__class__.__name__}" [ style = "filled, bold" penwidth = 5 fillcolor = "white" fontname = "Courier New" shape = "Mrecord" label =<<table border="0" cellborder="0" cellpadding="3" bgcolor="white"><tr><td bgcolor="black" align="center" colspan="2"><font color="white">{self.__class__.__name__}</font></td></tr> {cols} </table>> ];'
        return data

    @abstractmethod
    def get_all_names(self) -> Generator[str, None, None]:
        ...

    @classmethod
    def combine_graph(cls, *graphs: Graph) -> str:
        tables = []
        row = []
        for graph in graphs:
            tables.append(graph.graph())
            row.append(graph.__class__.__name__)
        graph_str = """
digraph Leo {
	fontname="Helvetica,Arial,sans-serif"
	node [fontname="Helvetica,Arial,sans-serif"]
	edge [fontname="Helvetica,Arial,sans-serif"]
    %s
    %s
}
        """ % ("\n".join(tables), "->".join(row))
        return graph_str
