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
from typing import Optional, List, Tuple, Set

from .graph import Graph

def ready_edges(g: Graph, edges: Set[int], v_done: Set[int]) -> Set[int]:
    ready = set()
    for e in edges:
        src = g.source(e)
        if all(v in v_done for v in src):
            ready.add(e)
    return ready

def layer_layout(g: Graph):
    """A simple hypergraph layout into evenly-spaced layers

    This layout adds identity boxes if wires need to cross more than one layer, and generally places vertices
    and boxes as early and near the x-axis as possible. It will throw an exception if the given graph is not
    directed acyclic.

    Currently it assumes graphs are monogamous. Expect strange behaviours if this is not the case.
    """
    layer = list(g.inputs())
    v_done = set(layer)
    edges = set(g.edges())

    x = 0
    while len(edges) > 0:
        for i, v in enumerate(layer):
            g.vertex_data(v).x = x
            g.vertex_data(v).y = len(layer)/2 - i
        
        layer = []
        new_layer = []
        for i, e in enumerate(ready_edges(g, edges, v_done)):
            c = sum(g.vertex_data(v).y for v in g.source(e)) / len(g.source(e))
            new_layer.append((c, e, g.target(e)))
            edges.remove(e)
        if len(new_layer) == 0:
            raise ValueError("Could not make progress. Is graph acyclic?")

        # sort according to center coordinate
        list.sort(new_layer)

        # forward pass, making enough space by shifting things above the x-axis up
        min = 0
        max = 0
        ctr = -1
        for i in range(len(new_layer)):
            c, e, vs = new_layer[i]
            if c < 0: continue
            pad = (g.edge_data(e).box_size() / 2)
            if ctr == -1:
                ctr = i
                max = c - pad
                min = c + pad
            else:
                if c < min + pad:
                    c = min + pad
                    min = c + pad
                    new_layer[i] = (c, e, vs)
            
        # backward pass, shifting things below the x-axis down
        for i in range(ctr-1, -1, -1):
            c, e, vs = new_layer[i]
            pad = (g.edge_data(e).box_size() / 2)
            if c > max - pad:
                c = max - pad
                max = c - pad
                new_layer[i] = (c, e, vs)



        for c, e, vs in new_layer:
            g.edge_data(e).x = x + 1.5

            g.edge_data(e).y = c
            for v in vs:
                layer.append(v)
                v_done.add(v)

        ready = ready_edges(g, edges, v_done)
        outputs = set(g.outputs())
        for v in layer:
            if (v in outputs and len(edges) > 0) or any(e not in ready for e in g.out_edges(v)):
                id = g.insert_id_after(v)
                edges.add(id)

        x += 3

    layer = g.outputs()
    for i, v in enumerate(layer):
        g.vertex_data(v).x = x
        g.vertex_data(v).y = len(layer)/2 - i

    shift = math.floor(x / 2)
    for v in g.vertices(): g.vertex_data(v).x -= shift
    for e in g.edges(): g.edge_data(e).x -= shift
    
