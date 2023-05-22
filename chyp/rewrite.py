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
from typing import Set, List, Dict, Iterator, Any, Optional, Iterable, Tuple
from .graph import Graph
from .matcher import Match
from .rule import Rule


def dpo(r: Rule, m: Match) -> Iterable[Match]:
    """Do double-pushout rewriting

    Given a rule r and match of r.lhs into a graph, return a match
    of r.rhs into the rewritten graph.
    """
    # if not r.is_left_linear():
    #     raise NotImplementedError("Only left linear rules are supported for now")

    # store the vertices we have split for id's on the LHS
    in_map: Dict[int, int] = dict()
    out_map: Dict[int, int] = dict()

    # compute the pushout complement
    ctx = m.cod.copy()
    for e in r.lhs.edges():
        ctx.remove_edge(m.emap[e])
    for v in r.lhs.vertices():
        v1 = m.vmap[v]
        if r.lhs.is_boundary(v):
            in_c = len(r.lhs.vertex_data(v).in_indices)
            out_c = len(r.lhs.vertex_data(v).out_indices)
            if in_c == 1 and out_c == 1:
                v1i, v1o = ctx.explode_vertex(v1)
                if len(v1i) == 1 and len(v1o) == 1:
                    in_map[v] = v1i[0]
                    out_map[v] = v1o[0]
                else:
                    raise NotImplementedError("Rewriting modulo Frobenius not yet supported.")
            elif in_c > 1 or out_c > 1:
                raise NotImplementedError("Rewriting modulo Frobenius not yet supported.")
        else:
            ctx.remove_vertex(v1)

    # this will be the rewritten graph
    h = ctx

    # this will embed r.rhs into h
    m1 = Match(r.rhs, h)
    # vmap1: Dict[int,int] = {}

    # first map the inputs, using the matching of the lhs
    for vl,vr in zip(r.lhs.inputs(), r.rhs.inputs()):
        m1.vmap[vr] = in_map[vl] if vl in in_map else m.vmap[vl]

    # next map the outputs. if the same vertex is an input and an output in r.rhs, then
    # merge them in h.
    for vl,vr in zip(r.lhs.outputs(), r.rhs.outputs()):
        vr1 = out_map[vl] if vl in out_map else m.vmap[vl]
        if vr in m1.vmap:
            h.merge_vertices(m1.vmap[vr], vr1)
        else:
            m1.vmap[vr] = vr1

    # then map the interior to new, fresh vertices
    for v in r.rhs.vertices():
        if not r.rhs.is_boundary(v):
            vd = r.rhs.vertex_data(v)
            v1 = h.add_vertex(vd.x, vd.y, vd.value)
            m1.vmap[v] = v1
            m1.vimg.add(v1)

    # now add the edges from rhs to h and connect them using vmap1
    for e in r.rhs.edges():
        ed = r.rhs.edge_data(e)
        e1 = h.add_edge([m1.vmap[v] for v in ed.s],
                        [m1.vmap[v] for v in ed.t],
                        ed.value, ed.x, ed.y, ed.fg, ed.bg, ed.hyper)
        m1.emap[e] = e1
        m1.eimg.add(e1)

    return [m1]

def rewrite(r: Rule, m: Match) -> Graph:
    """Apply the given rewrite r to at match m and return the first result

    This is a convience wrapper for `dpo` for when the extra rewrite data
    isn't needed."""

    try:
        result = next(iter(dpo(r, m)))
        return result.cod
    except StopIteration:
        raise RuntimeError("Rewrite has no valid context")

