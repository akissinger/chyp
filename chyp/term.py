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

from typing import List
from .graph import Graph

# def ready_edges(g: Graph, edges: Set[int], v_pos: Mapping[int,float]) -> Set[int]:
#     ready = set()
#     for e in edges:
#         src = g.source(e)
#         if all(v in v_pos for v in src):
#             ready.add(e)
#     return ready

def layer_decomp(g: Graph) -> List[List[int]]:
    """Decompose a graph into regular and singular layers

    Returns a list, sorting the edges of `g` into layers. Note that this
    can modify `g` by introducing extra vertices and identity boxes.
    """

    e_layers = []
    v_layer = []
    v_placed = set()


    # first, mark all of the inputs as 'placed' and add dummy edges for any input that is also an output
    outputs = set(g.outputs())
    for v in g.inputs():
        if v in outputs: g.insert_id_after(v)
        v_layer.append(v)
        v_placed.add(v)
    
    new_ids = set()
    edges = set(g.edges())

    # next, place edges in layers
    while len(edges) > 0:
        ready = set()
        for e in edges:
            if all(v in v_placed for v in g.source(e)):
                ready.add(e)
        outputs = set(g.outputs())
        for v in v_layer:
            if v in outputs or any(e not in ready for e in g.out_edges(v)):
                id = g.insert_id_after(v)
                new_ids.add(id)
                ready.add(id)
        
        e_layer = []
        for e in ready:
            src = g.source(e)
            e_layer.append(e)
            edges.discard(e)
        if all(e in new_ids for e in e_layer):
            raise ValueError("Could not make progress. Is graph acyclic?")

        e_layers.append(e_layer)

        if len(edges) > 0:
            v_layer = []
            for e in e_layer:
                for v in g.target(e):
                    v_placed.add(v)
                    v_layer.append(v)

    # finally attempt to minimise crossings by sorting edges according to the ideal positions of their source and
    # target vertices. This is done in a forward (it=0) and backward (it=1) pass.
    for it in range(2):
        rng = range(len(e_layers)) if it == 0 else range(len(e_layers)-1,-1,-1)
        for j in rng:
            inp = [v for e in e_layers[j-1] for v in g.target(e)] if j > 0 else list(g.inputs())
            inp_pos = { v : i/len(inp) for i, v in enumerate(inp) }

            # during the forward pass, ignore the positions of outputs
            if it != 0:
                outp = [v for e in e_layers[j+1] for v in g.source(e)] if j < len(e_layers)-1 else list(g.outputs())
                outp_pos = { v : i/len(outp) for i, v in enumerate(outp) }
            else:
                outp_pos = None

            e_pos = {}
            for e in e_layers[j]:
                src = g.source(e)
                e_pos[e] = sum(inp_pos[v] for v in src)/len(src) if len(src) != 0 else 0

                # during the backward pass, weight the positions of outputs more heavily than inputs
                if outp_pos:
                    tgt = g.target(e)
                    e_pos[e] += 2 * sum(outp_pos[v] for v in tgt)/len(tgt) if len(tgt) != 0 else 0

            list.sort(e_layers[j], key=lambda e: e_pos[e])

    return e_layers

def perm_to_s(perm: List[int]) -> str:
    if len(perm) == 1:
        return 'id'
    elif len(perm) == 2:
        return 'sw'
    else:
        return 'sw' + str(perm)

def split_perm(perm: List[int]) -> List[List[int]]:
    """Split a permutation into a tensor product of independent permuations
    """
    perms = []
    rest = perm

    while rest != []:
        m = 0
        for i, x in enumerate(rest):
            m = max(x, m)
            if m <= i:
                perms.append(rest[:i+1])
                rest = [y-(i+1) for y in rest[i+1:]]
                break
    return perms


def graph_to_term(g: Graph) -> str:
    """Convert a graph to a term

    This currently only works for monogamous acyclic graphs (and hence symmetric monoidal
    terms).
    """

    g = g.copy()
    e_layers = layer_decomp(g)

    in_layer = list(g.inputs())

    # build a list of terms to be sequentially composed
    seq = []
    for i in range(len(e_layers)):
        # compute the permutation from the current vertex layer to inputs of the edge layer
        v_pos = { v : j for j,v in enumerate(in_layer) }
        out_layer = [v for e in e_layers[i] for v in g.source(e)]
        v_perm = [v_pos[v] for v in out_layer]

        # append it as a layer of swap maps
        if v_perm != list(range(len(v_perm))):
            perms = split_perm(v_perm)
            seq.append(' * '.join([perm_to_s(p) for p in perms]))

        # append the parallel composition of the current edge layer
        par = [str(g.edge_data(e).value) for e in e_layers[i]]
        seq.append(' * '.join(par))

        # compute the permutation from the outputs of the edge layer to the next vertex layer
        in_layer = [v for e in e_layers[i] for v in g.target(e)]


    # compute the permutation from the final vertex layer to the outputs
    v_pos = { v : j for j,v in enumerate(in_layer) }
    out_layer = list(g.outputs())
    v_perm = [v_pos[v] for v in out_layer]

    # append it as a layer of swap maps
    if v_perm != list(range(len(v_perm))):
        perms = split_perm(v_perm)
        seq.append(' * '.join([perm_to_s(p) for p in perms]))

    return ' ; '.join(seq)

