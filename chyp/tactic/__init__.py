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
from typing import List, Tuple

from chyp.matcher import find_iso

from ..graph import Graph
from .. import state

class Tactic:
    _state: state.State
    _local_state: state.RewriteState

    def __init__(self, local_state: state.RewriteState) -> None:
        self._local_state = local_state
        self._state = local_state.state
        self._goal_lhs = local_state.lhs.copy() if local_state.lhs else None
        self._goal_rhs = local_state.rhs.copy() if local_state.rhs else None
        self._goal_stack: List[Tuple[Graph,Graph]] = []

    def has_goal(self) -> bool:
        return self._goal_lhs is not None and self._goal_rhs is not None

    def push_goal(self) -> None:
        if not self._goal_lhs or not self._goal_rhs: return
        self._goal_stack.append((self._goal_lhs.copy(), self._goal_rhs.copy()))

    def pop_goal(self) -> bool:
        if len(self._goal_stack) > 0:
            self._goal_lhs, self._goal_rhs = self._goal_stack.pop()
            return True
        else:
            return False


    def next(self) -> Graph:
        raise NotImplementedError('Tactic.next() must be implemented in subclass')

    def check(self) -> None:
        raise NotImplementedError('Tactic.check() must be implemented in subclass')

    def try_validate_goal(self) -> bool:
        if not self._goal_lhs or not self._goal_rhs: return False

        if (self._local_state.status != state.RewriteState.INVALID and
            find_iso(self._goal_lhs, self._goal_rhs)):
            self._local_state.status = state.RewriteState.VALID
            return True
        else:
            return False

