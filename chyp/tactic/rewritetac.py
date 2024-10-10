
#     chyp - An interactive theorem prover for string diagrams 
#     Copyright (C) 2024 - Aleks Kissinger
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
from typing import List

from ..graph import Graph
from . import Tactic
from ..proofstate import ProofState


class RewriteTac(Tactic):
    def __init__(self, proof_state: ProofState, args: List[str], term: Graph) -> None:
        Tactic.__init__(self, proof_state, args)
        self.term = term

    def name(self) -> str:
        return 'rewrite'

    def run(self) -> bool:
        if len(self.args) == 1 and self.args[0] == 'LHS':
            self.proof_state.replace_lhs(self.term)
        else:
            self.proof_state.replace_rhs(self.term)
        return True

