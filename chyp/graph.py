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
from typing import Iterable, Iterator, Any
from typing import TypeAlias
import json
import copy
from .polynomial import Polynomial, const_poly


# Non-default vertex types are identified by a string label
VType: TypeAlias = str | None


class GraphError(Exception):
    """An error occurred in the graph backend."""


class VData:
    """Data associated with a single vertex."""

    vtype: VType
    """The vertex type."""

    size: Polynomial
    """The register size (number of bundled parallel wires) of the vertex."""

    infer_type: bool
    """Whether to infer the vertex type during composition. Used for
    special generators (identities, permutations, redistributers)."""

    infer_size: bool
    """Whether to infer the vertex size during composition. Used for special
    generators (identities, permutations, redistributers)."""

    x: float
    """x-coordinate at which to draw the vertex"""

    y: float
    """y-coordinate at which to draw the vertex"""

    in_edges: set[int]
    """Integer identifiers of input hyperedges of this vertex"""

    out_edges: set[int]
    """Integer identifiers of output hyperedges of this vertex"""

    in_indices: set[int]
    """Indices (if any) where this vertex occurs in the input lists of the hypergraph."""

    out_indices: set[int]
    """Indices (if any) where this vertex occurs in the output lists of the hypergraph."""

    highlight: bool
    """Flag indicating whether to visually highlight this vertex"""

    value: Any
    """A field that can hold arbitrary data attached to a vertex"""

    def __init__(self,
                 vtype: VType = None, size: Polynomial = const_poly(1),
                 infer_type: bool = False, infer_size: bool = False,
                 x: float = 0.0, y: float = 0.0,
                 value: Any = None) -> None:
        """Initialize a VData instance."""

        # Graph logic attributes
        self.vtype = vtype
        self.size = size
        self.infer_type = infer_type
        self.infer_size = infer_size

        # Drawing attributes
        self.x = x
        self.y = y
        self.highlight = False
        self.value = value

        # Integer identifiers of input and output hyperedges of this vertex -
        # useful for finding neighbouring hyperedges.
        self.in_edges: set[int] = set()
        self.out_edges: set[int] = set()

        # Indices (if any) where this vertex occurs in the input and output
        # lists of the hypergraph.
        self.in_indices: set[int] = set()
        self.out_indices: set[int] = set()


class EData:
    """Data associated with a single edge."""

    s: list[int]
    """The source vertex list of the hyperedge."""

    t: list[int]
    """The target vertex list of the hyperedge."""

    x: float
    """x-coordinate at which to draw the hyperedge."""

    y: float
    """y-coordinate at which to draw the hyperedge."""

    fg: str
    """Hex code for the text and outline color of the hyperedge."""

    bg: str
    """Hex code for the box fill color of the hyperedge."""

    hyper: bool
    """Whether to draw this hyperedge as a box or as line connecting two
    vertices (currently not implemented)."""

    highlight: bool
    """Flag indicating whether to visually highlight this edge"""

    value: Any
    """A field that can hold arbitrary data attached to a edge"""

    def __init__(self,
                 s: list[int] | None = None, t: list[int] | None = None,
                 value: Any = None,
                 x: float = 0.0, y: float = 0.0,
                 fg: str = '', bg: str = '',
                 hyper: bool = True) -> None:
        """Initialize an EData instance."""

        # Graph logic attributes
        self.s = [] if s is None else s
        self.t = [] if t is None else t

        # Drawing attributes
        self.x = x
        self.y = y
        self.fg = fg
        self.bg = bg
        self.highlight = False
        self.hyper = hyper
        self.value = value

    def __repr__(self) -> str:
        return f'Edge: {self.value} ({self.x}, {self.y})'

    def box_size(self) -> int:
        """Return how many width 'units' this box needs to display nicely.

        This uses a simple rule:
            - If the number of inputs and outputs are both <= 1, draw as a small
              (1 width unit) box.
            - Otherwise draw as a larger (size 2) box.

        """
        return 1 if len(self.s) <= 1 and len(self.t) <= 1 else 2


