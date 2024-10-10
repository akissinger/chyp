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

from typing import Any, List, Tuple, Union, Optional
from PySide6.QtCore import QFileInfo, QPersistentModelIndex, Qt, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QFont, QBrush, QColor

from chyp.term import rule_to_term

from ..proofstate import ProofState
from ..rule import Rule
from .colors import current_theme

class ProofStateModel(QAbstractItemModel):
    """A model containing a list of errors, with line numbers"""
    proof_state: Optional[ProofState]

    def __init__(self) -> None:
        super().__init__()
        self.proof_state = None

    def set_proof_state(self, proof_state: ProofState) -> None:
        self.beginResetModel()
        self.proof_state = proof_state
        self.endResetModel()
    
    def num_formulas(self) -> int:
        if self.proof_state:
            return sum(1+len(g.assumptions) for g in self.proof_state.goals)
        else:
            return 0

    def formula_at_index(self, i: int) -> Tuple[str, Rule]:
        j = 0
        if self.proof_state:
            for g in self.proof_state.goals:
                for k,v in g.assumptions.items():
                    if i == j: return (k, v)
                    else: j += 1
                if i == j: return ('', g.rule)
                else: j += 1

        return ('', Rule())

    def data(self, index: Union[QModelIndex, QPersistentModelIndex], role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a view with errors"""
        if role == Qt.ItemDataRole.DisplayRole:
            if self.proof_state:
                asm, rule = self.formula_at_index(index.row())
                return f'{asm if asm != "" else " |-"} {rule_to_term(rule)}'
            return ""
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont("Cascadia Code", 14)
            font.setStyleHint(QFont.StyleHint.TypeWriter)
            return font
        elif role == Qt.ItemDataRole.ForegroundRole:
            if self.proof_state:
                asm, _ = self.formula_at_index(index.row())
                if asm != '':
                    return QBrush(QColor(current_theme()['fg_dim']))
            return QBrush(QColor(current_theme()['fg']))
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignTop

    # def headerData(self, section: int, orientation: Qt.Orientation, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
    #     """Overrides `QAbstractItemModel.headerData` to populate a view with column names"""

    #     if role == Qt.ItemDataRole.DisplayRole:
    #         return "Goal"
    #     else:
    #         return None

    def index(self, row: int, column: int, parent: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> QModelIndex:
        """Construct a `QModelIndex` for the given row and column"""

        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, parent: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> int:
        """The number of columns"""
        return 1

    def rowCount(self, parent: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> int:
        """The number of rows"""
        index = parent
        if self.proof_state and (not index or not index.isValid()):
            return self.num_formulas()
        else: return 0

    def parent(self, child: Any=None) -> Any:
        """Always return an invalid index, since there are no nested indices"""
        if child is None:
            return super().parent()
        else:
            return QModelIndex()

