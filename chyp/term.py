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

