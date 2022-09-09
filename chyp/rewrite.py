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

def rewrite(g: Graph, r: Rule, m: Match) -> Match:
    """Do DPO rewriting

    Given a graph g, a rule r, and match of r.lhs into g, return a match of r.rhs into
    the rewritten graph.
    """
    if not r.is_left_linear():
        raise NotImplementedError("Only left linear rules are supported for now")

    # this will be the rewritten graph
    h = g.copy()

    # compute the pushout complement
    for e in r.lhs.edges():
        h.remove_edge(m.emap[e])
    for v in r.lhs.vertices():
        if not r.lhs.is_boundary(v):
            h.remove_vertex(m.vmap[v])

    # this will embed r.rhs into h
    m1 = Match(r.rhs, h)
    vmap1: Dict[int,int] = {}

    # first map the boundary, using the matching of the lhs
    for vl,vr in zip(r.lhs.inputs(), r.rhs.inputs()): m1.vmap[vr] = m.vmap[vl]
    for vl,vr in zip(r.lhs.outputs(), r.rhs.outputs()): m1.vmap[vr] = m.vmap[vl]

    # then map the interior to new, fresh vertices
    for v in r.rhs.vertices():
        if not r.rhs.is_boundary(v):
            vd = r.rhs.vertex_data(v)
            v1 = h.add_vertex(vd.x, vd.y, vd.value)
            m1.vmap[v] = v1
            m1.vimg.add(v1)

    # now add the edges from rhs to h and connect them using vmap1
    for e in r.rhs.edges():
        ed = r.rhs.edge_data(e)
        e1 = h.add_edge([m1.vmap[v] for v in ed.s],
                        [m1.vmap[v] for v in ed.t],
                        ed.x, ed.y, ed.value, ed.hyper)
        m1.emap[e] = e1
        m1.eimg.add(e1)

    return m1

def rewrite_graph(g: Graph, r: Rule, m: Match) -> Graph:
    """Apply the given rewrite r to graph g and match m

    This is a convience wrapper for `rewrite` for when the matching of
    the rhs into the rewritten graph is not needed."""
    m1 = rewrite(g, r, m)
    return m1.cod
