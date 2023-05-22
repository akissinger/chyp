#     chyp - An interactive theorem prover for string diagrams 
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
from typing import Iterable, Set, List, Dict, Iterator, Any, Optional, Tuple
import json
import copy

class GraphError(Exception):
    pass

class VData:
    def __init__(self, x: float=0, y: float=0, value: Any="") -> None:
        self.value = value
        self.x = x
        self.y = y
        self.highlight = False

        # for quickly finding edges in the nhd of v
        self.in_edges: Set[int] = set()
        self.out_edges: Set[int] = set()

        # if v is in the list of inputs/outputs, save its index here
        self.in_indices: Set[int] = set()
        self.out_indices: Set[int] = set()

class EData:
    def __init__(self,
            s: Optional[List[int]]=None,
            t: Optional[List[int]]=None,
            value: Any="",
            x: float=0,
            y: float=0,
            fg: str='',
            bg: str='',
            hyper: bool=True) -> None:
        self.value = value
        self.highlight = False
        self.x = x
        self.y = y
        self.s = [] if s is None else s
        self.t = [] if t is None else t
        self.fg = fg
        self.bg = bg
        self.hyper = hyper

    def __repr__(self) -> str:
        return "Edge: %s (%d, %d)" % (self.value, self.x, self.y)

    def box_size(self) -> int:
        """Returns the number of 'units' of width the box should have to display nicely.

        The simple rule is if both inputs and outputs are <= 1, draw as a small (size 1) box, otherwise
        draw as a larger (size 2) box."""
        return 1 if len(self.s) <= 1 and len(self.t) <= 1 else 2

