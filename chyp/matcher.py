#     chyp - A compositional hypergraph library
#     Copyright (C) 2022 - Aleks Kissinger
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
from typing import Set, List, Dict, Iterator, Any, Optional, Iterable
from .graph import Graph
from .rule import Rule

def match_log(s: str) -> None:
    """Used for debugging the matcher"""
    pass
    # print(s)

class Match:
    dom: Graph
    cod: Graph
    vmap: Dict[int,int]
    vimg: Set[int]
    emap: Dict[int,int]
    eimg: Set[int]

    def __init__(self, dom: Graph=None, cod: Graph=None, m: Match=None) -> None:
        if m:
            self.dom = m.dom
            self.cod = m.cod
            self.vmap = m.vmap.copy()
            self.vimg = m.vimg.copy()
            self.emap = m.emap.copy()
            self.eimg = m.eimg.copy()
        elif dom and cod:
            self.dom = dom
            self.cod = cod
            self.vmap = dict()
            self.vimg = set()
            self.emap = dict()
            self.eimg = set()
        else:
            raise ValueError("Must provide either a match or a pair of graphs")

    def __str__(self) -> str:
        return "  vmap: {}\n  emap: {}".format(str(self.vmap), str(self.emap))

    def copy(self) -> Match:
        return Match(m=self)

    def try_add_vertex(self, v: int, cod_v: int) -> bool:
        match_log("trying to add vertex {} -> {} to match:".format(v, cod_v))
        match_log(str(self))

        v_val = self.dom.vertex_data(v).value
        cod_v_val = self.cod.vertex_data(cod_v).value

        if v_val != cod_v_val:
            match_log("vertex failed: values {} != {}".format(v_val, cod_v_val))
            return False

        if self.cod.is_boundary(cod_v) and not self.dom.is_boundary(v):
            match_log("vertex failed: cod v is boundary but dom v is not")
            return False

        # matches are only allowed to be non-injective on the boundary
        if cod_v in self.vimg:
            if not self.dom.is_boundary(v):
                match_log("vertex failed: non-injective on interior vertex")
                return False
            for dv, cv in self.vmap.items():
                if cv == cod_v and not self.dom.is_boundary(dv):
                    match_log("vertex failed: non-injective on interior vertex")
                    return False
        self.vmap[v] = cod_v
        self.vimg.add(cod_v)

        # unless v is a boundary, check that nhd(v) and nhd(vmap(v)) are the same size. Because
        # matchings are required to be injective on edges, this will guarantee that the gluing
        # conditions are satisfied.
        if not self.dom.is_boundary(v):
            if len(self.dom.in_edges(v)) != len(self.cod.in_edges(cod_v)):
                match_log("vertex failed: in_edges cannot satisfy gluing conds")
                return False
            if len(self.dom.out_edges(v)) != len(self.cod.out_edges(cod_v)):
                match_log("vertex failed: out_edges cannot satisfy gluing conds")
                return False

        match_log("vertex success")
        return True

    def try_add_edge(self, e: int, cod_e: int) -> bool:
        match_log("trying to add edge {} -> {} to match:".format(e, cod_e))
        match_log(str(self))

        e_val = self.dom.edge_data(e).value
        cod_e_val = self.cod.edge_data(cod_e).value
        if e_val != cod_e_val:
            match_log("edge failed: values {} != {}".format(e_val, cod_e_val))
            return False

        if cod_e in self.eimg:
            match_log("edge failed: non-injective")
            return False

        self.emap[e] = cod_e
        self.eimg.add(cod_e)

        # compare sources and targets
        s = self.dom.source(e)
        cod_s = self.cod.source(cod_e)
        t = self.dom.target(e)
        cod_t = self.cod.target(cod_e)

        # first the lengths need to be the same
        if len(s) != len(cod_s) or len(t) != len(cod_t):
            match_log("edge failed: source or target len doesn't match image")
            return False

        # then, each vertex that is already mapped needs to be consistent
        for v1, cod_v1 in zip(s + t, cod_s + cod_t):
            if v1 in self.vmap:
                if self.vmap[v1] != cod_v1:
                    match_log("edge failed: inconsistent with previously mapped vertex")
                    return False
            else:
                if not self.try_add_vertex(v1, cod_v1):
                    match_log("edge failed: couldn't add a vertex")
                    return False
        
        match_log("edge success")
        return True

    def dom_nhd_mapped(self, v: int) -> bool:
        """Returns True if nhd(v) is the domain of emap"""
        return (all(e in self.emap for e in self.dom.in_edges(v)) and
                all(e in self.emap for e in self.dom.out_edges(v)))

    # def cod_nhd_mapped(self, cod_v: int):
    #     """Returns True if nhd(cod_v) is the range of emap"""
    #     return (all(e in self.eimg for e in self.cod.in_edges(cod_v)) and
    #             all(e in self.eimg for e in self.cod.out_edges(cod_v)))


    def more(self) -> List[Match]:
        # a list of partial matches the same as this one, but matching 1 more vertex or edge
        ms = []

        # first try to complete nhds of vertices already matched
        for v in self.vmap:
            # check if a vertex's nhd is already fully mapped
            if self.dom_nhd_mapped(v): continue
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

        return []
    
    def is_total(self) -> bool:
        return len(self.vmap) == self.dom.num_vertices() and len(self.emap) == self.dom.num_edges()

    def is_surjective(self) -> bool:
        return len(self.vimg) == self.cod.num_vertices() and len(self.eimg) == self.cod.num_edges()

    def is_injective(self) -> bool:
        return len(self.vmap) == len(self.vimg)

class Matches(Iterable):
    def __init__(self, dom: Graph, cod: Graph) -> None:
        self.match_stack = [Match(dom=dom, cod=cod)]

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> Match:
        while len(self.match_stack) > 0:
            m = self.match_stack.pop()
            if m.is_total():
                match_log("got successful match:\n" + str(m))
                return m
            else:
                self.match_stack += m.more()
        raise StopIteration

def match_graph(dom: Graph, cod: Graph) -> Iterable[Match]:
    return Matches(dom, cod)

def match_rule(r: Rule, g: Graph) -> Iterable[Match]:
    return Matches(r.lhs, g)
