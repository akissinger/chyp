from typing import Any, List, Optional, Tuple
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QFont

class ErrorListModel(QAbstractItemModel):
    """A model containing a list of errors, with line numbers"""
    errors: List[Tuple[int,str]]

    def __init__(self) -> None:
        super().__init__()
        self.errors = []

    def set_errors(self, errors: List[Tuple[int, str]]) -> None:
        self.beginResetModel()
        self.errors = errors
        self.endResetModel()

    def data(self, index: QModelIndex, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a view with errors"""

        if index.row() >= len(self.errors) or index.column() >= 2:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return self.errors[index.row()][index.column()]
        elif role == Qt.ItemDataRole.FontRole:
            return QFont("monospace", 12)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignTop

    def headerData(self, section: int, orientation: Qt.Orientation, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.headerData` to populate a view with column names"""

        if role == Qt.ItemDataRole.DisplayRole and section <= 1:
            return "Line" if section == 0 else "Error"
        else:
            return None

    def index(self, row: int, column: int, parent: QModelIndex=QModelIndex()) -> QModelIndex:
        """Construct a `QModelIndex` for the given row and column"""

        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index: QModelIndex=QModelIndex()) -> int:
        """The number of columns"""
        return 2

    def rowCount(self, index: QModelIndex=QModelIndex()) -> int:
        """The number of rows"""
        if not index or not index.isValid(): return len(self.errors)
        else: return 0

    def parent(self, child: Optional[QModelIndex]=None) -> Any:
        """Always return an invalid index, since there are no nested indices"""

        if not child: return super().parent()
        else: return QModelIndex()
