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
from typing import TypeAlias
import json
import copy


VType: TypeAlias = str | None # vertex type is a string label

class GraphError(Exception):
    """Exception thrown by Graph's"""
    pass

class VData:
    """The data assocaited with a single vertex"""

    def __init__(self, x: float = 0, y: float = 0,
                 vtype: VType = None, size: int = 1,
                 value: Any = '') -> None:
        self.value = value
        self.x = x
        self.y = y
        self.highlight = False

        self.vtype = vtype
        self.size = size

        # for quickly finding edges in the nhd of v
        self.in_edges: Set[int] = set()
        self.out_edges: Set[int] = set()

        # if v is in the list of inputs/outputs, save its index here
        self.in_indices: Set[int] = set()
        self.out_indices: Set[int] = set()

class EData:
    """The data assocaited with a single edge"""

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
    """A hypergraph with boundaries

    This is the main data structure used by Chyp. It represents a directed hypergraph (which we call simply a "graph")
    as two dictionaries for vertices and (hyper)edges, respectively. Each vertex is associated with a `VData`
    object and edge edge with an `EData` object, which stores information about adjacency, position, label,
    etc.

    The particular flavor of hypergraphs we use associate to each hyperedge a list of source vertices and a list
    of target vertices. The hypergraph itself also has a list of input vertices and a list of output vertices,
    which are used for sequential composition and rewriting.
    """

    def __init__(self) -> None:
        self.vdata: Dict[int, VData] = {}
        self.edata: Dict[int, EData] = {}
        self._inputs: List[int] = []
        self._outputs: List[int] = []
        self.vindex = 0
        self.eindex = 0

    def copy(self) -> Graph:
        """Make a copy of the graph"""
        g = Graph()
        g.vdata = copy.deepcopy(self.vdata)
        g.edata = copy.deepcopy(self.edata)
        g._inputs = self._inputs.copy()
        g._outputs = self._outputs.copy()
        g.vindex = self.vindex
        g.eindex = self.eindex
        return g

    def vertices(self) -> Iterator[int]:
        """Returns an iterator over the vertices in the graph"""
        return iter(self.vdata.keys())

    def edges(self) -> Iterator[int]:
        """Returns an iterator over the edges in the graph"""
        return iter(self.edata.keys())

    def num_vertices(self) -> int:
        """The number of vertices"""
        return len(self.vdata)

    def num_edges(self) -> int:
        """The number of edges"""
        return len(self.edata)

    def domain(self) -> list[VType]:
        """Returns the domain of the graph."""
        domain = [self.vertex_data(vertex).vtype
                  for vertex in self.inputs()]
        # None is used as vtype in untyped graphs
        if all(d is None for d in domain):
            return len(domain)
        return domain

    def codomain(self) -> list[VType]:
        """Returns the codomain of the graph."""
        codomain = [self.vertex_data(vertex).vtype
                    for vertex in self.outputs()]
        # None is used as vtype in untyped graphs
        if all(d is None for d in codomain):
            return len(codomain)
        return codomain

    def vertex_data(self, v: int) -> VData:
        """Returns the :class:`VData` associated to a given vertex

        :param v: A vertex
        """

        return self.vdata[v]

    def edge_data(self, e: int) -> EData:
        """Returns the :class:`EData` associated to a given edge

        :param e: An edge
        """

        return self.edata[e]

    def edge_domain(self, e: int) -> List[VType] | int:
        """Returns the input type of an edge."""
        domain = [self.vertex_data(vertex).vtype
                  for vertex in self.source(e)]
        # None is used as vtype in untyped graphs
        if all(d is None for d in domain):
            return len(domain)
        return domain

    def edge_codomain(self, e: int) -> List[VType] | int:
        """Returns the output type of an edge."""
        codomain = [self.vertex_data(vertex).vtype
                    for vertex in self.target(e)]
        # None is used as vtype in untyped graphs
        if all(d is None for d in codomain):
            return len(codomain)
        return codomain

    def in_edges(self, v: int) -> Set[int]:
        """Returns a list of edges that have `v` as a target

        :param v: A vertex
        """

        return self.vdata[v].in_edges

    def out_edges(self, v: int) -> Set[int]:
        """Returns a list of edges that have `v` as a source

        :param v: A vertex
        """

        return self.vdata[v].out_edges

    def source(self, e: int) -> List[int]:
        """Returns the list of source vertices associated with an edge

        :param e: An edge
        """

        return self.edata[e].s

    def target(self, e: int) -> List[int]:
        """Returns the list of target vertices associated with an edge

        :param e: An edge
        """

        return self.edata[e].t

    def add_vertex(self, x: float = 0, y: float = 0,
                   vtype: VType = None, size: int = 1,
                   value: Any = '', name: int = -1) -> int:
        """Add a vertex to the graph
        
        :param x:     The X coordinate to draw the vertex
        :param y:     The Y coordinate
        :param value: The value carried by this vertex. This is the empty string by default.
        :param name:  An optional name. If this is set to -1, set the name automatically.
        """
        if name == -1:
            v = self.vindex
            self.vindex += 1
        else:
            v = name
            max_index = max(name, self.vindex)
            self.vindex = max_index + 1

        self.vdata[v] = VData(x, y, vtype, size, value)
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
                      rather than as a box. (Currently not implemented.)
        :param name:  An optional name. If this is set to -1, set the name automatically.
        """
        if name == -1:
            e = self.eindex
            self.eindex += 1
        else:
            e = name
            max_index = max(name, self.eindex)
            self.eindex = max_index + 1

        self.edata[e] = EData(s, t, value, x, y, fg, bg, hyper)
        for v in s: self.vdata[v].out_edges.add(e)
        for v in t: self.vdata[v].in_edges.add(e)
        return e

    def remove_vertex(self, v: int, strict: bool=False) -> None:
        """Remove a vertex

        This removes a single vertex. If `strict` is set to True, then the vertex
        must have no adjacent edges. If it is False, then `v` will be removed from
        the source/target list of all adjacent edges.

        :param v: A vertex to remove
        :param strict: If True, require the vertex to have no adjacent edges
        """

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
        """Remove an edge

        :param e: An edge to remove
        """

        for v in self.edge_data(e).s:
            self.vertex_data(v).out_edges.remove(e)
        for v in self.edge_data(e).t:
            self.vertex_data(v).in_edges.remove(e)
        del self.edata[e]

    # def add_simple_edge(self, s:int, t:int, value: Any="") -> int:
    #     e = self.add_edge([s], [t], value, hyper=False)
    #     return e

    def add_inputs(self, inp: List[int]) -> None:
        i1 = len(self._inputs)
        i2 = i1 + len(inp)
        self._inputs += inp
        for i in range(i1, i2):
            v = self._inputs[i]
            self.vdata[v].in_indices.add(i)

    def add_outputs(self, outp: List[int]) -> None:
        i1 = len(self._outputs)
        i2 = i1 + len(outp)
        self._outputs += outp
        for i in range(i1, i2):
            v = self._outputs[i]
            self.vdata[v].out_indices.add(i)

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
            v1 = self.add_vertex(vd.x, vd.y,
                                 vd.vtype, vd.size,
                                 vd.value)
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
        w = self.add_vertex(vd.x + 3, vd.y,
                            vd.vtype, vd.size,
                            vd.value)
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
    
    def tensor(self, other: Graph, layout: bool=True) -> None:
        """Take the monoidal product with the given graph

        Calling g.tensor(h) will turn g into g ⊗ h. Use the infix version "g + h" to simply return
        the tensor product without changing g.
        """
        vmap = dict()
        # emap = dict()

        if layout:
            max_self = max(max((self.vertex_data(v).y for v in self.vertices()), default = 0),
                           max((self.edge_data(e).y for e in self.edges()), default=0))
            min_other = min(min((other.vertex_data(v).y for v in other.vertices()), default = 0),
                            min((other.edge_data(e).y for e in other.edges()), default=0))

            for v in self.vertices(): self.vertex_data(v).y -= max_self
            for e in self.edges(): self.edge_data(e).y -= max_self
        else:
            min_other = 0

        for v in other.vertices():
            vd = other.vertex_data(v)
            vmap[v] = self.add_vertex(vd.x, vd.y - min_other + 1,
                                      vd.vtype, vd.size,
                                      vd.value)

        for e in other.edges():
            ed = other.edge_data(e)
            self.add_edge([vmap[v] for v in ed.s],
                          [vmap[v] for v in ed.t],
                          ed.value, ed.x, ed.y - min_other + 1, ed.fg, ed.bg, ed.hyper)
        
        # self.set_inputs(self.inputs() + [vmap[v] for v in other.inputs()])
        # self.set_outputs(self.outputs() + [vmap[v] for v in other.outputs()])
        self.add_inputs([vmap[v] for v in other.inputs()])
        self.add_outputs([vmap[v] for v in other.outputs()])

    def __mul__(self, other: Graph) -> Graph:
        g = self.copy()
        g.tensor(other)
        return g

    def compose(self, other: Graph) -> None:
        """Compose with a given graph in diagram order

        Note that composition is done in-place to the current graph.

        :param other: A graph to plug into the outputs of the current graph
        """
        codomain = self.codomain()
        domain = other.domain()
        if (not (isinstance(codomain, int) and isinstance(domain, int))
           and (len(codomain) != len(domain)
                or any(c != d for c, d in zip(domain, codomain)))):
            raise GraphError(
                f'Codomain {codomain} does not match domain {domain}'
            )

        vmap = dict()

        max_self = max(max((self.vertex_data(v).x for v in self.vertices()), default = 0),
                       max((self.edge_data(e).x for e in self.edges()), default=0))
        min_other = min(min((other.vertex_data(v).x for v in other.vertices()), default = 0),
                        min((other.edge_data(e).x for e in other.edges()), default=0))

        for v in self.vertices(): self.vertex_data(v).x -= max_self
        for e in self.edges(): self.edge_data(e).x -= max_self

        for v in other.vertices():
            vd = other.vertex_data(v)
            vmap[v] = self.add_vertex(vd.x - min_other, vd.y,
                                      vd.vtype, vd.size,
                                      vd.value)

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
        """Returns the composition of the current graph with `other`

        Composition is done in diagram order, and neither of the two graphs is changed.

        :param other: Another graph
        :returns: The composed graph
        """

        g = self.copy()
        g.compose(other)
        return g

    def highlight(self, vertices: Set[int], edges: Set[int]) -> None:
        """Set the `highlight` flag for a set of vertices and edges

        This tells the GUI to visually highlight a set of vertices/edges, e.g. by drawing them in bold.
        Any vertices/edges not in the sets provided will be un-highlighted.

        :param vertices: A set of vertices to highlight
        :param edges: A set of edges to highlight
        """

        for v, vd in self.vdata.items():
            vd.highlight = v in vertices
        for e, ed in self.edata.items():
            ed.highlight = e in edges

    def unhighlight(self) -> None:
        """Clear the `highlight` flag for all vertices/edges

        This is equivalent to calling :func:`highlight` with empty sets of vertices/edges.
        """

        for vd in self.vdata.values():
            vd.highlight = False
        for ed in self.edata.values():
            ed.highlight = False

def gen(value: str,
        domain: list[VType] | int, codomain: list[VType] | int,
        fg: str='', bg: str='') -> Graph:
    """Returns a graph with a single hyperedge and given number of inputs/outputs

    :param value: The label for the hyperedge
    :param arity: The number of input vertices connected to the source of the edge
    :param coarity: The number of output vertices connected to the target of the edge
    :param fg: An optional foregraph color, given as a 6-digit RGB hex code
    :param bg: An optional background color, given as a 6-digit RGB hex code
    """

    g = Graph()
    if type(domain) is not type(codomain):
        raise ValueError(
            f'Conflicting input/output types {type(domain)}'
            + f'and {type(codomain)}')
    if isinstance(domain, int) and isinstance(codomain, int):
        inputs = [g.add_vertex(-1.5, i - (domain-1)/2)
                  for i in range(domain)]
        outputs = [g.add_vertex(1.5, i - (codomain-1)/2)
                   for i in range(codomain)]
    else:
        inputs = [g.add_vertex(-1.5, i - (i-1)/2, vtype)
                  for i, vtype in enumerate(domain)]
        outputs = [g.add_vertex(1.5, i - (i-1)/2, vtype)
                   for i, vtype in enumerate(codomain)]
    g.add_edge(inputs, outputs, value, fg=fg, bg=bg)
    g.set_inputs(inputs)
    g.set_outputs(outputs)
    return g
        
def perm(p: List[int], domain: list[VType] | None = None) -> Graph:
    """Returns a graph corresponding to the given permutation

    This takes a permution, given as a list [x0,..,x(n-1)], which is interpreted as the permutation { x0 -> 0, x1 -> 1, ..., x(n-1) -> n-1 }.
    It produces a graph consisting just of vertices, where input xj is mapped to the same vertex as output j, representing an identity
    wire connecting input xj to output j.

    Note this is one of two reasonable conventions for specifying a permutation as a list of numbers. This one has the property, e.g.
    for graphs aj : 0 -> 1, we have: (a0 * a1 * a2) >> perm([2, 0, 1]) = a2 * a0 * a1.

    :param p: A permutation, given as an n-element list of integers from 0 to n-1.
    """

    g = Graph()
    size = len(p)
    if domain is None:
        inputs = [g.add_vertex(0, i - (size-1)/2) for i in range(size)]
    else:
        if len(domain) != size:
            raise ValueError(
                f'Domain {domain} does not match length of permutation.')
        inputs = [g.add_vertex(0, i - (size-1)/2, d)
                  for i, d in enumerate(domain)]
    outputs = [inputs[p[i]] for i in range(size)]
    g.set_inputs(inputs)
    g.set_outputs(outputs)
    return g

def identity(vtype: VType = None) -> Graph:
    """Returns a graph corresponding to the identity map

    This graph has a single vertex which is both an input and an output.
    """

    g = Graph()
    v = g.add_vertex(0, 0, vtype)
    g.set_inputs([v])
    g.set_outputs([v])
    return g

# def wide_id() -> Graph:
#     return gen("id", 1, 1)

# def id_perm(p: List[int]) -> Graph:
#     g = Graph()
#     size = len(p)
#     inputs = [g.add_vertex(-1.5, i - (size-1)/2) for i in range(size)]
#     outputs = [g.add_vertex(1.5, i - (size-1)/2) for i in range(size)]

#     for i in range(size):
#         y = i - (size-1)/2
#         g.add_edge([inputs[i]], [outputs[p[i]]], "id", 0, y)

#     g.set_inputs(inputs)
#     g.set_outputs(outputs)

#     return g

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
    return g
