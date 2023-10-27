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
from typing import Dict, List, Optional, Tuple

import os.path
from typing import Any, Dict, List, Optional, Tuple
import lark
from lark import v_args
from lark.tree import Meta

from . import parser
from .graph import Graph, GraphError, gen, perm, identity
from .rule import Rule, RuleError
from .tactic import Tactic
from .tactic.simptac import SimpTac
from .tactic.ruletac import RuleTac


class RewriteState:
    UNCHECKED = 0
    CHECKING = 1
    VALID = 2
    INVALID = 3

    def __init__(self,
                 sequence: int,
                 state: State,
                 line_number: int = 0,
                 term_pos: Tuple[int,int] = (0,0),
                 equiv: bool=True,
                 tactic: str='',
                 tactic_args: Optional[List[str]]=None,
                 lhs: Optional[Graph]=None,
                 rhs: Optional[Graph]=None,
                 lhs_match: Optional[Graph]=None,
                 rhs_match: Optional[Graph]=None,
                 stub: bool=False) -> None:

        # store an integer representing my current location. This prevents cyclic dependencies of
        # rules used inside of tactics. TODO: this doesn't work quite right for <= rules, since it
        # doesn't store the location of the rule *and* its converse being proved.
        self.sequence = sequence

        self.state = state
        self.status = RewriteState.UNCHECKED
        self.line_number = line_number
        self.term_pos = term_pos
        self.equiv = equiv
        self.lhs = lhs
        self.rhs = rhs
        self.lhs_match = lhs_match
        self.rhs_match = rhs_match

        tactic_args = [] if tactic_args is None else tactic_args

        self.tactic : Tactic
        if tactic == 'rule':
            self.tactic = RuleTac(self, tactic_args)
        elif tactic == 'simp':
            self.tactic = SimpTac(self, tactic_args)
        else:
            self.tactic = Tactic(self, tactic_args)
        self.stub = stub

    def check(self) -> None:
        self.tactic.run_check()


