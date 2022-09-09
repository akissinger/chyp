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
            s: List[int]=None,
            t: List[int]=None,
            x: float=0,
            y: float=0,
            value: Any="",
            hyper: bool=True) -> None:
        self.value = value
        self.x = x
        self.y = y
        self.s = [] if s is None else s
        self.t = [] if t is None else t
        self.hyper = hyper

class Graph:
    def __init__(self) -> None:
        self.vdata: Dict[int, VData] = {}
        self.edata: Dict[int, EData] = {}
        self._inputs: List[int] = []
        self._outputs: List[int] = []
        self.vindex = 0
        self.eindex = 0

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

    def add_vertex(self, x:float=0, y:float=0, value: Any="") -> int:
        v = self.vindex
        self.vindex += 1
        self.vdata[v] = VData(x, y, value)
        return v

    def add_edge(self, s:List[int], t:List[int], x:float=0, y:float=0, value: Any="") -> int:
        e = self.eindex
        self.eindex += 1
        self.edata[e] = EData(s, t, x, y, value)
        for v in s: self.vdata[v].out_edges.add(e)
        for v in t: self.vdata[v].in_edges.add(e)
        return e

    def add_simple_edge(self, s:int, t:int, value: Any="") -> int:
        e = self.add_edge([s], [t], value)
        self.edata[e].hyper = False
        return e

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
