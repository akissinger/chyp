from typing import Any, List, Union
from PySide6.QtCore import QObject, QPersistentModelIndex, Qt, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QFont

class CodeCompletionModel(QAbstractItemModel):
    """A model containing a list of completions, with line numbers"""
    completions: List[str]

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.completions = []

    def set_completions(self, completions: List[str]) -> None:
        self.beginResetModel()
        self.completions = completions
        self.endResetModel()

    def data(self, index: Union[QModelIndex, QPersistentModelIndex], role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a view with completions"""

        if index.row() >= len(self.completions) or index.column() >= 3:
            return None

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if index.column() == 0:
                return self.completions[index.row()]
        elif role == Qt.ItemDataRole.FontRole:
            return QFont("monospace", 12)

    # def headerData(self, section: int, orientation: Qt.Orientation, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
    #     """Overrides `QAbstractItemModel.headerData` to populate a view with column names"""

    #     if role == Qt.ItemDataRole.DisplayRole:
    #         if section == 0: return "File"
    #         elif section == 1: return "Line"
    #         else: return "Error"
    #     else:
    #         return None

    def index(self, row: int, column: int, parent: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> QModelIndex:
        """Construct a `QModelIndex` for the given row and column"""

        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> int:
        """The number of columns"""
        return 1

    def rowCount(self, index: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> int:
        """The number of rows"""
        if not index or not index.isValid(): return len(self.completions)
        else: return 0

    def parent(self, child: Any=None) -> Any:
        """Always return an invalid index, since there are no nested indices"""
        if child is None:
            return super().parent()
        else:
            return QModelIndex()