class State(lark.Transformer):
    def __init__(self, namespace: str='', file_name: str='') -> None:
        self.namespace = namespace
        self.file_name = file_name
        self.import_depth = 0
        self.sequence: int = 0
        self.graphs: Dict[str, Graph] = dict()
        self.rules: Dict[str, Rule] = {'refl': Rule(Graph(), Graph(), name="refl")}
        self.rule_sequence: Dict[str, int] = {'refl': 0}
        self.rewrites: Dict[str, RewriteState] = dict()
        self.errors: List[Tuple[str, int, str]] = list()
        self.parts: List[Tuple[int, int, str, str]] = list()
        self.parsed = False

    def part_with_index_at(self, pos: int) -> Optional[Tuple[int, Tuple[int,int,str,str]]]:
        p0 = (0, self.parts[0]) if len(self.parts) >= 1 else None
        for (i,p) in enumerate(self.parts):
            if p[0] <= pos:
                p0 = (i,p)
                if p[1] >= pos:
                    return (i,p)
        return p0

    def part_at(self, pos: int) -> Optional[Tuple[int,int,str,str]]:
        p = self.part_with_index_at(pos)
        return p[1] if p else None
        

    def var(self, items: List[Any]) -> str:
        s = str(items[0])
        return self.namespace + '.' + s if self.namespace else s

    def module_name(self, items: List[Any]) -> str:
        return str(items[0])
    
    def num(self, items: List[Any]) -> int:
        return int(items[0])

    def type_term(self, items: List[Any]) -> list[str] | int:
        if (len(items) == 1
           and isinstance(items[0], int)):
            return items[0]
        return [str(item) for item in items
                if item != 'None']

    def id(self, _: List[Any]) -> Graph:
        return identity()

    def id0(self, _: List[Any]) -> Graph:
        return Graph()

    def eq(self, _: List[Any]) -> bool:
        return True

    def le(self, _: List[Any]) -> bool:
        return False

    @v_args(meta=True)
    def perm(self, meta: Meta, items: List[Any]) -> Optional[Graph]:
        try:
            if items[0] is None:
                return perm([1, 0], items[1])
            else:
                return perm([int(i) for i in items[0]], items[1])
        except GraphError as e:
            self.errors.append((self.file_name, meta.line, str(e)))
        return None

    def perm_indices(self, items: list[int]) -> list[int]:
        return items

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
            self.parts.append((meta.start_pos, meta.end_pos, 'rule', rule.name))

    @v_args(meta=True)
    def gen(self, meta: Meta, items: List[Any]) -> None:
        name = items[0]
        domain = items[1]
        codomain = items[2]
        (fg,bg) = items[3] if items[3] else ('','')
        if not name in self.graphs:
            self.graphs[name] = gen(name, domain, codomain, fg, bg)
        else:
            g = self.graphs[name]
            existing_domain = g.domain()
            existing_codomain = g.codomain()
            if existing_domain != domain or existing_codomain != codomain:
                self.errors.append((self.file_name, meta.line, "Term '{}' already defined with incompatible type {} -> {}.".format(name, existing_domain, existing_codomain)))
                self.errors.append((self.file_name, meta.line, "(Trying to add) {} -> {}.".format(domain, codomain)))
        self.parts.append((meta.start_pos, meta.end_pos, 'gen', name))
        
    @v_args(meta=True)
    def let(self, meta: Meta, items: List[Any]) -> None:
        name, graph = items
        if not name in self.graphs:
            if graph:
                self.graphs[name] = graph
        else:
            self.errors.append((self.file_name, meta.line, "Term '{}' already defined.".format(name)))
        self.parts.append((meta.start_pos, meta.end_pos, 'let', name))

    @v_args(meta=True)
    def rule(self, meta: Meta, items: List[Any]) -> None:
        name, lhs, invertible, rhs = items
        if not name in self.rules:
            if lhs and rhs:
                try:
                    self.rules[name] = Rule(lhs, rhs, name, invertible)
                    self.sequence += 1
                    self.rule_sequence[name] = self.sequence
                except RuleError as e:
                    self.errors.append((self.file_name, meta.line, str(e)))
        else:
            self.errors.append((self.file_name, meta.line, "Rule '{}' already defined.".format(name)))
        self.parts.append((meta.start_pos, meta.end_pos, 'rule', name))

    @v_args(meta=True)
    def def_statement(self, meta: Meta, items: List[Any]) -> None:
        name = items[0]
        graph = items[1]
        (fg,bg) = items[2] if items[2] else ('','')

        rule_name = name + '_def'
        if not rule_name in self.rules:
            if graph:
                arity = len(graph.inputs())
                coarity = len(graph.outputs())

                if not name in self.graphs:
                    lhs = gen(name, arity, coarity, fg, bg)
                    self.graphs[name] = lhs
                    self.rules[rule_name] = Rule(lhs, graph, rule_name, True)
                    self.sequence += 1
                    self.rule_sequence[rule_name] = self.sequence
                else:
                    lhs = self.graphs[name]
                    inp = len(lhs.inputs())
                    outp = len(lhs.outputs())
                    if inp == arity and outp == coarity:
                        self.rules[rule_name] = Rule(lhs, graph, rule_name, True)
                        self.sequence += 1
                        self.rule_sequence[rule_name] = self.sequence
                    else:
                        self.errors.append((self.file_name, meta.line, "Term '{}' already defined with incompatible type {} -> {}.".format(name, inp, outp)))

        else:
            self.errors.append((self.file_name, meta.line, "Rule '{}' already defined.".format(rule_name)))
        self.parts.append((meta.start_pos, meta.end_pos, 'rule', rule_name))

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

        self.parts.append((meta.start_pos, meta.end_pos, 'import', file_name))

    def import_let(self, items: List[Any]) -> Tuple[str, Graph]:
        return (items[0], items[1])

    @v_args(meta=True)
    def rewrite(self, meta: Meta, items: List[Any]) -> None:
        converse = True if items[0] else False
        base_name = items[1]
        name = '-' + base_name if converse else base_name

        term = items[2]
        rw_parts = items[3:]

        if len(rw_parts) == 0:
            self.parts.append((meta.start_pos, meta.end_pos, "rewrite", name))
            self.rewrites[name] = RewriteState(self.sequence, self, lhs=term, stub=True)
        else:
            start = meta.start_pos
            lhs = term
            rhs = None
            all_equiv = True

            if converse and base_name in self.rules:
                lhs_match = self.rules[base_name].rhs
                rhs_match = self.rules[base_name].lhs
            else:
                lhs_match = None
                rhs_match = None

            last_i = len(rw_parts)-1
            for i, rw_part in enumerate(rw_parts):
                line_number, rw_end, t_start, t_end, equiv, tactic, tactic_args, rhs = rw_part
                end = max(rw_end, t_end)
                all_equiv = all_equiv and equiv
                self.rewrites[name + ":" + str(i)] = RewriteState(
                        self.sequence,
                        self,
                        line_number,
                        (t_start, t_end),
                        equiv,
                        tactic, tactic_args,
                        lhs, rhs,
                        lhs_match if i == 0 else None,
                        rhs_match if i == last_i else None)
                lhs = rhs.copy() if rhs else None
                self.parts.append((start, end, "rewrite", name + ":" + str(i)))
                start = end
            if term and rhs:
                try:
                    if converse:
                        if base_name in self.rules:
                            self.rules[base_name].equiv = True

                            # TODO: this will stop the <= version of the rule from being usable before the converse is
                            # proven. While this is sound and workable, it might confuse people.
                            self.sequence += 1
                            self.rule_sequence[base_name] = self.sequence
                        else:
                            self.errors.append((self.file_name, meta.line, "Trying to prove converse for unknown rule: " + base_name))
                    else:
                        if not name in self.rules:
                            rule = Rule(term.copy(), rhs.copy(), name=name, equiv=all_equiv)
                            # remove any highlights placed there by the first/last proof step
                            rule.lhs.unhighlight()
                            rule.rhs.unhighlight()
                            self.rules[name] = rule
                            self.sequence += 1
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

        # converse = True if items[2] else False

        # rule = items[3] if items[3] else self.rules['refl']
        # if rule and converse:
        #     rule = rule.converse()
        # if equiv and rule and not rule.equiv:
        #     rule = None

        return (meta.line, meta.end_pos, t_start, t_end, equiv, tactic, tactic_args, rhs)

    def tactic(self, items: List[Any]) -> Tuple[str, List[str]]:
        if len(items) >= 2 and str(items[1]) == "(": #)
            args = items[2:] if not items[2] is None else []
            # arg_str = ', '.join(args)
            # print(f"got tactic: {items[0]}({arg_str})")
            return (items[0], args)
        else:
            rule_expr = ('-' if items[0] else '') + items[1]
            # print(f"defaulting to rule tactic: rule({rule_expr})")
            return ("rule", [rule_expr])


    @v_args(meta=True)
    def term_hole(self, meta: Meta, items: List[Any]) -> Tuple[int, int, Optional[Graph]]:
        t = items[0] if len(items) != 0 else None
        return (meta.start_pos, meta.end_pos, t)

    def nested_term(self, items: List[Any]) -> Optional[Graph]:
        return items[1]


