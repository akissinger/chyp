from typing import List, Mapping, Tuple, Set
from .graph import Graph

# def ready_edges(g: Graph, edges: Set[int], v_pos: Mapping[int,float]) -> Set[int]:
#     ready = set()
#     for e in edges:
#         src = g.source(e)
#         if all(v in v_pos for v in src):
#             ready.add(e)
#     return ready

def layer_decomp(g: Graph) -> Tuple[List[List[int]], List[List[int]]]:
    """Decompose a graph into regular and singular layers

    Returns a pair of lists, sorting the vertices and edges of
    `g` into layers, respectively. Note that this can modify `g`
    by introducing extra vertices and identity boxes.
    """

    v_layers = []
    e_layers = []

    v_pos = dict()
    e_pos = dict()
    v_layer = []
    for i,v in enumerate(g.inputs()):
        v_layer.append(v)
        v_pos[v] = i
    edges = set(g.edges())
    new_ids = set()
    
    while len(edges) > 0:
        v_layers.append(v_layer)

        ready = set()
        for e in edges:
            if all(v in v_pos for v in g.source(e)):
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
            e_pos[e] = sum(v_pos[v] for v in src)/len(src) if len(src) != 0 else 0
            e_layer.append(e)
            edges.discard(e)
        if all(e in new_ids for e in e_layer):
            raise ValueError("Could not make progress. Is graph acyclic?")

        list.sort(e_layer, key=lambda e: e_pos[e])

        e_layers.append(e_layer)

        if len(edges) > 0:
            v_layer = []
            for e in e_layer:
                for v in g.target(e):
                    v_pos[v] = len(v_layer)
                    v_layer.append(v)


    v_layers.append(g.outputs().copy())
    return (v_layers, e_layers)

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
    v_layers, e_layers = layer_decomp(g)

    # build a list of terms to be sequentially composed
    seq = []
    for i in range(len(e_layers)):
        # compute the permulation from the current vertex layer to inputs of the edge layer
        s_layer = [v for e in e_layers[i] for v in g.source(e)]
        v_pos = { v : j for j,v in enumerate(v_layers[i]) }
        v_perm = [v_pos[v] for v in s_layer]

        # append it as a layer of swap maps
        if v_perm != list(range(len(v_perm))):
            perms = split_perm(v_perm)
            seq.append(' * '.join([perm_to_s(p) for p in perms]))

        # append the parallel composition of the current edge layer
        par = [str(g.edge_data(e).value) for e in e_layers[i]]
        seq.append(' * '.join(par))

        # compute the permulation from the outputs of the edge layer to the next vertex layer
        t_layer = [v for e in e_layers[i] for v in g.target(e)]
        v_pos = { v : j for j,v in enumerate(t_layer) }
        v_perm = [v_pos[v] for v in v_layers[i+1]]

        # append it as a layer of swap maps
        if v_perm != list(range(len(v_perm))):
            perms = split_perm(v_perm)
            seq.append(' * '.join([perm_to_s(p) for p in perms]))

    return ' ; '.join(seq)