class Graph:
    """A hypergraph with boundaries.

    This is the main data structure used by Chyp. It represents a directed
    hypergraph (which we call simply a "graph") as two dictionaries for
    vertices and (hyper)edges, respectively. Each vertex is associated with a
    `VData` object and edge edge with an `EData` object, which stores
    information about adjacency, position, label, etc.

    The particular flavor of hypergraphs we use associate to each hyperedge a
    list of source vertices and a list of target vertices. The hypergraph
    itself also has a list of input vertices and a list of output vertices,
    which are used for sequential composition and rewriting.
    """

    vdata: dict[int, VData]
    """Mapping from integer identifiers of each vertex to its data."""

    edata: dict[int, EData]
    """Mapping from integer identifiers of each hyperedge to its data."""

    def __init__(self) -> None:
        self.vdata: dict[int, VData] = {}
        self.edata: dict[int, EData] = {}
        self._inputs: list[int] = []
        self._outputs: list[int] = []
        self._vindex = 0
        self._eindex = 0
                

    def copy(self) -> Graph:
        """Return a copy of the graph."""
        g = Graph()
        g.vdata = copy.deepcopy(self.vdata)
        g.edata = copy.deepcopy(self.edata)
        g._inputs = self._inputs.copy()
        g._outputs = self._outputs.copy()
        g._vindex = self._vindex
        g._eindex = self._eindex
        return g

    def vertices(self) -> Iterator[int]:
        """Return an iterator over the vertices in the graph."""
        return iter(self.vdata.keys())

    def edges(self) -> Iterator[int]:
        """Return an iterator over the edges in the graph."""
        return iter(self.edata.keys())

    def num_vertices(self) -> int:
        """Return the number of vertices in the graph."""
        return len(self.vdata)

    def num_edges(self) -> int:
        """Return the number of edges in the graph."""
        return len(self.edata)

    def vars(self):
        vmap = []
        
        for typ, p in self.domain() + self.codomain():
            vmap.append((tuple(p.subs), p))
            
        return vmap

    def domain(self) -> list[tuple[VType, Polynomial]]:
        """Return the domain of the graph.

        This consists of a list of pairs (vertex type, register size)
        corresponding to each input vertex.
        """
        domain = [(self.vertex_data(vertex).vtype,
                   self.vertex_data(vertex).size)
                  for vertex in self.inputs()]
        return domain

    def codomain(self) -> list[tuple[VType, Polynomial]]:
        """Return the domain of the graph.

        This consists of a list of pairs (vertex type, register size)
        corresponding to each output vertex.
        """
        codomain = [(self.vertex_data(vertex).vtype,
                     self.vertex_data(vertex).size)
                    for vertex in self.outputs()]
        return codomain

    def vertex_data(self, v: int) -> VData:
        """Return the :class:`VData` associated with vertex id `v`.

        Args:
            v: Integer identifier of the vertex.
        """
        return self.vdata[v]

    def edge_data(self, e: int) -> EData:
        """Return the :class:`EData` associated with edge id `e`.

        Args:
            e: Integer identifier of the edge.
        """
        return self.edata[e]

    def edge_domain(self, edge_id: int) -> list[tuple[VType, int]]:
        """Return the domain of edge with id `edge_id`.

        This consists of a list of pairs (vertex type, register size)
        corresponding to each input vertex of the edge.

        Args:
            edge_id: Integer identifier of the edge
                     whose domain will be returned.
        """
        domain = [(self.vertex_data(vertex).vtype,
                   self.vertex_data(vertex).size)
                  for vertex in self.source(edge_id)]
        return domain

    def edge_codomain(self, edge_id: int) -> list[tuple[VType, int]]:
        """Return the codomain of edge with id `edge_id`.

        This consists of a list of pairs (vertex type, register size)
        corresponding to each output vertex of the edge.

        Args:
            edge_id: Integer identifier of the edge
                     whose codomain will be returned.
        """
        codomain = [(self.vertex_data(vertex).vtype,
                     self.vertex_data(vertex).size)
                    for vertex in self.target(edge_id)]
        return codomain

    def in_edges(self, v: int) -> set[int]:
        """Return the set of edge ids for which vertex id `v` is a target.

        Args:
            v: Integer identifier of the vertex.
        """
        return self.vdata[v].in_edges

    def out_edges(self, v: int) -> set[int]:
        """Return the set of edge ids for which vertex id `v` is a source.

        Args:
            v: Integer identifier of the vertex.
        """
        return self.vdata[v].out_edges

    def source(self, e: int) -> list[int]:
        """Return the list of source vertex ids of edge with id `e`.

        Args:
            e: Integer identifier of the edge.
        """
        return self.edata[e].s

    def target(self, e: int) -> list[int]:
        """Return the list of target vertex ids of edge with id `e`.

        Args:
            e: Integer identifier of the edge.
        """
        return self.edata[e].t

    def add_vertex(self,
                   vtype: VType = None, size: int = 1,
                   infer_type: bool = False, infer_size: bool = False,
                   x: float = 0.0, y: float = 0.0,
                   value: Any = '', name: int = -1) -> int:
        """Add a new vertex to the graph.

        Args:
            vtype: The vertex type.
            size: The register size (number of bundled parallel wires)
                  of the vertex.
            infer_type: Whether to infer the vertex type during composition.
                        Used for special generators (identities, permutations,
                        redistributers).
            infer_size: Whether to infer the vertex size during composition.
                        Used for special generators (identities, permutations,
                        redistributers).

            x: x-coordinate at which to draw the vertex.
            y: y-coordinate at which to draw the vertex.

            value: The value carried by this vertex (currently unused).
            name: The integer identifier to use for this vertex. If this is
                  set to -1, the identifier is set automatically.
                  (Note: no checks are currently made to ensure the identifier
                  is not already in use).
        """
        if name == -1:
            v = self._vindex
            self._vindex += 1
        else:
            v = name
            max_index = max(name, self._vindex)
            self._vindex = max_index + 1

        self.vdata[v] = VData(
            vtype=vtype, size=size,
            infer_type=infer_type, infer_size=infer_size,
            x=x, y=y, value=value
        )
        return v

    def add_edge(self,
                 s: list[int], t: list[int], value: Any = '',
                 x: float = 0.0, y: float = 0.0,
                 fg: str = '', bg: str = '',
                 hyper: bool = True, name: int = -1) -> int:
        """Add a new hyperedge to the graph.

        Args:
            s: A list of source vertex ids.
            t: A list of target vertex ids.
            value: The value carried by this edge (currently unused).
            x: x-coordinate at which to draw the hyperedge.
            y: y-coordinate at which to draw the hyperedge.
            fg: Hex code for the text and outline color of the hyperedge.
            bg: Hex code for the box fill color of the hyperedge.
            hyper: Whether to draw this hyperedge as a box or as line connecting
                   two vertices (currently not implemented).
            name: The integer identifier to use for this vertex. If this is
                  set to -1, the identifier is set automatically.
                  (Note: no checks are currently made to ensure the identifier
                  is not already in use).
        """
        if name == -1:
            e = self._eindex
            self._eindex += 1
        else:
            e = name
            max_index = max(name, self._eindex)
            self._eindex = max_index + 1

        self.edata[e] = EData(s, t, value, x, y, fg, bg, hyper)
        for v in s:
            self.vdata[v].out_edges.add(e)
        for v in t:
            self.vdata[v].in_edges.add(e)
        return e

    def remove_vertex(self, v: int, strict: bool = False) -> None:
        """Remove a vertex from the graph.

        This removes a single vertex.
        If `strict` is set to True, then the
        vertex must have no adjacent edges nor be a boundary vertex.
        If `strict` is False, then `v` will be removed from the
        source/target list of all adjacent edges and removed from the
        boundaries, if applicable.

        Args:
            v: Integer identifier of the vertex to remove.
            strict: If True, require the vertex to have no adjacent edges
                    and not be a boundary vertex.
        """
        if strict:
            if (len(self.vertex_data(v).in_edges) > 0 or
               len(self.vertex_data(v).out_edges) > 0):
                raise ValueError('Attempting to remove vertex with adjacent'
                                 + 'edges while strict == True.')
            if (v in self.inputs() or v in self.outputs()):
                raise ValueError('Attempting to remove boundary vertex while'
                                 + 'strict == True.')
        else:
            for e in self.vertex_data(v).in_edges:
                self.edge_data(e).t = [v1 for v1 in self.edge_data(e).t
                                       if v1 != v]
            for e in self.vertex_data(v).out_edges:
                self.edge_data(e).s = [v1 for v1 in self.edge_data(e).s
                                       if v1 != v]
            self.set_inputs([v1 for v1 in self.inputs() if v1 != v])
            self.set_outputs([v1 for v1 in self.outputs() if v1 != v])
        del self.vdata[v]

    def remove_edge(self, e: int) -> None:
        """Remove an edge from the graph.

        Args:
            e: Integer identifier of the edge to remove.
        """
        for v in self.edge_data(e).s:
            self.vertex_data(v).out_edges.remove(e)
        for v in self.edge_data(e).t:
            self.vertex_data(v).in_edges.remove(e)
        del self.edata[e]

    # def add_simple_edge(self, s:int, t:int, value: Any="") -> int:
    #     e = self.add_edge([s], [t], value, hyper=False)
    #     return e

    def add_inputs(self, inp: list[int]) -> None:
        """Append `inp` to the inputs of the graph.

        Args:
            inp: The list of vertex integer identifiers
                 of the appended inputs.
        """
        i1 = len(self._inputs)
        i2 = i1 + len(inp)
        self._inputs += inp
        # Register the input indices with the vertex data instances.
        for i in range(i1, i2):
            v = self._inputs[i]
            self.vdata[v].in_indices.add(i)

    def add_outputs(self, outp: list[int]) -> None:
        """Append `outp` to the outputs of the graph.

        Args:
            outp: The list of vertex integer identifiers
                  of the appended outputs.
        """
        i1 = len(self._outputs)
        i2 = i1 + len(outp)
        self._outputs += outp
        # Register the output indices with the vertex data instances.
        for i in range(i1, i2):
            v = self._outputs[i]
            self.vdata[v].out_indices.add(i)

    def set_inputs(self, inp: list[int]) -> None:
        """Set the inputs of the graph to `inp`.

        Args:
            inp: The list of vertex integer identifiers of the new inputs.
        """
        self._inputs = inp
        for d in self.vdata.values():
            d.in_indices.clear()
        # Register the input indices with the vertex data instances.
        for i, v in enumerate(self._inputs):
            self.vdata[v].in_indices.add(i)

    def set_outputs(self, outp: list[int]) -> None:
        """Set the outputs of the graph to `outp`.

        Args:
            outp: The list of vertex integer identifiers of the new outputs.
        """
        self._outputs = outp
        for d in self.vdata.values():
            d.out_indices.clear()
        # Register the output indices with the vertex data instances.
        for i, v in enumerate(self._outputs):
            self.vdata[v].out_indices.add(i)

    def inputs(self) -> list[int]:
        """Return the list of vertex ids of the graph inputs."""
        return self._inputs

    def outputs(self) -> list[int]:
        """Return the list of vertex ids of the graph outputs."""
        return self._outputs

    def is_input(self, v: int) -> bool:
        """Return whether vertex id `v` is in the graph inputs.

        Args:
            v: Integer identifier of the vertex to check.
        """
        return len(self.vdata[v].in_indices) > 0

    def is_output(self, v: int) -> bool:
        """Return whether vertex id `v` is in the graph outputs.

        Args:
            v: Integer identifier of the vertex to check.
        """
        return len(self.vdata[v].out_indices) > 0

    def is_boundary(self, v: int) -> bool:
        """Return whether vertex id `v` lies on the graph boundary.

        Args:
            v: Integer identifier of the vertex to check.
        """
        return self.is_input(v) or self.is_output(v)

    def successors(self, vs: Iterable[int]) -> set[int]:
        """Return vertices that lie on a directed path from any of `vs`.

        Args:
            v: Integer identifiers of the vertices to find successors of.
        """
        succ: set[int] = set()
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
        """Merge vertex `w` into vertex `v`.

        Form the quotient of the graph by identifying v with w.
        Afterwards, the quotiented vertex will be have integer identifier `v`.

        Args:
            v: Integer identifier of the vertex into which to merge `w`.
            w: Integer identifier of the vertex to merge into `v`.
        """
        vd = self.vertex_data(v)
        # print("merging %s <- %s" % (v, w))

        # Where vertex `w` occurs as an edge target, replace it with `v`
        for e in self.in_edges(w):
            ed = self.edge_data(e)
            ed.t = [v if x == w else x for x in ed.t]
            vd.in_edges.add(e)

        # Where vertex `w` occurs as an edge source, replace it with `v`
        for e in self.out_edges(w):
            ed = self.edge_data(e)
            ed.s = [v if x == w else x for x in ed.s]
            vd.out_edges.add(e)

        # Wherever `w` occurs on the graph boundary, replace it with `v`
        self.set_inputs([v if x == w else x for x in self.inputs()])
        self.set_outputs([v if x == w else x for x in self.outputs()])

        # Remove references to `w` from the graph
        self.remove_vertex(w)

    def explode_vertex(self, v: int) -> tuple[list[int], list[int]]:
        """Split a vertex into copies for each input, output, and tentacle.

        This is used for computing pushout complements of rules that aren't
        left-linear.
        (See arXiv:2012.01847 Section 3.3 for definition of left-linear).

        Args:
            v: Integer identifier of vertex to be exploded.

        Returns:
            A pair of lists containing the new input-like and output-like
            vertices, respectively.
        """
        new_vs: tuple[list[int], list[int]] = ([], [])
        vd = self.vertex_data(v)

        def fresh(j: int) -> int:
            """Creates a new vertex with the same data as `v`.

            The integer identifier of the new vertex is recorded in either
            the list of new input-like vertices or the list of new output-like
            vertices, depending on the value of `j`.

            Args:
                j: If 0, the new vertex is added to the list of new input-like
                   vertices. If 1, the new vertex is added to the list of
                   new output-like vertices.
            """
            v1 = self.add_vertex(
                vtype=vd.vtype, size=vd.size,
                x=vd.x, y=vd.y, value=vd.value
            )
            new_vs[j].append(v1)
            return v1

        # Replace any occurences of the original vertex in the graph inputs
        # with a new input-like vertex.
        self.set_inputs([v1 if v1 != v else fresh(0) for v1 in self.inputs()])
        # Where the original vertex is the target of a hyperedge, replace its
        # occurence in the hyperedge's target list with a new input-like
        # vertex and register this with the new vertex's data instance.
        for e in vd.in_edges:
            ed = self.edge_data(e)
            for i in range(len(ed.t)):
                if ed.t[i] == v:
                    ed.t[i] = fresh(0)
                    self.vertex_data(ed.t[i]).in_edges.add(e)

        # Replace any occurences of the original vertex in the graph outputs
        # with a new output-like vertex.
        self.set_outputs([v1 if v1 != v else fresh(1)
                          for v1 in self.outputs()])
        # Where the original vertex is the source of a hyperedge, replace its
        # occurence in the hyperedge's target list with a new output-like
        # vertex and register this with the new vertex's data instance.
        for e in vd.out_edges:
            ed = self.edge_data(e)
            for i in range(len(ed.s)):
                if ed.s[i] == v:
                    ed.s[i] = fresh(1)
                    self.vertex_data(ed.s[i]).out_edges.add(e)

        # Register the fact that `v` no longer occurs in as a source or target
        # of any hyperedge.
        vd.in_edges = set()
        vd.out_edges = set()
        # Remove `v` from the hypergraph, using strict == True to catch any
        # errors (no errors should be raised with current code).
        self.remove_vertex(v, strict=True)

        return new_vs

    def insert_id_after(self, v: int, reverse: bool = False) -> int:
        """Insert a new identity hyperedge after the given vertex.

        A new vertex is also created, which replaces the orignal vertex as the
        source of any edges in graph as well as any occurences of the original
        vertex in the graph outputs.

        Args:
            reverse: If `False`, the original vertex becomes the source of the
                     new identity hyperedge while the new vertex becomes the
                     target.
                     If `True`, the source and target of the new identity are
                     flipped. This can be used to break directed cycles, by
                     effectively introducing a cap and cup.
        """
        vd = self.vertex_data(v)

        # Create a new vertex with the same vtype and size
        w = self.add_vertex(
            vtype=vd.vtype, size=vd.size,
            x=vd.x + 3, y=vd.y, value=vd.value
        )
        wd = self.vertex_data(w)
        # The new vertex is highlighted whenever the orignal vertex is.
        wd.highlight = vd.highlight

        # Replace any occurences of the original vertex in the graph outputs
        # with the new vertex.
        self.set_outputs([x if x != v else w for x in self.outputs()])
        # Where the original vertex is the source of a hyperedge, replace it
        # with the new vertex and register this change with the data instance
        # of each vertex.
        for e in vd.out_edges:
            ed = self.edge_data(e)
            ed.s = [x if x != v else w for x in ed.s]
            wd.out_edges.add(e)
        vd.out_edges.clear()

        # Assign the orignal and new vertex as source or target of the new
        # identity edge, based on the `reverse` argument.
        s, t = ([v], [w]) if not reverse else ([w], [v])

        # Create the new identity edge.
        e = self.add_edge(s, t, 'id', vd.x + 1.5, vd.y)
        # The new edge is highlighted whenever the original vertex is.
        self.edge_data(e).highlight = vd.highlight
        return e

    def tensor(self, other: Graph, layout: bool = True) -> None:
        """Take the monoidal product of this graph in-place with another.

        Calling g.tensor(h) will turn g into g ⊗ h, performing the operation
        in-place. Use the infix version `g @ h` to simply return the tensor
        product without changing g.

        Args:
            other: The graph with which to take the monoidal product.
            layout: If `True`, compute new y-coordinates of the vertices and
                    edges of the resulting graph so that the two graphs in the
                    tensor product are adjacent with no overlap in the
                    y-direction.
        """
        # Mapping used to match which new vertex added to this graph each
        # vertex of the other graph corresponds to.
        # Used when computing connectivity of edges copied over from the
        # other graph.
        vmap = dict()
        # emap = dict()

        if layout:
            # Compute the max y-coordinate of the edges and vertices in this
            # graph.
            max_self = max(
                max((self.vertex_data(v).y for v in self.vertices()),
                    default=0),
                max((self.edge_data(e).y for e in self.edges()), default=0)
            )
            # Compute the min y-coordinate of the edges and vertices in the
            # other graph.
            min_other = min(
                min((other.vertex_data(v).y for v in other.vertices()),
                    default=0),
                min((other.edge_data(e).y for e in other.edges()), default=0)
            )
            # Shift all vertices and edges of this graph below the y-axis.
            for v in self.vertices():
                self.vertex_data(v).y -= max_self
            for e in self.edges():
                self.edge_data(e).y -= max_self
        else:
            min_other = 0

        # Copy the vertices and edges of the other graph to this one, with all
        # vertices and edges shifted above the y-axis if layout == True.
        for v in other.vertices():
            vd = other.vertex_data(v)
            vmap[v] = self.add_vertex(
                vtype=vd.vtype, size=vd.size,
                infer_type=vd.infer_type, infer_size=vd.infer_size,
                x=vd.x, y=vd.y - min_other + 1, value=vd.value
            )
        for e in other.edges():
            ed = other.edge_data(e)
            self.add_edge([vmap[v] for v in ed.s],
                          [vmap[v] for v in ed.t],
                          ed.value, ed.x, ed.y - min_other + 1,
                          ed.fg, ed.bg, ed.hyper)

        # self.set_inputs(self.inputs() + [vmap[v] for v in other.inputs()])
        # self.set_outputs(self.outputs() + [vmap[v] for v in other.outputs()])

        # Add the inputs and outputs of the other graph to this one.
        self.add_inputs([vmap[v] for v in other.inputs()])
        self.add_outputs([vmap[v] for v in other.outputs()])

    def __mul__(self, other: Graph) -> Graph:
        """Return the tensor product of this graph with another.

        This does not modify either of the original graphs.
        """
        g = self.copy()
        g.tensor(other)
        return g

    def compose(self, other: Graph) -> None:
        """Sequentially compose this graph in-place with another.

        Calling g.compose(h) will turn g into g ; h, performing the operation
        in-place. Use the infix version `g >> h` to simply return the
        sequential composition without changing g.

        Args:
            other: The graph with which to take the sequential composition.
        """
        self_outputs = self.outputs()
        other_inputs = other.inputs()

        # Check that codomain of this graph matches the domain of the other:
        # this is required for valid sequential composition.
        if len(self_outputs) != len(other_inputs):
            raise GraphError(
                f'Codomain {self.codomain()} does not '
                + f'match domain {other.domain()}'
            )
        for output_id, input_id in zip(self_outputs, other_inputs):
            output_data = self.vertex_data(output_id)
            input_data = other.vertex_data(input_id)
            if output_data.vtype != input_data.vtype:
                if not (output_data.infer_type or input_data.infer_type):
                    raise GraphError(
                        f'Codomain {self.codomain()} does not '
                        + f'match domain {other.domain()}'
                    )
            if output_data.size != input_data.size:
                if not (output_data.infer_size or input_data.infer_size):
                    raise GraphError(
                        f'Codomain {self.codomain()} does not '
                        + f'match domain {other.domain()}'
                    )

        vmap = dict()

        # Compute the max x-coordinate of the edges and vertices
        # in this graph.
        max_self = max(
            max((self.vertex_data(v).x for v in self.vertices()), default=0),
            max((self.edge_data(e).x for e in self.edges()), default=0)
        )
        # Compute the min x-coordinate of the edges and vertices
        # in the other graph.
        min_other = min(
            min((other.vertex_data(v).x for v in other.vertices()),
                default=0),
            min((other.edge_data(e).x for e in other.edges()), default=0)
        )

        # Shift all vertices and edges of this graph below the x-axis.
        for v in self.vertices():
            self.vertex_data(v).x -= max_self
        for e in self.edges():
            self.edge_data(e).x -= max_self

        # Copy the vertices and edges of the other graph to this one, with all
        # vertices and edges shifted above the x-axis.
        for v in other.vertices():
            vd = other.vertex_data(v)
            vmap[v] = self.add_vertex(
                vtype=vd.vtype, size=vd.size,
                infer_type=vd.infer_type, infer_size=vd.infer_size,
                x=vd.x - min_other, y=vd.y, value=vd.value
            )
        for e in other.edges():
            ed = other.edge_data(e)
            self.add_edge([vmap[v] for v in ed.s],
                          [vmap[v] for v in ed.t],
                          ed.value, ed.x - min_other, ed.y,
                          ed.fg, ed.bg, ed.hyper)

        # 'Plug' the two graphs together. In other words, merge the input
        # vertices of other into the corresponding output vertices of `self`.
        plug1 = self.outputs()
        plug2 = [vmap[v] for v in other.inputs()]
        if len(plug1) != len(plug2):
            raise GraphError(f'Attempting to plug a graph with {len(plug1)} '
                             + f'outputs into one with {len(plug2)} inputs')

        # The outputs of the composed graph are the outputs of `other`
        # The outputs can only be set once we have assigned a copy of
        # the outputs of `self` to `plug1` above.
        self.set_outputs([vmap[v] for v in other.outputs()])

        # `quotient` will keep track of which vertices
        # have been merged into which.
        quotient: dict[int, int] = dict()
        # Go through pairs of vertices from each plug
        for p1, p2 in zip(plug1, plug2):
            # While vertex currently assigned to p1 has already been merged
            # into another vertex, repeatedly replace it with the vertex the
            # it was merged into until p1 is a vertex that has not already
            # been merged. Vice versa for p2.
            while p1 in quotient:
                p1 = quotient[p1]
            while p2 in quotient:
                p2 = quotient[p2]
            # If the resulting p1 and p2 are not the same vertex, merge them.
            if p1 != p2:
                data_1 = self.vertex_data(p1)
                data_2 = self.vertex_data(p2)
                # If both vertices have flexible types that are not equal,
                # raise an error due to ambiguity.
                if (data_1.infer_type and data_2.infer_type
                   and data_1.vtype != data_2.vtype):
                    raise GraphError(
                        'Ambiguous vertex type during composition.')
                # Otherwise, if one vertex has a flexible type, ensure
                # the vertex types match.
                elif data_1.infer_type:
                    data_1.vtype = data_2.vtype
                    data_1.infer_type = False
                elif data_2.infer_type:
                    data_2.vtype = data_1.vtype
                    data_2.infer_type = False
                # If both vertices have flexible sizes that are not equal,
                # raise an error due to ambiguity.
                if (data_1.infer_size and data_2.infer_size
                   and data_1.size != data_2.size):
                    raise GraphError(
                        'Ambiguous vertex size during composition.')
                # Otherwise, if one vertex has a flexible size, ensure
                # the vertex sizes match.
                elif data_1.infer_size:
                    data_1.size = data_2.size
                    data_1.infer_size = False
                elif data_2.infer_size:
                    data_2.size = data_1.size
                    data_2.infer_size = False

                self.merge_vertices(p1, p2)
                # Register than p2 has been merged into p1.
                quotient[p2] = p1

    def __rshift__(self, other: Graph) -> Graph:
        """Return the composition of the current graph with `other`.

        Composition is done in diagram order (`other` comes after `self`),
        and neither of the two graphs are modified.

        Args:
            other: Graph with which to compose `self`.
        """
        g = self.copy()
        g.compose(other)
        return g

    def highlight(self, vertices: set[int], edges: set[int]) -> None:
        """Set the `highlight` flag for a set of vertices and edges.

        This tells the GUI to visually highlight a set of vertices/edges,
        e.g. by drawing them in bold.
        Any vertices/edges not in the sets provided will be un-highlighted.

        Args:
            vertices: A set of vertices to highlight.
            edges: A set of edges to highlight.
        """
        for v, vd in self.vdata.items():
            vd.highlight = v in vertices
        for e, ed in self.edata.items():
            ed.highlight = e in edges

    def unhighlight(self) -> None:
        """Clear the `highlight` flag for all vertices/edges.

        This is equivalent to calling :func:`highlight` with empty sets
        of vertices/edges.
        """
        for vd in self.vdata.values():
            vd.highlight = False
        for ed in self.edata.values():
            ed.highlight = False


