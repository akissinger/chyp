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
from typing import Callable, Iterator


from ..graph import Graph
from . import Tactic


class SimpTac(Tactic):
    MAX_DEPTH = 256

    def name(self) -> str:
        return 'simp'

    def __repeat(self, m: Callable):
        got_match = True
        i = 0
        while got_match and i < SimpTac.MAX_DEPTH:
            got_match = False
            for r in self.args:
                while m(r) and i < SimpTac.MAX_DEPTH:
                    got_match = True
                    i += 1

    def make_rhs(self) -> Iterator[Graph]:
        self.__repeat(self.rewrite_lhs)
        lhs = self.lhs()
        if lhs: yield lhs

    def check(self) -> None:
        self.__repeat(self.rewrite_lhs)
        self.__repeat(self.rewrite_rhs)
        self.validate_goal()

