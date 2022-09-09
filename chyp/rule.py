from __future__ import annotations
import itertools
from .graph import Graph

class Rule:
    lhs: Graph
    rhs: Graph

    def __init__(self, lhs: Graph, rhs: Graph):
        self.lhs = lhs
        self.rhs = rhs

    def is_left_linear(self) -> bool:
        """Returns True if boundary on lhs embeds injectively"""
        verts = set()
        for v in itertools.chain(self.lhs.inputs(), self.lhs.outputs()):
            if v in verts: return False
            verts.add(v)
        return True
