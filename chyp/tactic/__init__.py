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
from typing import Callable, Dict, Iterator, List, Optional, Set, Tuple
import re

from ..term import graph_to_term
from ..graph import Graph
from ..rewrite import dpo
from ..rule import Rule
from ..proofstate import ProofState
from ..matcher import Match, match_rule, find_iso
from .. import state


class Tactic:
    """The base class for all tactics

    This provides the 'refl' tactic and also the tactic API. All other tactics should extend this
    class and only interact with the prover state via its public methods.
    """
    def __init__(self, proof_state: ProofState, args: List[str]) -> None:
        self.proof_state = proof_state
        self.args = args


    def repeat(self, rw: Callable[[str], bool], rules: List[str], max_iter: int=255, bound_lhs: int=-1, bound_rhs: int=-1) -> None:
        got_match = True
        i = 0
        while (got_match and
               (max_iter == -1 or i < max_iter) and
               (bound_lhs == -1 or self.proof_state.lhs_size() < bound_lhs) and
               (bound_rhs == -1 or self.proof_state.rhs_size() < bound_rhs)):
            got_match = False
            for r in rules:
                # print('rewriting: ' + r)
                while rw(r) and i < max_iter:
                    # print('success')
                    got_match = True
                    i += 1



    def highlight_lhs(self, vertices: Set[int], edges: Set[int], goal_i: int=0) -> None:
        if goal_i >= 0 and goal_i < len(self.proof_state.goals):
            self.proof_state.goals[goal_i].formula.lhs.highlight(vertices, edges)

    def highlight_rhs(self, vertices: Set[int], edges: Set[int], goal_i: int=0) -> None:
        if goal_i >= 0 and goal_i < len(self.proof_state.goals):
            self.proof_state.goals[goal_i].formula.lhs.highlight(vertices, edges)

    # def __reset(self) -> None:
    #     self.__errors.clear()
    #     self.__context.clear()
    #     self.__goal_lhs = self.__local_state.lhs.copy() if self.__local_state.lhs else None
    #     self.__goal_rhs = self.__local_state.rhs.copy() if self.__local_state.rhs else None
    #     # self.__goal_stack = []

    # def next_rhs(self, current: str) -> Optional[str]:
    #     self.__reset()
    #     seen: Set[str] = set()
    #     seen = set([current])

    #     found_prev = (current == '?')
    #     next_term = None
    #     for g in self.make_rhs():
    #         t = graph_to_term(g)
    #         if found_prev and not t in seen:
    #             next_term = t
    #             break
    #         elif not next_term:
    #             next_term = t

    #         seen.add(t)
    #         found_prev = (current == t)
    #     return next_term

    def run_check(self) -> None:
        self.__local_state.status = state.Part.CHECKING
        self.__reset()
        self.check()
        if self.__local_state.status != state.Part.VALID:
            self.__local_state.status = state.Part.INVALID

    # tactics should override this method
    def name(self) -> str:
        return 'refl'

    # tactics should override this method
    def check(self) -> None:
        self.proof_state.validate_goal()

    # tactics that can synthesize an RHS should override this method
    def make_rhs(self) -> Iterator[Graph]:
        lhs = self.proof_state.lhs()
        if lhs: yield lhs




