#     chyp - An interactive theorem prover for string diagrams 
#     Copyright (C) 2023 - Aleks Kissinger
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
from typing import Iterator

from ..graph import Graph
from . import Tactic


class RuleTac(Tactic):
    def name(self) -> str:
        return 'rule'

    def make_rhs(self) -> Iterator[Graph]:
        if len(self.args) == 0: raise StopIteration()
        for _, m_rhs in self.proof_state.rewrite_lhs(self.args[0]):
            yield m_rhs.codomain

    def run(self) -> bool:
        if len(self.args) == 0:
            return False

        # apply a single rewrite rule in all possible ways
        for _ in self.proof_state.rewrite_lhs(self.args[0]):
            # if the LHS and RHS are isomorphic, close the goal...
            return self.proof_state.try_close_goal()
            # if iso:
                # ...and highlight the part that was rewritten
                # TODO highlighting needs to work differently from before
                # rhs_verts = set(iso.vertex_map[v] for v in m_rhs.vertex_image)
                # rhs_edges = set(iso.edge_map[e] for e in m_rhs.edge_image)
                # self.highlight_lhs(m_lhs.vertex_image, m_lhs.edge_image)
                # self.highlight_rhs(rhs_verts, rhs_edges)
                # return True
        
        return False