def module_filename(name: str, current_file: str) -> str:
    return os.path.join(os.path.dirname(current_file), *name.split('.')) + '.chyp'

# class State:
#     def __init__(self) -> None:
#         self.graphs: Dict[str, Graph] = dict()
#         self.rules: Dict[str, Rule] = dict()
#         self.rule_sequence: Dict[str, int] = dict()
#         self.rewrites: Dict[str, RewriteState] = dict()
#         self.parts: List[Tuple[int, int, str, str]] = list()
#         self.errors: List[Tuple[str, int, str]] = list()

#     def update(self, code: str, file_name: str) -> None:
#         parse_data = parse(code, file_name)
#         self.graphs = parse_data.graphs
#         self.rules = parse_data.rules
#         self.rule_sequence = parse_data.rule_sequence
#         self.parts = parse_data.parts
#         self.errors = parse_data.errors

#         for name, (sequence, t_start, t_end, equiv, tactic, tactic_args, lhs, rhs, lhs_match, rhs_match) in parse_data.rewrites.items():
#             stub = not (':' in name)
#             self.rewrites[name] = RewriteState(sequence, self, (t_start, t_end), equiv, tactic, tactic_args, lhs, rhs, lhs_match, rhs_match, stub)

#     def part_with_index_at(self, pos: int) -> Optional[Tuple[int, Tuple[int,int,str,str]]]:
#         p0 = (0, self.parts[0]) if len(self.parts) >= 1 else None
#         for (i,p) in enumerate(self.parts):
#             if p[0] <= pos:
#                 p0 = (i,p)
#                 if p[1] >= pos:
#                     return (i,p)
#         return p0

#     def part_at(self, pos: int) -> Optional[Tuple[int,int,str,str]]:
#         p = self.part_with_index_at(pos)
#         return p[1] if p else None

