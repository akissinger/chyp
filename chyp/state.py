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

import os.path
from typing import Any, Dict, List, Optional, Tuple
import lark
from lark import v_args
from lark.tree import Meta

from . import parser
from .graph import Graph, GraphError, gen, perm, identity, redistributer
from .rule import Rule, RuleError
from .proofstate import ProofState
from .parts import *


class State(lark.Transformer):
    def __init__(self, namespace: str='', file_name: str='') -> None:
        self.namespace = namespace
        self.file_name = file_name
        self.revision = -1 # to check if state is currently being used by editor
        self.import_depth = 0
        self.sequence: int = 0
        self.graphs: Dict[str, Graph] = dict()
        self.rules: Dict[str, Rule] = {'refl': Rule(Graph(), Graph(), name="refl")}
        self.rule_sequence: Dict[str, int] = {'refl': 0}
        # self.rewrites: Dict[str, List[RewriteState]] = dict()
        self.proofs: Dict[str, ProofState] = dict()
        self.errors: List[Tuple[str, int, str]] = list()
        self.parts: List[Part] = list()
        self.current_part: Optional[Part] = None
        self.parsed = False
    
    def set_current_part(self, p: Optional[Part]) -> None:
        self.current_part = p
    
    def add_part(self, p: Part) -> None:
        # we only save parts for the top-level file, not imported files
        if self.import_depth == 0:
            p.index = len(self.parts)
            self.parts.append(p)

    def part_at(self, pos: int, strict: bool=False) -> Optional[Part]:
        imin = 0
        imax = len(self.parts)-1
        while imin <= imax:
            i = (imax+imin)//2
            p = self.parts[i]
            if pos < p.start:
                imax = i-1
            elif pos > p.end:
                imin = i+1
            else:
                if i > 0 and self.parts[i-1].end >= pos:
                    return self.parts[i-1]
                return p
        if not strict and len(self.parts) > 0:
            return self.parts[max(0, imin-1)]
        else:
            return None
    
    def copy_state_until(self, state: State, pos: int) -> None:
        for (i,p) in enumerate(state.parts):
            if p.end < pos and len(self.parts) > i:
                self.parts[i] = p
            else:
                break

    def var(self, items: List[Any]) -> str:
        s = str(items[0])
        return self.namespace + '.' + s if self.namespace else s

    def module_name(self, items: List[Any]) -> str:
        return str(items[0])

    def num(self, items: List[Any]) -> int:
        return int(items[0])

    def type_element(self, items: list[Any]
                     ) -> tuple[str | None, int] | None:
        # The default type is denoted by keyword 'u'
        if items[0] == 'u':
            vtype = None
        # The monoidal unit is denoted by keyword 'None'
        elif items[0] == 'None':
            return None
        else:
            vtype = str(items[0])
        size = 1 if items[1] is None else items[1]
        return vtype, size

    def type_term(self, items: list[tuple[str | None, int] | None]
                  ) -> (list[tuple[None, int]]
                        | list[tuple[str | None, int] | None]):
        # An integer n is parsed as n parallel default type wires of
        # register size 1.
        if isinstance(items[0], int):
            return items[0] * [(None, int(1))]
        # Assuming strict monoidal category: ignore remove monoidal units
        items = [i for i in items if i is not None]
        return items

    def id(self, items: list[Any]) -> Graph:
        if items[0] is None:
            return identity(infer_type=True, infer_size=True)
        vtype, size = items[0]
        return identity(vtype=vtype, size=size)

    def id0(self, _: List[Any]) -> Graph:
        return Graph()

    def eq(self, _: List[Any]) -> bool:
        return True

    def le(self, _: List[Any]) -> bool:
        return False

    @v_args(meta=True)
    def perm(self, meta: Meta, items: List[Any]) -> Graph | None:
        try:
            # If no explicit permutation is provided, the permutation
            # is assumed to be a swap on two vertices.
            if items[1] is None:
                permutation_indices = [1, 0]
            else:
                permutation_indices = [int(i) for i in items[1]]
            # If no type argument is provided, the domain types and
            # sizes are set to the default type and size 1, and can
            # be inferred at composition time.
            infer_type = infer_size = items[0] is None
            if items[0] is None:
                domain = len(permutation_indices) * [(None, 1)]
            else:
                domain = items[0]
            return perm(permutation_indices, domain=domain, # type:ignore
                        infer_type=infer_type, infer_size=infer_size)
        except GraphError as e:
            self.errors.append((self.file_name, meta.line, str(e)))
        return None

    def perm_indices(self, items: list[int]) -> list[int]:
        return items

    @v_args(meta=True)
    def redistribution(self, meta: Meta,
                       items: list[Any]) -> Graph | None:
        try:
            # A redistributer on the monoidal unit is the empty diagram.
            if items[0] == 'None':
                return Graph()
            if items[0] == 'u' or items[0] is None:
                vtype = None
            else:
                vtype = items[0]
            # # If keyword provided as domain size list, make a divider.
            # if items[1] is None:
            #     size_list = items[2]
            #     domain = [(vtype, sum(size_list))]
            #     codomain = [(vtype, size) for size in size_list]
            # # If keyword provided as codomain size list, make a gatherer.
            # elif items[2] is None:
            #     size_list = items[1]
            #     domain = [(vtype, size) for size in size_list]
            #     codomain = [(vtype, sum(size_list))]
            domain = [(vtype, size) for size in items[1]]
            codomain = [(vtype, size) for size in items[2]]
            return redistributer(domain, codomain)
        except GraphError as e:
            self.errors.append((self.file_name, meta.line, str(e)))
            return None

    def size_list(self, items: list[int]) -> list[int]:
        return items

    def var_list(self, items: List[Any]) -> List[str]:
        return [self.var((item,)) for item in items]

    @v_args(meta=True)
    def term_ref(self, meta: Meta, items: List[Any]) -> Optional[Graph]:
        s = str(items[0])
        if self.namespace:
            s = self.namespace + '.' + s

        if s in self.graphs:
            return self.graphs[s]
        else:
            self.errors.append((self.file_name, meta.line, 'Undefined term: ' + s))
            return None

    @v_args(meta=True)
    def rule_ref(self, meta: Meta, items: List[Any]) -> Optional[Rule]:
        s = str(items[0])
        if self.namespace and s != 'refl':
            s = self.namespace + '.' + s

        if s in self.rules:
            return self.rules[s]
        else:
            self.errors.append((self.file_name, meta.line, 'Undefined rule: ' + s))
            return None

    def par(self, items: List[Any]) -> Optional[Graph]:
        if items[0] and items[1]:
            return items[0] * items[1]
        else:
            return None

    @v_args(meta=True)
    def seq(self, meta: Meta, items: List[Any]) -> Optional[Graph]:
        if items[0] and items[1]:
            g = None
            try:
                g = items[0] >> items[1]
            except GraphError as e:
                self.errors.append((self.file_name, meta.line, str(e)))
            return g
        else:
            return None

    @v_args(meta=True)
    def show(self, meta: Meta, items: List[Any]) -> None:
        rule = items[0]
        if rule:
            self.add_part(RulePart(meta.start_pos, meta.end_pos, meta.line, rule))

    @v_args(meta=True)
    def gen(self, meta: Meta, items: List[Any]) -> None:
        print(meta, items)
        name = items[0]
        domain = items[1]
        codomain = items[2]
        (fg, bg) = items[3] if items[3] else ('', '')
        if name not in self.graphs:
            g = gen(name, domain, codomain, fg=fg, bg=bg)
            self.graphs[name] = g
        else:
            g = self.graphs[name]
            existing_domain = g.domain()
            existing_codomain = g.codomain()
            if existing_domain != domain or existing_codomain != codomain:
                self.errors.append((self.file_name, meta.line, "Term '{}' already defined with incompatible type {} -> {}.".format(name, existing_domain, existing_codomain)))
                self.errors.append((self.file_name, meta.line, "(Trying to add) {} -> {}.".format(domain, codomain)))
        self.add_part(GenPart(meta.start_pos, meta.end_pos, meta.line, name, g))

    @v_args(meta=True)
    def family(self, meta: Meta, items: List[Any]) -> None:
        print(meta, items)
        name = items[0]
        args = items[1]
        domain = items[2]
        codomain = items[3]
        if name not in self.graphs:
            self.graphs[name] = gen(name, domain, codomain)
        else:
            g = self.graphs[name]
            existing_domain = g.domain()
            existing_codomain = g.codomain()
            if existing_domain != domain or existing_codomain != codomain:
                self.errors.append((self.file_name, meta.line, "Term '{}' already defined with incompatible type {} -> {}.".format(name, existing_domain, existing_codomain)))
                self.errors.append((self.file_name, meta.line, "(Trying to add) {} -> {}.".format(domain, codomain)))
        self.parts.append((meta.start_pos, meta.end_pos, 'family', name))

    @v_args(meta=True)
    def let(self, meta: Meta, items: List[Any]) -> None:
        name, graph = items
        if name not in self.graphs:
            if graph:
                self.graphs[name] = graph
        else:
            self.errors.append((self.file_name, meta.line, "Term '{}' already defined.".format(name)))
        self.add_part(LetPart(meta.start_pos, meta.end_pos, meta.line, name, graph))

    @v_args(meta=True)
    def rule(self, meta: Meta, items: List[Any]) -> None:
        self.sequence += 1
        name, lhs, invertible, rhs = items
        if not name in self.rules:
            if lhs and rhs:
                try:
                    if not invertible:
                        self.errors.append((self.file_name, meta.line, "Non-invertible rules currently not supported."))
                    else:
                        rule = Rule(lhs, rhs, name)
                        self.rules[name] = rule
                        self.rule_sequence[name] = self.sequence
                        self.add_part(RulePart(meta.start_pos, meta.end_pos, meta.line, rule))
                except RuleError as e:
                    self.errors.append((self.file_name, meta.line, str(e)))
        else:
            self.errors.append((self.file_name, meta.line, "Rule '{}' already defined.".format(name)))

    @v_args(meta=True)
    def def_statement(self, meta: Meta, items: List[Any]) -> None:
        self.sequence += 1
        name = items[0]
        graph = items[1]
        (fg, bg) = items[2] if items[2] else ('', '')

        rule_name = name + '_def'
        if rule_name not in self.rules:
            if graph:
                domain = graph.domain()
                codomain = graph.codomain()

                if name not in self.graphs:
                    lhs = gen(name, domain, codomain, fg=fg, bg=bg)
                    self.graphs[name] = lhs
                    rule = Rule(lhs, graph, rule_name)
                    self.rules[rule_name] = rule
                    self.rule_sequence[rule_name] = self.sequence
                    self.add_part(RulePart(meta.start_pos, meta.end_pos, meta.line, rule))
                else:
                    lhs = self.graphs[name]
                    lhs_domain = lhs.domain()
                    lhs_codomain = lhs.codomain()
                    if lhs_domain == domain and lhs_codomain == codomain:
                        rule = Rule(lhs, graph, rule_name)
                        self.rules[rule_name] = rule
                        self.sequence += 1
                        self.rule_sequence[rule_name] = self.sequence
                        self.add_part(RulePart(meta.start_pos, meta.end_pos, meta.line, rule))
                    else:
                        self.errors.append(
                            (self.file_name, meta.line,
                             f'Term "{name}" already defined with '
                             + f'incompatible type {domain} -> {codomain}.')
                        )

        else:
            self.errors.append((self.file_name, meta.line,
                                f'Rule "{rule_name}" already defined.'))

    def gen_color(self, items: List[Any]) -> Tuple[str,str]:
        return (items[1], items[0]) if len(items) == 2 else ('', items[0])

    def color(self, items: List[Any]) -> str:
        return '#' + ''.join([str(it) for it in items])

    @v_args(meta=True)
    def import_statement(self, meta: Meta, items: List[Any]) -> None:
        mod = items[0]
        namespace = items[1] or ''
        import_lets = items[2:]

        for il in import_lets:
            if il:
                name, graph = il
                name = namespace + '.' + name
                if not name in self.graphs:
                    if graph:
                        self.graphs[name] = graph
                else:
                    self.errors.append((self.file_name, meta.line, "Term '{}' already defined.".format(name)))

        file_name = module_filename(mod, self.file_name)
        try:
            parser.parse(file_name=file_name, namespace=namespace, parent=self)
        except FileNotFoundError:
            self.errors.append((self.file_name, meta.line, 'File not found: {}'.format(file_name)))

        self.add_part(ImportPart(meta.start_pos, meta.end_pos, meta.line, file_name))

    def import_let(self, items: List[Any]) -> Tuple[str, Graph]:
        return (items[0], items[1])

    @v_args(meta=True)
    def rewrite(self, meta: Meta, items: List[Any]) -> None:
        self.sequence += 1
        converse = True if items[0] else False
        base_name = items[1]
        name = '-' + base_name if converse else base_name

        term = items[2]
        rw_parts = items[3:]

        if len(rw_parts) == 0:
            self.add_part(RewritePart(meta.start_pos, meta.end_pos, meta.line, name,
                                      sequence=self.sequence,
                                      lhs=term,
                                      stub=True))
        else:
            start = meta.start_pos
            lhs = term
            rhs = None
            all_equiv = True

            for rw_part in rw_parts:
                line_number, rw_end, t_start, t_end, equiv, tactic, tactic_args, rhs = rw_part
                end = max(rw_end, t_end)
                all_equiv = all_equiv and equiv
                if rhs == 'LHS' or rhs == 'RHS':
                    self.errors.append((self.file_name, meta.line, "Cannot use LHS/RHS outside of proof."))
                else:
                    self.add_part(RewritePart(start, end, line_number, name,
                                              sequence=self.sequence,
                                              term_pos=(t_start,t_end),
                                              tactic=tactic,
                                              tactic_args=tactic_args,
                                              lhs=lhs,
                                              rhs=rhs))
                    lhs = rhs.copy() if rhs else None
                start = end
            if term and rhs and isinstance(rhs, Graph):
                try:
                    if converse:
                        # TODO non-invertible rules
                        self.errors.append((self.file_name, meta.line, "Non-invertible rules currently not supported: " + base_name))
                    else:
                        if not name in self.rules:
                            rule = Rule(term.copy(), rhs.copy(), name=name)
                            # remove any highlights placed there by the first/last proof step
                            rule.lhs.unhighlight()
                            rule.rhs.unhighlight()
                            self.rules[name] = rule
                            self.rule_sequence[name] = self.sequence
                        else:
                            self.errors.append((self.file_name, meta.line, "Rule '{}' already defined.".format(name)))
                except RuleError as e:
                    self.errors.append((self.file_name, meta.line, str(e)))

    @v_args(meta=True)
    def rewrite_part(self, meta: Meta, items: List[Any]) -> Tuple[int, int, int, int, bool, str, List[str], Optional[Graph]]:
        equiv = items[0]
        t_start,t_end,rhs = items[1]
        if items[2]:
            tactic, tactic_args = items[2]
        else:
            tactic, tactic_args = ("refl", [])

        return (meta.line, meta.end_pos, t_start, t_end, equiv, tactic, tactic_args, rhs)

    def formula(self, items: List[Any]) -> Tuple[Graph, Graph]:
        lhs = items[0]
        rhs = items[2]
        return (lhs, rhs)

    @v_args(meta=True)
    def theorem(self, meta: Meta, items: List[Any]) -> None:
        self.sequence += 1
        name = items[0]
        (lhs,rhs) = items[1]
        try:
            rule = Rule(lhs, rhs, name)
            self.rule_sequence[name] = self.sequence
            self.add_part(TheoremPart(meta.start_pos, meta.end_pos, meta.line, rule, self.sequence))
        except RuleError as e:
            self.errors.append((self.file_name, meta.line, str(e)))

    @v_args(meta=True)
    def proof_start(self, meta: Meta, _: List[Any]) -> None:
        name = ''
        self.add_part(ProofStartPart(meta.start_pos, meta.end_pos, meta.line, name, self.sequence))

    @v_args(meta=True)
    def proof_end(self, meta: Meta, _: List[Any]) -> None:
        name = ''
        self.add_part(ProofQedPart(meta.start_pos, meta.end_pos, meta.line, name, self.sequence))

    @v_args(meta=True)
    def apply_tac(self, meta: Meta, items: List[Any]) -> None:
        name = ''
        tactic, args = items[0]
        self.add_part(ApplyTacticPart(meta.start_pos, meta.end_pos, meta.line, name,
                                      sequence=self.sequence,
                                      tactic=tactic,
                                      tactic_args=args))

    @v_args(meta=True)
    def rewrite_in_proof(self, meta: Meta, items: List[Any]) -> None:
        name = ''
        lhs_side = items[0]

        start = meta.start_pos
        for step in items[1:]:
            line, end, t_start, t_end, _, sub_tac, sub_tac_args, term_or_side = step
            if isinstance(term_or_side, Graph):
                rhs = term_or_side
                rhs_side = None
            else:
                rhs = None
                rhs_side = term_or_side
            self.add_part(RewritePart(start, end, line, name,
                                      sequence=self.sequence,
                                      term_pos=(t_start,t_end),
                                      lhs_side=lhs_side,
                                      rhs_side=rhs_side,
                                      lhs=None,
                                      rhs=rhs,
                                      tactic=sub_tac,
                                      tactic_args=sub_tac_args))
            start = end
    
    def LHS(self, _: List[Any]) -> str:
        return "LHS"

    def RHS(self, _: List[Any]) -> str:
        return "RHS"

    def tactic(self, items: List[Any]) -> Tuple[str, List[str]]:
        if len(items) >= 2 and str(items[1]) == "(": #)
            args = items[2:] if not items[2] is None else []
            return (items[0], args)
        else:
            rule_expr = ('-' if items[0] else '') + items[1]
            return ("rule", [rule_expr])


    @v_args(meta=True)
    def term_hole(self, meta: Meta, items: List[Any]) -> Tuple[int, int, Optional[Graph]]:
        t = items[0] if len(items) != 0 else None
        return (meta.start_pos, meta.end_pos, t)

    def nested_term(self, items: List[Any]) -> Optional[Graph]:
        return items[1]


def module_filename(name: str, current_file: str) -> str:
    return os.path.join(os.path.dirname(current_file), *name.split('.')) + '.chyp'