def gen(value: str,
        domain: list[tuple[VType, int]], codomain: list[tuple[VType, int]],
        infer_types: bool = False, infer_sizes: bool = False,
        fg: str = '', bg: str = '') -> Graph:
    """Return a graph with one hyperedge and given domain and codomain.

    Args:
        value: The label for the hyperedge.
        domain: A list of pairs (vertex type, register size) corresponding to
                each input vertex.
        codomain: A list of pairs (vertex type, register size) corresponding to
                each output vertex.
        fg: An optional foregraph color, given as a 6-digit RGB hex code.
        bg: An optional background color, given as a 6-digit RGB hex code.
    """
    g = Graph()
    inputs = [g.add_vertex(vtype=vtype, size=size,
                           infer_type=infer_types, infer_size=infer_sizes,
                           x=-1.5, y=i - (i-1)/2)
              for i, (vtype, size)
              in enumerate(domain)]
    outputs = [g.add_vertex(vtype=vtype, size=size,
                            infer_type=infer_types, infer_size=infer_sizes,
                            x=1.5, y=i - (i-1)/2)
               for i, (vtype, size)
               in enumerate(codomain)]
    g.add_edge(inputs, outputs, value, fg=fg, bg=bg)
    g.set_inputs(inputs)
    g.set_outputs(outputs)
    return g


