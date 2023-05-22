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
import itertools
from typing import Optional

from .graph import Graph

class RuleError(Exception):
    pass

class Rule:
    lhs: Graph
    rhs: Graph

    def __init__(self, lhs: Graph, rhs: Graph, name: str='', equiv: bool=True):
        if len(lhs.inputs()) != len(rhs.inputs()) or len(lhs.outputs()) != len(rhs.outputs()):
            raise RuleError("Inputs and outputs must match on LHS and RHS of rule")
        self.lhs = lhs
        self.rhs = rhs
        self.name = name
        self.equiv = equiv

    def converse(self) -> Optional[Rule]:
        if self.equiv:
            if self.name.startswith('-'):
                name = self.name[1:]
            else:
                name = '-' + self.name

            return Rule(self.rhs.copy(), self.lhs.copy(), name, True)
        else:
            return None

    def is_left_linear(self) -> bool:
        """Returns True if boundary on lhs embeds injectively"""
        verts = set()
        for v in itertools.chain(self.lhs.inputs(), self.lhs.outputs()):
            if v in verts: return False
            verts.add(v)
        return True
