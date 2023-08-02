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
from ..matcher import Match, match_rule, find_iso
from .. import state

RULE_NAME_RE = re.compile('(-)?\\s*([a-zA-Z_][\\.a-zA-Z0-9_]*)')

class Tactic:
    """The base class for all tactics

    This provides the 'refl' tactic and also the tactic API. All other tactics should extend this
    class and only interact with the prover state via its public methods.
    """

    __state: state.State
    __local_state: state.RewriteState

    def __init__(self, local_state: state.RewriteState, args: List[str]) -> None:
        self.__local_state = local_state
        self.__state = local_state.state
        self.__context: Dict[str, Rule] = dict()
        self.__goal_lhs: Optional[Graph] = None
        self.__goal_rhs: Optional[Graph] = None
        self.__errors: Set[str] = set()
        # self.__goal_stack: List[Tuple[Graph,Graph]] = []
        self.args = args


    def repeat(self, rw: Callable[[str], bool], rules: List[str], max_iter: int=255, bound_lhs: int=-1, bound_rhs: int=-1) -> None:
        got_match = True
        i = 0
        while (got_match and
               (max_iter == -1 or i < max_iter) and
               (bound_lhs == -1 or self.lhs_size() < bound_lhs) and
               (bound_rhs == -1 or self.rhs_size() < bound_rhs)):
            got_match = False
            for r in rules:
                # print('rewriting: ' + r)
                while rw(r) and i < max_iter:
                    # print('success')
                    got_match = True
                    i += 1


    def error(self, message: str) -> None:
        if not message in self.__errors:
            self.__state.errors.append((self.__state.file_name, self.__local_state.line_number, message))
            self.__errors.add(message)

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

    def global_rules(self) -> List[str]:
        return [name for name, j in self.__state.rule_sequence.items() if j <= self.__local_state.sequence]

    def lookup_rule(self, rule_expr: str, local: Optional[bool]=None) -> Tuple[Optional[Rule],bool]:
        """Lookup a rule

        This takes a rule expression, which is a rule name preceeded optionally by '-', and attempts
        to look up the rule first in the local context (i.e. rules added locally by the tactic via
        `add_*_to_context` methods) then the global context (i.e. rules defined the past of this proof).

        There is an optional parameter `local`. If `local` is True, then only rules from the local context
        are returned. If it is False, only rules from the global context are returned. If it is not given,
        both contexts are used, searching in the local context first.

        It returns the Rule object and a bool indicating whether '-' appeared in the rule expression, which
        indicates that the converse of the rule should be returned.
        """

        m = RULE_NAME_RE.match(rule_expr)
        if not m:
            self.error('Bad rule expression: ' + rule_expr)
            return (None, False)
        converse = m.group(1) == '-'
        rule_name = m.group(2)

        loc = local is None or local == True
        glo = local is None or local == False

        rule: Optional[Rule] = None
        if loc and rule_name in self.__context:
            rule = self.__context[rule_name]

        if glo and not rule and rule_name in self.__state.rule_sequence:
            if self.__state.rule_sequence[rule_name] > self.__local_state.sequence:
                self.error(f'Attempting to use rule {rule_name} before it is defined/proven.')
                return (None, False)
            rule = self.__state.rules[rule_name]

        if not rule:
            self.error(f'Rule {rule_name} not defined.')
            return (None, False)

        if converse:
            return (rule.converse(), True)
        else:
            return (rule.copy(), False)

    def add_refl_to_context(self, graph: Graph, ident: str) -> None:
        """Adds a trivial (reflexivity) rule to the local context, using the provided graph as LHS and RHS
        """

        rule = Rule(lhs=graph.copy(), rhs=graph.copy(), name=ident)
        self.__context[ident] = rule

    def add_rule_to_context(self, rule_name: str, ident: str='') -> None:
        """Copies the given global rule into the local context, allowing it to be modified by the tactic
        """
        if ident == '': ident = rule_name
        rule, conv = self.lookup_rule(rule_name, local=False)

        if rule:
            if conv and not rule.equiv:
                self.error(f'Attempting to add converse of one-way rule {rule_name} to context.')
            else:
                self.__context[ident] = rule

    def __lhs(self, target: str) -> Optional[Graph]:
        if target == '':
            return self.__goal_lhs
        elif target in self.__context:
            return self.__context[target].lhs
        else:
            return None

    def __rhs(self, target: str) -> Optional[Graph]:
        if target == '':
            return self.__goal_rhs
        elif target in self.__context:
            return self.__context[target].rhs
        else:
            return None
    
    def __set_lhs(self, target: str, graph: Graph) -> None:
        if target == '':
            self.__goal_lhs = graph
        elif target in self.__context:
            self.__context[target].lhs = graph

    def __set_rhs(self, target: str, graph: Graph) -> None:
        if target == '':
            self.__goal_rhs = graph
        elif target in self.__context:
            self.__context[target].rhs = graph

    def rewrite_lhs(self, rule_expr: str, target: str='') -> Iterator[Tuple[Match,Match]]:
        """Rewrite the LHS of the goal or a rule in the local context using the provided rule

        If `target` is '', then the rewrite is applied to the goal, otherwise it is applied to the named
        rule in the local context.
        """

        # variance is True if one-way rules should only be applied in the forward direction here and False
        # if they should only be applied in the backward direction
        variance = (target == '')

        if not self.__goal_lhs: return None
        rule, converse = self.lookup_rule(rule_expr)
        if not rule: return None
        if not rule.equiv and converse == variance:
            self.error(f'Attempting to use converse of rule {rule_expr} without proof.')
            return None

        target_graph = self.__lhs(target)
        if not target_graph:
            return None

        for m_g in match_rule(rule, target_graph):
            for m_h in dpo(rule, m_g):
                self.__set_lhs(target, m_h.cod.copy())
                yield (m_g, m_h)

    def rewrite_rhs(self, rule_expr: str, target: str='') -> Iterator[Tuple[Match,Match]]:
        """Rewrite the RHS of the goal or a rule in the local context using the provided rule

        If `target` is '', then the rewrite is applied to the goal, otherwise it is applied to the named
        rule in the local context.
        """

        # variance is True if one-way rules should only be applied in the forward direction here and False
        # if they should only be applied in the backward direction
        variance = (target != '')

        if not self.__goal_rhs: return None
        rule, converse = self.lookup_rule(rule_expr)
        if not rule: return None
        if not rule.equiv and converse == variance:
            self.error(f'Attempting to use converse of rule {rule_expr} without proof.')
            return None

        target_graph = self.__rhs(target)
        if not target_graph:
            return None

        for m_g in match_rule(rule, target_graph):
            for m_h in dpo(rule, m_g):
                self.__set_rhs(target, m_h.cod.copy())
                yield (m_g, m_h)

    def rewrite_lhs1(self, rule_expr: str, target: str='') -> bool:
        for _ in self.rewrite_lhs(rule_expr, target):
            return True
        return False

    def rewrite_rhs1(self, rule_expr: str, target: str='') -> bool:
        for _ in self.rewrite_rhs(rule_expr, target):
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

    def lhs(self, target: str='') -> Optional[Graph]:
        g = self.__lhs(target)
        return g.copy() if g else None

    def rhs(self, target: str='') -> Optional[Graph]:
        g = self.__rhs(target)
        return g.copy() if g else None

    def lhs_size(self, target: str='') -> int:
        g = self.__lhs(target)
        return g.num_edges() + g.num_vertices() if g else 0

    def rhs_size(self, target: str='') -> int:
        g = self.__rhs(target)
        return g.num_edges() + g.num_vertices() if g else 0

    def highlight_lhs(self, vertices: Set[int], edges: Set[int]) -> None:
        if self.__local_state.lhs:
            self.__local_state.lhs.highlight(vertices, edges)

    def highlight_rhs(self, vertices: Set[int], edges: Set[int]) -> None:
        if self.__local_state.rhs:
            self.__local_state.rhs.highlight(vertices, edges)

    def __reset(self) -> None:
        self.__errors.clear()
        self.__context.clear()
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




