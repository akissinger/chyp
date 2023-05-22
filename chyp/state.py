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

from typing import Dict, List, Optional, Tuple

from .matcher import find_iso, match_rule
from .parser import parse
from .rewrite import dpo
from .graph import Graph
from .rule import Rule

# class SemanticError(Exception):
#     def __init__(self, line: int, message: str):
#         self.line = line
#         self.message = message
#         super().__init__(str(self.line) + ": " + self.message)


class RewriteState:
    UNCHECKED = 0
    CHECKING = 1
    VALID = 2
    INVALID = 3

    def __init__(self,
                 term_pos: Tuple[int,int] = (0,0),
                 equiv: bool=True,
                 rule: Optional[Rule]=None,
                 lhs: Optional[Graph]=None,
                 rhs: Optional[Graph]=None,
                 lhs_match: Optional[Graph]=None,
                 rhs_match: Optional[Graph]=None,
                 stub: bool=False) -> None:
        self.status = RewriteState.UNCHECKED
        self.term_pos = term_pos
        self.equiv = equiv
        self.rule = rule
        self.lhs = lhs
        self.rhs = rhs
        self.lhs_match = lhs_match
        self.rhs_match = rhs_match
        self.stub = stub

    def check(self) -> None:
        if self.rule and self.lhs and self.rhs:
            # check for any constraints on the LHS and RHS first
            if self.lhs_match and not find_iso(self.lhs, self.lhs_match):
                self.status = RewriteState.INVALID
            if self.rhs_match and not find_iso(self.rhs, self.rhs_match):
                self.status = RewriteState.INVALID

            # if all LHS/RHS constraints are satisfied, try to prove the rule step by rewriting
            if self.status == RewriteState.CHECKING:
                for m_lhs in match_rule(self.rule, self.lhs):
                    for m_rhs in dpo(self.rule, m_lhs):
                        iso = find_iso(m_rhs.cod, self.rhs)
                        if iso:
                            self.status = RewriteState.VALID

                            for v in m_lhs.dom.vertices():
                                self.lhs.vertex_data(m_lhs.vmap[v]).highlight = True
                            for e in m_lhs.dom.edges():
                                self.lhs.edge_data(m_lhs.emap[e]).highlight = True

                            for v in m_rhs.dom.vertices():
                                self.rhs.vertex_data(iso.vmap[m_rhs.vmap[v]]).highlight = True
                            for e in m_rhs.dom.edges():
                                self.rhs.edge_data(iso.emap[m_rhs.emap[e]]).highlight = True

                            break

        if self.status != RewriteState.VALID:
            self.status = RewriteState.INVALID

class State:
    def __init__(self) -> None:
        self.graphs: Dict[str, Graph] = dict()
        self.rules: Dict[str, Rule] = dict()
        self.rewrites: Dict[str, RewriteState] = dict()
        self.parts: List[Tuple[int, int, str, str]] = list()
        self.errors: List[Tuple[str, int, str]] = list()

    def update(self, code: str, file_name: str) -> None:
        parse_data = parse(code, file_name)
        self.graphs = parse_data.graphs
        self.rules = parse_data.rules
        self.parts = parse_data.parts
        self.errors = parse_data.errors

        for name, (t_start, t_end, equiv, rule, lhs, rhs, lhs_match, rhs_match) in parse_data.rewrites.items():
            stub = not (':' in name)
            self.rewrites[name] = RewriteState((t_start, t_end), equiv, rule, lhs, rhs, lhs_match, rhs_match, stub)

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

