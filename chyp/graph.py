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
from typing import Set, List, Dict, Iterator, Any, Optional
import json
import copy

class VData:
    def __init__(self, x: float=0, y: float=0, value: Any="") -> None:
        self.value = value
        self.x = x
        self.y = y

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
            hyper: bool=True) -> None:
        self.value = value
        self.x = x
        self.y = y
        self.s = [] if s is None else s
        self.t = [] if t is None else t
        self.hyper = hyper

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

    def add_edge(self, s:List[int], t:List[int], value:Any="", x:float=0, y:float=0, hyper:bool=True, name:int=-1) -> int:
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

        self.edata[e] = EData(s, t, value, x, y, hyper)
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

    def insert_id_after(self, v: int) -> int:
        """Insert a new identity hyperedge with source at the given vertex and redirect any out-edges or
        outputs to the target of the new hyperedge."""
        vd = self.vertex_data(v)
        w = self.add_vertex(vd.x + 3, vd.y, vd.value)
        wd = self.vertex_data(w)
        self.set_outputs([x if x != v else w for x in self.outputs()])
        for e in vd.out_edges:
            ed = self.edge_data(e)
            ed.s = [x if x != v else w for x in ed.s]
            wd.out_edges.add(e)
        vd.out_edges.clear()

        return self.add_edge([v], [w], "id", vd.x + 1.5, vd.y)

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
                   x=float(ed["x"]) if "x" in ed else 0.0,
                   y=float(ed["y"]) if "y" in ed else 0.0,
                   value=ed["value"] if "value" in ed else "",
                   hyper=bool(ed["hyper"]) if "hyper" in ed else True,
                   name=int(e))

    g.set_inputs([int(v) for v in j["inputs"]])
    g.set_outputs([int(v) for v in j["outputs"]])
    g.update_indices()
    return g
