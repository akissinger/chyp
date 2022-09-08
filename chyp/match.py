from __future__ import annotations
from typing import Set, List, Dict, Iterator, Any, Optional, Iterable

from .graph import Graph

class Match:
    def __init__(self, dom: Graph=None, cod: Graph=None, m: Match=None):
        if m:
            self.dom = m.dom
            self.cod = m.cod
            self.vmap: Dict[int,int] = m.vmap.copy()
            self.vimg: Set[int] = m.vimg.copy()
            self.vdone: Set[int] = m.vdone.copy()
            self.emap: Dict[int,int] = m.emap.copy()
            self.eimg: Set[int] = m.eimg.copy()
        else:
            self.dom = dom
            self.cod = cod
            self.vmap: Dict[int,int] = dict()
            self.vimg: Dict[int,int] = dict()
            self.vdone: Set[int] = set()
            self.emap: Dict[int,int] = dict()
            self.eimg: Dict[int,int] = dict()

    def copy(self) -> Match:
        return Match(m=self)

    def try_add_vertex(self, v: int, cod_v: int) -> bool:
        if self.dom.vdata(v).value != self.cod.vdata(cod_v).value: return False

        # matches are only allowed to be non-injective on the boundary
        if cod_v in self.vimg:
            if not self.dom.is_boundary(v): return False
            for dv, cv in self.dom.vmap.items():
                if cv == cod_v and not self.dom.is_boundary(dv):
                    return False
        self.vmap[v] = cod_v
        self.vimg.add(cod_v)

    def try_add_edge(self, e: int, cod_e: int) -> bool:
        if self.dom.edata(e).value != self.cod.edata(cod_e).value: return False
        if e_cod in self.eimg: return False
        self.emap[e] = cod_e
        self.eimg.add(cod_e)

        # compare sources and targets
        s = self.dom.source(e)
        cod_s = self.cod.source(cod_e)
        t = self.dom.target(e)
        cod_t = self.cod.target(cod_e)

        # first the lengths need to be the same
        if len(s) != len(cod_s) or len(t) != len(cod_t):
            return False

        # then, each vertex that is already mapped needs to be consistent
        success = True
        for v1, cod_v1 in zip(s + t, cod_s + cod_t):
            if v1 in self.vmap:
                if self.vmap[v1] != cod_v1:
                    success = False
                    break
            else:
                if not self.try_add_vertex(v1, cod_v1):
                    success = False
                    break
        return success

    def more(self) -> List[Match]:
        # a list of partial matches the same as this one, but matching 1 more vertex or edge
        ms = []

        # first try to complete nhds of vertices already matched
        for v in self.vmap:
            # check if a vertex's nhd is already fully mapped. the set vdone prevents this check from
            #  being done multiple times.
            if v in self.vdone: continue
            if (all(e in self.emap for e in self.dom.in_edges(v)) and
                all(e in self.emap for e in self.dom.out_edges(v))):
                self.vdone.add(v)
                continue

            cod_v = self.vmap[v]

            # try to extend the match by mapping the next in_edge
            for e in self.dom.in_edges(v):
                if e in self.emap: continue
                for cod_e in self.cod.in_edges(cod_v):
                    m1 = self.copy()
                    if m1.try_add_edge(e, cod_e):
                        ms.append(m1)
                return ms

            # if there are no unmapped in_edges, try to match the next out_edge
            for e in self.dom.out_edges(v):
                if e in self.emap: continue
                for cod_e in self.cod.out_edges(cod_v):
                    if cod_e in self.eimg: continue
                    m1 = self.copy()
                    if m1.try_add_edge(e, cod_e):
                        ms.append(m1)
                return ms
            
        # if there are no more vertices with partially-mapped nhds,  try to match a new vertex
        for v in self.dom.vertices():
            # already looked at these
            if v in self.vmap: continue
            
            # create a new match for every possible place v can go
            for cod_v in self.cod.vertices():
                m1 = self.copy()
                if m1.try_add_vertex(v, cod_v):
                    ms.append(m1)
            return ms
    
    def is_total(self) -> bool:
        return len(self.vmap) == self.dom.num_vertices() and len(self.emap) == self.dom.num_edges()

    def is_surjective(self) -> bool:
        return len(self.vimg) == self.cod.num_vertices() and len(self.eimg) == self.cod.num_edges()

    def is_injective(self) -> bool:
        return len(self.vmap) == len(self.vimg)

class Matches(Iterable):
    def __init__(self):
        self.match_stack = []

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> Match:
        while len(self.match_stack) > 0:
            m = self.match_stack.pop()
            if m.is_total(): return m
            else: self.match_stack += m.more()
        raise StopIteration
