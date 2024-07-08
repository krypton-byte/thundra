from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generator


class Graph(ABC):
    """
    Abstract base class representing a graph with nodes and edges.
    """

    def graph(self) -> str:
        """
        Generates a formatted string representing the graph, including its nodes and edges.

        :return: A string representation of the graph.
        :rtype: str
        """
        cols = [
            f'<tr><td align="left" port="r0">{col} </td></tr>'
            for col in self.get_all_names()
        ]
        data = (
            f'"{self.__class__.__name__}" [ style = "filled, bold" penwidth = 5 '
            f'fillcolor = "white" fontname = "Courier New" shape = "Mrecord" '
            f'label =<<table border="0" cellborder="0" cellpadding="3" bgcolor="white">'
            f'<tr><td bgcolor="black" align="center" colspan="2">'
            f'<font color="white">{self.__class__.__name__}</font></td></tr> {cols} </table>> ];'
        )
        return data

    @abstractmethod
    def get_all_names(self) -> Generator[str, None, None]:
        """
        Abstract method to get all node names in the graph.

        :yield: A generator yielding node names.
        :rtype: Generator[str, None, None]
        """
        ...

    @classmethod
    def combine_graph(cls, *graphs: Graph) -> str:
        """
        Combines multiple graph representations into a single graph.

        :param graphs: Multiple graph objects to combine.
        :type graphs: Graph
        :return: A string representation of the combined graph.
        :rtype: str
        """
        tables = []
        row = []
        for graph in graphs:
            tables.append(graph.graph())
            row.append(graph.__class__.__name__)
        graph_str = """
digraph Thundra {
    fontname="Helvetica,Arial,sans-serif"
    node [fontname="Helvetica,Arial,sans-serif"]
    edge [fontname="Helvetica,Arial,sans-serif"]
    %s
    %s
}
        """ % ("\n".join(tables), "->".join(row))
        return graph_str
