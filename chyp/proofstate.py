from __future__ import annotations
import re
from typing import Dict, Iterator, List, Optional, Set, Tuple
from .term import graph_to_term
from .graph import Graph
from .rewrite import dpo
from .rule import Rule, RuleError
from .matcher import Match, match_rule, find_iso
from . import state

RULE_NAME_RE = re.compile('(-)?\\s*([a-zA-Z_][\\.a-zA-Z0-9_]*)')

class Goal:
    formula: Rule
    assumptions: Dict[str, Rule]
    def __init__(self, formula: Rule, assumptions: Optional[Dict[str, Rule]]=None):
        self.formula = formula
        self.assumptions = assumptions if assumptions else dict()
    
    def copy(self) -> Goal:
        assumptions = {asm: r.copy() for asm,r in self.assumptions.items()}
        return Goal(self.formula.copy(), assumptions)

class ProofState:
    def __init__(self, state: state.State, sequence: int, goals: Optional[List[Goal]] = None):
        self.state = state
        self.sequence = sequence
        self.goals = goals if goals else []
        self.context: Dict[str, Rule] = dict()
        self.errors: Set[str] = set()
        self.line = -1
    
    def snapshot(self, part: state.ProofStepPart) -> ProofState:
        goals = [g.copy() for g in self.goals]
        ps = ProofState(self.state, self.sequence, goals)
        ps.line = part.line
        return ps

    def error(self, message: str) -> None:
        if not message in self.errors:
            # TODO get the line number from somewhere
            line = -1
            self.state.errors.append((self.state.file_name, line, message))
            self.errors.add(message)

    def has_goal(self, i:int=0) -> bool:
        return len(self.goals) > i

    def global_rules(self) -> List[str]:
        return [name for name, j in self.state.rule_sequence.items() if j <= self.sequence]

    def lookup_rule(self, rule_expr: str, goal_i:int=0, local: Optional[bool]=None) -> Tuple[Optional[Rule],bool]:
        """Lookup a rule

        This takes a rule expression, which is a rule name preceeded optionally by '-', and attempts
        to look up the rule first in the local context (i.e. rules added locally by the tactic via
        `add_*_to_context` methods) then assumptions local to goal 'goal_i', then the global context (i.e.
        rules defined the past of this proof).

        There is an optional parameter `local`. If `local` is True, then only rules from the local context
        and assumptions local to the current goal are returned. If it is False, only rules from the global
        context are returned. If it is not given, both contexts are used, searching in the local context first.

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
        if loc:
            if rule_name in self.context:
                rule = self.context[rule_name]
            elif rule_name in self.goals[goal_i].assumptions:
                rule = self.goals[goal_i].assumptions[rule_name]

        if glo and not rule and rule_name in self.state.rule_sequence:
            if self.state.rule_sequence[rule_name] >= self.sequence:
                self.error(f'Attempting to use rule {rule_name} before it is defined/proven.')
                return (None, False)
            rule = self.state.rules[rule_name]

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
        self.context[ident] = rule

    def add_rule_to_context(self, rule_name: str, ident: str='') -> None:
        """Copies the given global rule into the local context, allowing it to be modified by the tactic
        """
        if ident == '': ident = rule_name
        rule, conv = self.lookup_rule(rule_name, local=False)

        if rule:
            if conv and not rule.equiv:
                self.error(f'Attempting to add converse of one-way rule {rule_name} to context.')
            else:
                self.context[ident] = rule

    def __lhs(self, target: str) -> Optional[Graph]:
        if target == '' and len(self.goals) > 0:
            return self.goals[0].formula.lhs
        elif target in self.context:
            return self.context[target].lhs
        else:
            return None

    def __rhs(self, target: str) -> Optional[Graph]:
        if target == '' and len(self.goals) > 0:
            return self.goals[0].formula.rhs
        elif target in self.context:
            return self.context[target].rhs
        else:
            return None
    
    def __set_lhs(self, target: str, graph: Graph) -> None:
        if target == '' and len(self.goals) > 0:
            self.goals[0].formula.lhs = graph
        elif target in self.context:
            self.context[target].lhs = graph

    def __set_rhs(self, target: str, graph: Graph) -> None:
        if target == '' and len(self.goals) > 0:
            self.goals[0].formula.rhs = graph
        elif target in self.context:
            self.context[target].rhs = graph
    
    def replace_lhs(self, new_lhs: Graph) -> None:
        """Replace the LHS of the top goal with the given graph

        For old_lhs the current LHS of the top goal, this adds a new goal "old_lhs = new_lhs"
        to the top of the goal stack. Typically this goal will be closed straight away by another
        tactic like "rule" or "simp".
        """
        try:
            r = Rule(self.lhs(), new_lhs)
            self.__set_lhs('', new_lhs)
            g = self.goals[0].copy()
            g.formula = r
            self.goals.insert(0, g)
        except RuleError as e:
            self.error(str(e))

    def replace_rhs(self, new_rhs: Graph) -> None:
        """Replace the LHS of the top goal with the given graph

        For old_lhs the current LHS of the top goal, this adds a new goal "old_lhs = new_lhs"
        to the top of the goal stack. Typically this goal will be closed straight away by another
        tactic like "rule" or "simp".
        """
        try:
            r = Rule(self.rhs(), new_rhs)
            self.__set_rhs('', new_rhs)
            g = self.goals[0].copy()
            g.formula = r
            self.goals.insert(0, g)
        except RuleError as e:
            self.error(str(e))

    def rewrite_lhs(self, rule_expr: str, target: str='') -> Iterator[Tuple[Match,Match]]:
        """Rewrite the LHS of the goal or a rule in the local context using the provided rule

        If `target` is '', then the rewrite is applied to the goal, otherwise it is applied to the named
        rule in the local context.
        """

        # variance is True if one-way rules should only be applied in the forward direction here and False
        # if they should only be applied in the backward direction
        variance = (target == '')

        # if not self.__goal_lhs: return None
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
                self.__set_lhs(target, m_h.codomain.copy())
                yield (m_g, m_h)

    def rewrite_rhs(self, rule_expr: str, target: str='') -> Iterator[Tuple[Match,Match]]:
        """Rewrite the RHS of the goal or a rule in the local context using the provided rule

        If `target` is '', then the rewrite is applied to the goal, otherwise it is applied to the named
        rule in the local context.
        """

        # variance is True if one-way rules should only be applied in the forward direction here and False
        # if they should only be applied in the backward direction
        variance = (target != '')

        # if not self.__goal_rhs: return None
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
                self.__set_rhs(target, m_h.codomain.copy())
                yield (m_g, m_h)

    def rewrite_lhs1(self, rule_expr: str, target: str='') -> bool:
        for _ in self.rewrite_lhs(rule_expr, target):
            return True
        return False

    def rewrite_rhs1(self, rule_expr: str, target: str='') -> bool:
        for _ in self.rewrite_rhs(rule_expr, target):
            return True
        return False


    def validate_goal(self, i:int=0) -> Optional[Match]:
        if i >= 0 and i < len(self.goals):
            g = self.goals[i]
            return find_iso(g.formula.lhs, g.formula.rhs)
            # if (self.__local_state.status != state.Part.INVALID and iso):
            #     self.__local_state.status = state.Part.VALID
            #     return iso
        return None

    def try_close_goal(self, i:int=0) -> bool:
        if i >= 0 and i < len(self.goals):
            g = self.goals[i]
            if find_iso(g.formula.lhs, g.formula.rhs) != None:
                self.goals.pop(i)
                return True
        return False


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