class Graph:
    def __init__(self) -> None:
        self.vdata: Dict[int, VData] = {}
        self.edata: Dict[int, EData] = {}
        self._inputs: List[int] = []
        self._outputs: List[int] = []
        self.vindex = 0
        self.eindex = 0

    def copy(self) -> Graph:
        g = Graph()
        g.vdata = copy.deepcopy(self.vdata)
        g.edata = copy.deepcopy(self.edata)
        g._inputs = self._inputs.copy()
        g._outputs = self._outputs.copy()
        g.vindex = self.vindex
        g.eindex = self.eindex
        return g

    def vertices(self) -> Iterator[int]:
        return iter(self.vdata.keys())

    def edges(self) -> Iterator[int]:
        return iter(self.edata.keys())

    def num_vertices(self) -> int:
        return len(self.vdata)

    def num_edges(self) -> int:
        return len(self.edata)

    def vertex_data(self, v: int) -> VData:
        return self.vdata[v]

    def edge_data(self, e: int) -> EData:
        return self.edata[e]

    def in_edges(self, v: int) -> Set[int]:
        return self.vdata[v].in_edges

    def out_edges(self, v: int) -> Set[int]:
        return self.vdata[v].out_edges

    def source(self, e: int) -> List[int]:
        return self.edata[e].s

    def target(self, e: int) -> List[int]:
        return self.edata[e].t

    def add_vertex(self, x:float=0, y:float=0, value: Any="", name: int=-1) -> int:
        """Add a vertex to the graph
        
        :param x:     The X coordinate to draw the vertex
        :param y:     The Y coordinate
        :param value: The value carried by this vertex. This is the empty string by default.
        :param name:  An optional name. If this is set to -1, set the name automatically. After
                      setting names manually, be sure to call `update_indices` to make sure
                      future automatic names don't clash.
        """
        if name == -1:
            v = self.vindex
            self.vindex += 1
        else:
            v = name

        self.vdata[v] = VData(x, y, value)
        return v

    def add_edge(self, s:List[int], t:List[int], value:Any="", x:float=0, y:float=0, fg:str='', bg:str='', hyper:bool=True, name:int=-1) -> int:
        """Add an edge to the graph
        
        :param s:     A list of source vertices
        :param t:     A list of target vertices
        :param value: The value carried by this edge (typically a string)
        :param x:     The X coordinate to draw the box representing this hyperedge
        :param y:     The Y coordinate
        :param hyper: This is a hint to tell the GUI how to draw this (hyper)edge. If set to
                      False, ideally it should be drawn simply as a line connected two vertices
                      rather than as a box.
        :param name:  An optional name. If this is set to -1, set the name automatically. After
                      setting names manually, be sure to call `update_indices` to make sure
                      future automatic names don't clash.
        """
        if name == -1:
            e = self.eindex
            self.eindex += 1
        else:
            e = name

        self.edata[e] = EData(s, t, value, x, y, fg, bg, hyper)
        for v in s: self.vdata[v].out_edges.add(e)
        for v in t: self.vdata[v].in_edges.add(e)
        return e

    def remove_vertex(self, v: int, strict: bool=False) -> None:
        if strict:
            if (len(self.vertex_data(v).in_edges)  > 0 or
                len(self.vertex_data(v).out_edges) > 0):
                raise Exception("Attempting to remove vertex with adjacent edges")
            if (v in self.inputs() or v in self.outputs()):
                raise Exception("Attempting to remove boundary vertex")
        else:
            for e in self.vertex_data(v).in_edges:
                self.edge_data(e).t = [v1 for v1 in self.edge_data(e).t if v1 != v]
            for e in self.vertex_data(v).out_edges:
                self.edge_data(e).s = [v1 for v1 in self.edge_data(e).s if v1 != v]
            self.set_inputs([v1 for v1 in self.inputs() if v1 != v])
            self.set_outputs([v1 for v1 in self.outputs() if v1 != v])
        del self.vdata[v]

    def remove_edge(self, e: int) -> None:
        for v in self.edge_data(e).s:
            self.vertex_data(v).out_edges.remove(e)
        for v in self.edge_data(e).t:
            self.vertex_data(v).in_edges.remove(e)
        del self.edata[e]

    def add_simple_edge(self, s:int, t:int, value: Any="") -> int:
        e = self.add_edge([s], [t], value, hyper=False)
        return e

    def update_indices(self) -> None:
        self.vindex = max(self.vdata.keys()) + 1 if self.vdata else 0
        self.eindex = max(self.edata.keys()) + 1 if self.edata else 0

    def set_inputs(self, inp: List[int]) -> None:
        self._inputs = inp
        for d in self.vdata.values():
            d.in_indices.clear()

        for i,v in enumerate(self._inputs):
            self.vdata[v].in_indices.add(i)

    def set_outputs(self, outp: List[int]) -> None:
        self._outputs = outp
        for d in self.vdata.values():
            d.out_indices.clear()

        for i,v in enumerate(self._outputs):
            self.vdata[v].out_indices.add(i)

    def inputs(self) -> List[int]:
        return self._inputs

    def outputs(self) -> List[int]:
        return self._outputs

    def is_input(self, v: int) -> bool:
        return len(self.vdata[v].in_indices) > 0

    def is_output(self, v: int) -> bool:
        return len(self.vdata[v].out_indices) > 0

    def is_boundary(self, v: int) -> bool:
        return self.is_input(v) or self.is_output(v)

    def successors(self, vs: Iterable[int]) -> Set[int]:
        succ: Set[int] = set()
        current = list(vs)
        while len(current) > 0:
            v = current.pop()
            for e in self.out_edges(v):
                for v1 in self.target(e):
                    if v1 not in succ:
                        succ.add(v1)
                        current.append(v1)

        return succ

    def merge_vertices(self, v: int, w: int) -> None:
        """Identify the two vertices given

        Form the quotient of the graph by identifying v with w. Afterwards, the
        quotiented vertex will be named v.
        """

        vd = self.vertex_data(v)
        
        # print("merging %s <- %s" % (v, w))
        for e in self.in_edges(w):
            ed = self.edge_data(e)
            ed.t = [v if x == w else x for x in ed.t]
            vd.in_edges.add(e)

        for e in self.out_edges(w):
            ed = self.edge_data(e)
            ed.s = [v if x == w else x for x in ed.s]
            vd.out_edges.add(e)

        self.set_inputs([v if x == w else x for x in self.inputs()])
        self.set_outputs([v if x == w else x for x in self.outputs()])
        self.remove_vertex(w)

    def explode_vertex(self, v: int) -> Tuple[List[int], List[int]]:
        """Split a vertex into one copy for each input, in-tentacle, output, and out-tentacle

        This is used for computing pushout complements of rules that aren't left-linear. Returns
        a pair of lists containing the new input-like and output-like vertices, respectively.
        """

        new_vs: Tuple[List[int], List[int]] = ([], [])
        vd = self.vertex_data(v)
        def fresh(j: int) -> int:
            v1 = self.add_vertex(vd.x, vd.y, vd.value)
            new_vs[j].append(v1)
            return v1

        self.set_inputs([v1 if v1 != v else fresh(0) for v1 in self.inputs()])

        for e in vd.in_edges:
            ed = self.edge_data(e)
            for i in range(len(ed.t)):
                if ed.t[i] == v:
                    ed.t[i] = fresh(0)
                    self.vertex_data(ed.t[i]).in_edges.add(e)

        self.set_outputs([v1 if v1 != v else fresh(1) for v1 in self.outputs()])

        for e in vd.out_edges:
            ed = self.edge_data(e)
            for i in range(len(ed.s)):
                if ed.s[i] == v:
                    ed.s[i] = fresh(1)
                    self.vertex_data(ed.s[i]).out_edges.add(e)


        vd.in_edges = set()
        vd.out_edges = set()
        self.remove_vertex(v, strict=True)

        return new_vs

    def insert_id_after(self, v: int, reverse: bool = False) -> int:
        """Insert a new identity hyperedge after the given vertex

        Insert a dummy identity box with source at the given vertex and redirect
        any out-edges or outputs to the target of the new hyperedge. If `reverse`
        is True, then flip the source and target of the identity wire. This can be
        used to break directed cycles, essentially by introducing a cap and cup.
        """
        vd = self.vertex_data(v)
        w = self.add_vertex(vd.x + 3, vd.y, vd.value)
        wd = self.vertex_data(w)
        wd.highlight = vd.highlight
        self.set_outputs([x if x != v else w for x in self.outputs()])
        for e in vd.out_edges:
            ed = self.edge_data(e)
            ed.s = [x if x != v else w for x in ed.s]
            wd.out_edges.add(e)
        vd.out_edges.clear()

        s, t = ([v], [w]) if not reverse else ([w], [v])
        e = self.add_edge(s, t, "id", vd.x + 1.5, vd.y)
        self.edge_data(e).highlight = vd.highlight
        return e
    
    def tensor(self, other: Graph) -> None:
        """Take the monoidal product with the given graph

        Calling g.tensor(h) will turn g into g ⊗ h. Use the infix version "g + h" to simply return
        the tensor product without changing g.
        """
        vmap = dict()
        # emap = dict()

        max_self = max(max((self.vertex_data(v).y for v in self.vertices()), default = 0),
                       max((self.edge_data(e).y for e in self.edges()), default=0))
        min_other = min(min((other.vertex_data(v).y for v in other.vertices()), default = 0),
                        min((other.edge_data(e).y for e in other.edges()), default=0))

        for v in self.vertices(): self.vertex_data(v).y -= max_self
        for e in self.edges(): self.edge_data(e).y -= max_self

        for v in other.vertices():
            vd = other.vertex_data(v)
            vmap[v] = self.add_vertex(vd.x, vd.y - min_other + 1, vd.value)

        for e in other.edges():
            ed = other.edge_data(e)
            self.add_edge([vmap[v] for v in ed.s],
                          [vmap[v] for v in ed.t],
                          ed.value, ed.x, ed.y - min_other + 1, ed.fg, ed.bg, ed.hyper)
        
        self.set_inputs(self.inputs() + [vmap[v] for v in other.inputs()])
        self.set_outputs(self.outputs() + [vmap[v] for v in other.outputs()])

    def __mul__(self, other: Graph) -> Graph:
        g = self.copy()
        g.tensor(other)
        return g

    def compose(self, other: Graph) -> None:
        """Compose with given graph in diagram order"""

        vmap = dict()

        max_self = max(max((self.vertex_data(v).x for v in self.vertices()), default = 0),
                       max((self.edge_data(e).x for e in self.edges()), default=0))
        min_other = min(min((other.vertex_data(v).x for v in other.vertices()), default = 0),
                        min((other.edge_data(e).x for e in other.edges()), default=0))

        for v in self.vertices(): self.vertex_data(v).x -= max_self
        for e in self.edges(): self.edge_data(e).x -= max_self

        for v in other.vertices():
            vd = other.vertex_data(v)
            vmap[v] = self.add_vertex(vd.x - min_other, vd.y, vd.value)

        for e in other.edges():
            ed = other.edge_data(e)
            self.add_edge([vmap[v] for v in ed.s],
                          [vmap[v] for v in ed.t],
                          ed.value, ed.x - min_other, ed.y, ed.fg, ed.bg, ed.hyper)
        
        plug1 = self.outputs()
        plug2 = [vmap[v] for v in other.inputs()]
        quotient: Dict[int,int] = dict()
        if len(plug1) != len(plug2):
            raise GraphError("Attempting to plug a graph with %d outputs into one with %d inputs" % (len(plug1), len(plug2)))

        self.set_outputs([vmap[v] for v in other.outputs()])

        for i in range(len(plug1)):
            p1 = plug1[i]
            p2 = plug2[i]
            while p1 in quotient: p1 = quotient[p1]
            while p2 in quotient: p2 = quotient[p2]
            if p1 != p2:
                self.merge_vertices(p1, p2)
                quotient[p2] = p1

    def __rshift__(self, other: Graph) -> Graph:
        g = self.copy()
        g.compose(other)
        return g

