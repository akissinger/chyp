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


class SimpTac(Tactic):
    def name(self) -> str:
        return 'simp'

    def __prepare_context(self):
        defs = [r for r in self.args if r[-4:] == '_def']
        for r in self.args:
            if r[-4:] != '_def':
                self.add_rule_to_context(r)
                Tactic.repeat(lambda df: self.rewrite_lhs1(df, r), defs)

    def make_rhs(self) -> Iterator[Graph]:
        self.__prepare_context()
        Tactic.repeat(self.rewrite_lhs1, self.args)
        lhs = self.lhs()
        if lhs: yield lhs

    def check(self) -> None:
        self.__prepare_context()
        Tactic.repeat(self.rewrite_lhs1, self.args)
        Tactic.repeat(self.rewrite_rhs1, self.args)
        self.validate_goal()