def perm(p: list[int], domain: list[tuple[VType, int]],
         infer_type: bool = False, infer_size: bool = False) -> Graph:
    """Return a graph corresponding to the given permutation.

    This takes a permution, given as a list [x0,..,x(n-1)], which is
    interpreted as the permutation { x0 -> 0, x1 -> 1, ..., x(n-1) -> n-1 }.
    It produces a graph consisting just of vertices, where input xj is mapped
    to the same vertex as output j, representing an identity wire connecting
    input xj to output j.

    Note this is one of two reasonable conventions for specifying a
    permutation as a list of numbers.
    This one has the property, e.g. for graphs aj : 0 -> 1, we have:

        (a0 * a1 * a2) >> perm([2, 0, 1]) = a2 * a0 * a1.

    Args:
        p: A permutation given as an n-element list of integers from 0 to n-1.
        domain: The domain type of the permutation. This consists of a list of
                pairs (vertex type, register size) corresponding to each input
                vertex of the edge.
                If `None`, the domain is assumed to be the  appropriate number
                of default type vertices all with register size 1.
    """
    g = Graph()
    num_wires = len(p)
    if len(domain) != num_wires:
        raise GraphError(
            f'Domain {domain} does not match length of permutation.')
    inputs = [g.add_vertex(vtype=vtype, size=size,
                           infer_type=infer_type, infer_size=infer_size,
                           x=0, y=i - (num_wires-1)/2)
              for i, (vtype, size) in enumerate(domain)]
    outputs = [inputs[p[i]] for i in range(num_wires)]
    g.set_inputs(inputs)
    g.set_outputs(outputs)
    return g


