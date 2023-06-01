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
    __state: state.State
    __local_state: state.RewriteState

    def __init__(self, local_state: state.RewriteState, args: List[str]) -> None:
        self.__local_state = local_state
        self.__state = local_state.state
        self.__goal_lhs: Optional[Graph] = None
        self.__goal_rhs: Optional[Graph] = None
        # self.__goal_stack: List[Tuple[Graph,Graph]] = []
        self.args = args

    def error(self, message: str) -> None:
        self.__state.errors.append((self.__state.file_name, self.__local_state.line_number, message))

    def has_goal(self) -> bool:
        return self.__goal_lhs is not None and self.__goal_rhs is not None

    # def push_goal(self) -> None:
    #     if not self.__goal_lhs or not self.__goal_rhs: return
    #     self.__goal_stack.append((self.__goal_lhs.copy(), self.__goal_rhs.copy()))

    # def pop_goal(self) -> bool:
    #     if len(self.__goal_stack) > 0:
    #         self.__goal_lhs, self.__goal_rhs = self.__goal_stack.pop()
    #         return True
    #     else:
    #         return False

    def lookup_rule(self, rule_expr: str) -> Tuple[Optional[Rule],bool]:
        m = RULE_NAME_RE.match(rule_expr)
        if not m:
            self.error('Bad rule expression: ' + rule_expr)
            return (None, False)
        converse = m.group(1) == '-'
        rule_name = m.group(2)

        if not rule_name in self.__state.rule_sequence:
            self.error(f'Rule {rule_name} not defined.')
            return (None, False)

        if self.__state.rule_sequence[rule_name] > self.__local_state.sequence:
            self.error(f'Attempting to use rule {rule_name} before it is defined/proven.')
            return (None, False)

        rule = self.__state.rules[rule_name]
        if converse:
            return (rule.converse(), True)
        else:
            return (rule.copy(), False)

    def rewrite_lhs(self, rule_expr: str) -> Iterator[Tuple[Match,Match]]:
        if not self.__goal_lhs: return None
        rule, converse = self.lookup_rule(rule_expr)
        if not rule: return None
        if converse and not rule.equiv:
            self.error(f'Attempting to use converse of rule {rule_expr} without proof.')
            return None

        for m_g in match_rule(rule, self.__goal_lhs):
            for m_h in dpo(rule, m_g):
                self.__goal_lhs = m_h.cod.copy()
                yield (m_g, m_h)

    def rewrite_rhs(self, rule_expr: str) -> Iterator[Tuple[Match,Match]]:
        if not self.__goal_rhs: return None
        rule, converse = self.lookup_rule(rule_expr)
        if not rule: return None
        if not converse and not rule.equiv:
            self.error(f'Attempting to use converse of rule {rule_expr} without proof.')
            return None

        for m_g in match_rule(rule, self.__goal_rhs):
            for m_h in dpo(rule, m_g):
                self.__goal_rhs = m_h.cod.copy()
                yield (m_g, m_h)

    def rewrite_lhs1(self, rule_expr: str) -> bool:
        for _ in self.rewrite_lhs(rule_expr):
            return True
        return False

    def rewrite_rhs1(self, rule_expr: str) -> bool:
        for _ in self.rewrite_rhs(rule_expr):
            return True
        return False

    def validate_goal(self) -> Optional[Match]:
        if not self.__goal_lhs or not self.__goal_rhs: return None

        iso = find_iso(self.__goal_lhs, self.__goal_rhs)
        if (self.__local_state.status != state.RewriteState.INVALID and iso):
            self.__local_state.status = state.RewriteState.VALID
            return iso
        else:
            return None

    def lhs(self) -> Optional[Graph]:
        if not self.__goal_lhs is None:
            return self.__goal_lhs.copy()
        else:
            return None

    def rhs(self) -> Optional[Graph]:
        if not self.__goal_rhs is None:
            return self.__goal_rhs.copy()
        else:
            return None

    def highlight_lhs(self, vertices: Set[int], edges: Set[int]) -> None:
        if self.__local_state.lhs:
            self.__local_state.lhs.highlight(vertices, edges)

    def highlight_rhs(self, vertices: Set[int], edges: Set[int]) -> None:
        if self.__local_state.rhs:
            self.__local_state.rhs.highlight(vertices, edges)

    def __reset(self) -> None:
        self.__goal_lhs = self.__local_state.lhs.copy() if self.__local_state.lhs else None
        self.__goal_rhs = self.__local_state.rhs.copy() if self.__local_state.rhs else None
        # self.__goal_stack = []

    def next_rhs(self, current: str) -> Optional[str]:
        self.__reset()
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
        self.__local_state.status = state.RewriteState.CHECKING
        self.__reset()
        self.check()
        if self.__local_state.status != state.RewriteState.VALID:
            self.__local_state.status = state.RewriteState.INVALID

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




