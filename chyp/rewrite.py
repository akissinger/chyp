from __future__ import annotations
from typing import Set, List, Dict, Iterator, Any, Optional, Iterable
import itertools
from .graph import Graph
from .matcher import Match

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

def rewrite(g: Graph, r: Rule, m: Match) -> Graph:
    if not r.is_left_linear():
        raise NotImplementedError("Only left linear rules are supported for now")

    h = g.copy()

    # compute the pushout complement
    for e in r.lhs.edges():
        h.remove_edge(m.emap[e])
    for v in r.lhs.vertices():
        if not r.lhs.is_boundary(v):
            h.remove_vertex(m.vmap[v])

    # TODO glue in rhs

    return h

