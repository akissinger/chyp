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

from typing import Any, List, Tuple, Union
from PySide6.QtCore import QFileInfo, QPersistentModelIndex, Qt, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QFont

class ErrorListModel(QAbstractItemModel):
    """A model containing a list of errors, with line numbers"""
    errors: List[Tuple[str,int,str]]

    def __init__(self) -> None:
        super().__init__()
        self.errors = []

    def set_errors(self, errors: List[Tuple[str, int, str]]) -> None:
        self.beginResetModel()
        self.errors = errors
        self.endResetModel()

    def data(self, index: Union[QModelIndex, QPersistentModelIndex], role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a view with errors"""

        if index.row() >= len(self.errors) or index.column() >= 3:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return QFileInfo(self.errors[index.row()][0]).fileName()
            else:
                return self.errors[index.row()][index.column()] 
        elif role == Qt.ItemDataRole.FontRole:
            return QFont("monospace", 12)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignTop

    def headerData(self, section: int, orientation: Qt.Orientation, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.headerData` to populate a view with column names"""

        if role == Qt.ItemDataRole.DisplayRole:
            if section == 0: return "File"
            elif section == 1: return "Line"
            else: return "Error"
        else:
            return None

    def index(self, row: int, column: int, parent: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> QModelIndex:
        """Construct a `QModelIndex` for the given row and column"""

        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> int:
        """The number of columns"""
        return 3

    def rowCount(self, index: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> int:
        """The number of rows"""
        if not index or not index.isValid(): return len(self.errors)
        else: return 0

    def parent(self, child: Any=None) -> Any:
        """Always return an invalid index, since there are no nested indices"""
        if child is None:
            return super().parent()
        else:
            return QModelIndex()

