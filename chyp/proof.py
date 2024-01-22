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
"""First order logic theorem proving backend."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from chyp.graph import Graph


class Connective(Enum):
    """A logical connective."""
    AND = '∧'
    OR = '∨'
    NOT = '¬'
    IMPLIES = '⟶'
    IFF = '⟷'


class Formula:
    """A first order logic formula using graph equations as predicates."""
    ...


@dataclass
class Predicate(Formula):
    """An equation between two graphs."""
    lhs: Graph
    rhs: Graph


@dataclass
class Connected(Formula):
    """Two formula joined by a connective."""
    connective: Connective
    lhs: Formula
    rhs: Formula