def gen(value: str, arity: int, coarity: int, fg: str='', bg: str='') -> Graph:
    g = Graph()
    inputs = [g.add_vertex(-1.5, i - (arity-1)/2) for i in range(arity)]
    outputs = [g.add_vertex(1.5, i - (coarity-1)/2) for i in range(coarity)]
    g.add_edge(inputs, outputs, value, fg=fg, bg=bg)
    g.set_inputs(inputs)
    g.set_outputs(outputs)
    return g
        
def perm(p: List[int]) -> Graph:
    g = Graph()
    size = len(p)
    inputs = [g.add_vertex(0, i - (size-1)/2) for i in range(size)]
    outputs = [inputs[p[i]] for i in range(size)]
    g.set_inputs(inputs)
    g.set_outputs(outputs)
    return g

def identity() -> Graph:
    g = Graph()
    v = g.add_vertex(0, 0)
    g.set_inputs([v])
    g.set_outputs([v])
    return g

# def wide_id() -> Graph:
#     return gen("id", 1, 1)

def id_perm(p: List[int]) -> Graph:
    g = Graph()
    size = len(p)
    inputs = [g.add_vertex(-1.5, i - (size-1)/2) for i in range(size)]
    outputs = [g.add_vertex(1.5, i - (size-1)/2) for i in range(size)]

    for i in range(size):
        y = i - (size-1)/2
        g.add_edge([inputs[i]], [outputs[p[i]]], "id", 0, y)

    g.set_inputs(inputs)
    g.set_outputs(outputs)

    return g

def load_graph(path: str) -> Graph:
    """Load a .chyp graph file from the given path"""

    with open(path) as f:
        g = graph_from_json(f.read())
    return g

def graph_from_json(json_string: str) -> Graph:
    """Load a graph from the given JSON string"""

    j = json.loads(json_string)
    g = Graph()
    for v,vd in j["vertices"].items():
        g.add_vertex(x=float(vd["x"] if "x" in vd else 0.0),
                     y=float(vd["y"] if "y" in vd else 0.0),
                     value=vd["value"] if "value" in vd else "",
                     name=int(v))
    for e,ed in j["edges"].items():
        g.add_edge(s=[int(v) for v in ed["s"]],
                   t=[int(v) for v in ed["t"]],
                   value=ed["value"] if "value" in ed else "",
                   x=float(ed["x"]) if "x" in ed else 0.0,
                   y=float(ed["y"]) if "y" in ed else 0.0,
                   hyper=bool(ed["hyper"]) if "hyper" in ed else True,
                   name=int(e))

    g.set_inputs([int(v) for v in j["inputs"]])
    g.set_outputs([int(v) for v in j["outputs"]])
    g.update_indices()
    return g
