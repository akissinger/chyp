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


from ..term import graph_to_term
from ..graph import Graph
from ..rewrite import dpo
from ..rule import Rule
from ..matcher import Match, match_rule, find_iso
from .. import state

class Tactic:
    _state: state.State
    _local_state: state.RewriteState

    def __init__(self, local_state: state.RewriteState, args: List[str]) -> None:
        self._local_state = local_state
        self._state = local_state.state
        self._goal_lhs = None
        self._goal_rhs = None
        self._goal_stack: List[Tuple[Graph,Graph]] = []
        self.args = args

    def has_goal(self) -> bool:
        return self._goal_lhs is not None and self._goal_rhs is not None

    def push_goal(self) -> None:
        if not self._goal_lhs or not self._goal_rhs: return
        self._goal_stack.append((self._goal_lhs.copy(), self._goal_rhs.copy()))

    def pop_goal(self) -> bool:
        if len(self._goal_stack) > 0:
            self._goal_lhs, self._goal_rhs = self._goal_stack.pop()
            return True
        else:
            return False

    def lookup_rule(self, rule_name: str) -> Optional[Rule]:
        if rule_name in self._state.rule_sequence and self._state.rule_sequence[rule_name] <= self._local_state.sequence:
            return self._state.rules[rule_name]
        else:
            return None

    def rewrite_lhs(self, rule_name: str, converse: bool=False) -> Iterator[Tuple[Match,Match]]:
        if not self._goal_lhs:
            raise StopIteration

        rule = self.lookup_rule(rule_name)

        if not rule:
            raise StopIteration

        if converse and not rule.equiv:
            raise StopIteration

        rewrite_id = 0
        for m_lhs in match_rule(rule, self._goal_lhs):
            for m_rhs in dpo(rule, m_lhs):
                self._goal_lhs = m_rhs.cod.copy()
                yield (m_lhs, m_rhs)
                rewrite_id += 1

    def rewrite_rhs(self, rule_name: str, converse: bool=False) -> Iterator[Tuple[Match,Match]]:
        if not self._goal_rhs:
            raise StopIteration

        rule = self.lookup_rule(rule_name)

        if not rule:
            raise StopIteration

        if not converse and not rule.equiv:
            raise StopIteration

        rewrite_id = 0
        for m_lhs in match_rule(rule, self._goal_rhs):
            for m_rhs in dpo(rule, m_lhs):
                self._goal_rhs = m_rhs.cod.copy()
                yield (m_lhs, m_rhs)
                rewrite_id += 1

    def validate_goal(self) -> Optional[Match]:
        if not self._goal_lhs or not self._goal_rhs: return None

        iso = find_iso(self._goal_lhs, self._goal_rhs)
        if (self._local_state.status != state.RewriteState.INVALID and iso):
            self._local_state.status = state.RewriteState.VALID
            return iso
        else:
            return None

    def highlight_lhs(self, vertices: Set[int], edges: Set[int]):
        if self._local_state.lhs:
            self._local_state.lhs.highlight(vertices, edges)

    def highlight_rhs(self, vertices: Set[int], edges: Set[int]):
        if self._local_state.rhs:
            self._local_state.rhs.highlight(vertices, edges)

    def _reset(self):
        self._goal_lhs = self._local_state.lhs.copy() if self._local_state.lhs else None
        self._goal_rhs = self._local_state.rhs.copy() if self._local_state.rhs else None
        self._goal_stack: List[Tuple[Graph,Graph]] = []

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
    def check(self) -> None:
        raise NotImplementedError('Tactic.check() must be implemented in subclass')

    # tactics that can synthesise an RHS should override this method
    def make_rhs(self) -> Iterator[Graph]:
        raise StopIteration




