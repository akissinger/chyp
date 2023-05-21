from typing import Any, Iterable, List, Union
from PySide6.QtCore import QAbstractListModel, QObject, QPersistentModelIndex, Qt, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QFont

class CodeCompletionModel(QAbstractListModel):
    """A model containing a list of completions, with line numbers"""
    completions: List[str]

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.completions = []

    def set_completions(self, completions: Iterable[str]) -> None:
        self.beginResetModel()
        self.completions = sorted(completions)
        self.endResetModel()

    def data(self, index: Union[QModelIndex, QPersistentModelIndex], role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a view with completions"""

        if index.row() >= len(self.completions) or index.column() >= 3:
            return None

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if index.column() == 0:
                return self.completions[index.row()]
        elif role == Qt.ItemDataRole.FontRole:
            return QFont("monospace", 14)

    def rowCount(self, index: Union[QModelIndex, QPersistentModelIndex]=QModelIndex()) -> int:
        """The number of rows"""
        if not index or not index.isValid(): return len(self.completions)
        else: return 0


