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
import math
# from typing import Optional, List, Tuple

from .graph import Graph

def layer_layout(g: Graph):
    layer = list(g.inputs())
    edges = set(g.edges())
    done = set()

    x = 0
    while len(edges) > 0:
        for i, v in enumerate(layer):
            g.vertex_data(v).x = x
            g.vertex_data(v).y = len(layer)/2 - i
            done.add(v)
        
        layer = []
        new_layer = []
        for e in edges:
            src = g.source(e)
            if all(v in done for v in src):
                new_layer.append((sum(g.vertex_data(v).y for v in src) / len(src), e, g.target(e)))
        if len(new_layer) == 0:
            raise ValueError("Could not make progress. Is graph acyclic?")

        list.sort(new_layer)
        for center, e, vs in new_layer:
            g.edge_data(e).x = x + 1.5

            # FIXME using center coordinate of inputs could layout boxes on top of each other
            g.edge_data(e).y = center
            edges.remove(e)
            layer += vs

        x += 3

    layer = g.outputs()
    for i, v in enumerate(layer):
        g.vertex_data(v).x = x
        g.vertex_data(v).y = len(layer)/2 - i

    shift = math.floor(x / 2)
    for v in g.vertices(): g.vertex_data(v).x -= shift
    for e in g.edges(): g.edge_data(e).x -= shift
    