def identity(vtype: VType = None, size: int = 1,
             infer_type: bool = False, infer_size: bool = False) -> Graph:
    """Return a graph corresponding to the identity map.

    This graph has a single vertex which is both an input and an output.

    Args:
        vtype: The input and output vertex type. Used in typed hypergraphs.
    """
    g = Graph()
    v = g.add_vertex(vtype=vtype, size=size,
                     infer_type=infer_type, infer_size=infer_size,
                     x=0, y=0)
    g.set_inputs([v])
    g.set_outputs([v])
    return g


def redistributer(domain: list[tuple[VType, int]],
                  codomain: list[tuple[VType, int]]) -> Graph:
    """Return a graph corresponding to a vertex size redistribution.

    A specific case of this family of graphs are 'dividers', which split a
    vertex of some type and size into multiple size 1 vertices of the same
    type. Conversely, 'gatherers' bundle multiple vertices of the same type
    into a single vertex of the same type and size the sum of the individual
    input vertex sizes.

    More generally, a conversion can be done between different lists of sizes,
    for some vertex type.

    Args:
        domain: A list of pairs (vertex type, register size) corresponding to
                each input vertex.
        codomain: A list of pairs (vertex type, register size) corresponding to
                each output vertex.
    """
    vtypes = set(vtype for vtype, _ in domain)
    vtypes.update(vtype for vtype, _ in codomain)
    if len(vtypes) > 1:
        raise GraphError('Size conversion cannot mix vertex types.')

    # Raise error if size conservation is violated
    domain_size = sum(size for _, size in domain)
    codomain_size = sum(size for _, size in codomain)
    if domain_size != codomain_size:
        raise GraphError(f'Sum of domain sizes ({domain_size}) does not equal'
                         + f'sum of codomain sizes ({codomain_size}).')

    return gen('_redistributer', domain, codomain)

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
    """Load a .chyp graph file from the given path."""

    with open(path) as f:
        g = graph_from_json(f.read())
    return g


def graph_from_json(json_string: str) -> Graph:
    """Load a graph from the given JSON string."""

    j = json.loads(json_string)
    g = Graph()
    for v, vd in j["vertices"].items():
        g.add_vertex(x=float(vd["x"] if "x" in vd else 0.0),
                     y=float(vd["y"] if "y" in vd else 0.0),
                     value=vd["value"] if "value" in vd else "",
                     name=int(v))
    for e, ed in j["edges"].items():
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
