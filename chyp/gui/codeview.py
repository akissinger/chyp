from typing import Optional, Tuple

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from .document import ChypDocument
from .highlighter import BG, FG, NO_STATUS


class CodeView(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet("QPlainTextEdit {background-color: %s; color: %s}" % (BG, FG))

    def set_current_region(self, region: Optional[Tuple[int,int]], status: int = NO_STATUS) -> None:
        doc = self.document()

        if isinstance(doc, ChypDocument):
            self.blockSignals(True)
            doc.highlighter.set_current_region(region, status)
            self.blockSignals(False)

    def add_line_below(self, text: str) -> None:
        doc = self.document()

        if isinstance(doc, ChypDocument):
            cursor = self.textCursor()
            if doc.highlighter.region:
                cursor.setPosition(doc.highlighter.region[1])
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            cursor.insertText('\n' + text)
            self.setTextCursor(cursor)


