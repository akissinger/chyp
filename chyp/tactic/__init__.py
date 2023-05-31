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
from typing import Iterator, List, Optional, Set, Tuple
import re

from ..term import graph_to_term
from ..graph import Graph
from ..rewrite import dpo
from ..rule import Rule
from ..matcher import Match, match_rule, find_iso
from .. import state

RULE_NAME_RE = re.compile('(-)?\\s*([a-zA-Z_][\\.a-zA-Z0-9_]*)')

class Tactic:
    _state: state.State
    _local_state: state.RewriteState

    def __init__(self, local_state: state.RewriteState, args: List[str]) -> None:
        self._local_state = local_state
        self._state = local_state.state
        self._goal_lhs: Optional[Graph] = None
        self._goal_rhs: Optional[Graph] = None
        self._goal_stack: List[Tuple[Graph,Graph]] = []
        self.args = args

    def has_goal(self) -> bool:
        return self._goal_lhs is not None and self._goal_rhs is not None

    # def push_goal(self) -> None:
    #     if not self._goal_lhs or not self._goal_rhs: return
    #     self._goal_stack.append((self._goal_lhs.copy(), self._goal_rhs.copy()))

    # def pop_goal(self) -> bool:
    #     if len(self._goal_stack) > 0:
    #         self._goal_lhs, self._goal_rhs = self._goal_stack.pop()
    #         return True
    #     else:
    #         return False

    def lookup_rule(self, rule_expr: str) -> Tuple[Optional[Rule],bool]:
        m = RULE_NAME_RE.match(rule_expr)
        if not m: return (None, False)
        converse = m.group(1) == '-'
        rule_name = m.group(2)
        if rule_name in self._state.rule_sequence and self._state.rule_sequence[rule_name] <= self._local_state.sequence:
            rule = self._state.rules[rule_name]
            if converse:
                return (rule.converse(), True)
            else:
                return (rule.copy(), False)
        else:
            return (None, False)

    def rewrite_lhs(self, rule_expr: str) -> Iterator[Tuple[Match,Match]]:
        if not self._goal_lhs: return None
        rule, converse = self.lookup_rule(rule_expr)
        if not rule: return None
        if converse and not rule.equiv:
            return None

        for m_g in match_rule(rule, self._goal_lhs):
            for m_h in dpo(rule, m_g):
                self._goal_lhs = m_h.cod.copy()
                yield (m_g, m_h)


    def rewrite_rhs(self, rule_expr: str) -> Iterator[Tuple[Match,Match]]:
        if not self._goal_rhs: return None
        rule, converse = self.lookup_rule(rule_expr)
        if not rule: return None
        if not converse and not rule.equiv:
            return None

        for m_g in match_rule(rule, self._goal_rhs):
            for m_h in dpo(rule, m_g):
                self._goal_rhs = m_h.cod.copy()
                yield (m_g, m_h)


    def validate_goal(self) -> Optional[Match]:
        if not self._goal_lhs or not self._goal_rhs: return None

        iso = find_iso(self._goal_lhs, self._goal_rhs)
        if (self._local_state.status != state.RewriteState.INVALID and iso):
            self._local_state.status = state.RewriteState.VALID
            return iso
        else:
            return None

    def lhs(self) -> Optional[Graph]:
        if not self._goal_lhs is None:
            return self._goal_lhs.copy()
        else:
            return None

    def rhs(self) -> Optional[Graph]:
        if not self._goal_rhs is None:
            return self._goal_rhs.copy()
        else:
            return None

    def highlight_lhs(self, vertices: Set[int], edges: Set[int]) -> None:
        if self._local_state.lhs:
            self._local_state.lhs.highlight(vertices, edges)

    def highlight_rhs(self, vertices: Set[int], edges: Set[int]) -> None:
        if self._local_state.rhs:
            self._local_state.rhs.highlight(vertices, edges)

    def _reset(self) -> None:
        self._goal_lhs = self._local_state.lhs.copy() if self._local_state.lhs else None
        self._goal_rhs = self._local_state.rhs.copy() if self._local_state.rhs else None
        self._goal_stack = []

    def next_rhs(self, current: str) -> Optional[str]:
        self._reset()
        seen: Set[str] = set()
        seen = set([current])

        found_prev = (current == '?')
        next_term = None
        for g in self.make_rhs():
            t = graph_to_term(g)
            if found_prev and not t in seen:
                next_term = t
                break
            elif not next_term:
                next_term = t

            seen.add(t)
            found_prev = (current == t)
        return next_term

    def run_check(self) -> None:
        self._local_state.status = state.RewriteState.CHECKING
        self._reset()
        self.check()
        if self._local_state.status != state.RewriteState.VALID:
            self._local_state.status = state.RewriteState.INVALID

    # tactics should override this method
    def name(self) -> str:
        return 'refl'

    # tactics should override this method
    def check(self) -> None:
        self.validate_goal()

    # tactics that can synthesize an RHS should override this method
    def make_rhs(self) -> Iterator[Graph]:
        lhs = self.lhs()
        if lhs: yield lhs




