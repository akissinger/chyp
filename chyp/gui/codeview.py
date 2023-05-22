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

from sys import prefix
from typing import Iterable, Optional, Tuple
import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QTextCursor
from PySide6.QtWidgets import QCompleter, QPlainTextEdit

from .completion import CodeCompletionModel
from .document import ChypDocument
from .highlighter import BG, FG, NO_STATUS


class CodeView(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet("QPlainTextEdit {background-color: %s; color: %s}" % (BG, FG))
        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseSensitive)
        self.completer.setModelSorting(QCompleter.ModelSorting.CaseSensitivelySortedModel)
        self.completer.setWidget(self)
        self.completion_model = CodeCompletionModel(self.completer)
        # self.completion_model.set_completions(["foo", "bar", "baz"])
        self.completer.setModel(self.completion_model)
        self.completer.activated.connect(self.insert_completion)

    def popup_visible(self) -> bool:
        return self.completer.popup().isVisible()

    def set_completions(self, completions: Iterable[str]) -> None:
        self.completion_model.set_completions(completions)

    def ident_at_cursor(self) -> str:
        cursor = self.textCursor()
        block_pos = cursor.positionInBlock() + 1
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        block = cursor.selectedText()
        # print('full block: "{}"'.format(block))
        block = block[:block_pos]
        # print('chopped block: "{}"'.format(block))

        m = re.search('([a-zA-Z_][\\.a-zA-Z0-9_]*)$', block)
        if m:
            return m.group(1)
        else:
            return ''

    def insert_completion(self, completion: str) -> None:
        if self.completer.widget() is not self:
            return

        # print("inserting completion: " + completion)
        cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())

        if extra != 0:
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
            cursor.insertText(completion[-extra:])
            self.setTextCursor(cursor)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if (self.completer.popup().isVisible() and
            e.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab)):
            e.ignore()
            return

        complete = e.key() == Qt.Key.Key_Tab or (Qt.KeyboardModifier.ControlModifier in e.modifiers() and e.key() == Qt.Key.Key_Space)
        if self.completer.popup().isVisible() or complete:
            if not complete:
                super().keyPressEvent(e)

            prefix = self.ident_at_cursor()
            cursor = self.textCursor()
            cursor.setPosition(cursor.position() - len(prefix))
            cr = self.cursorRect(cursor)
            # print("prefix: " + prefix)
            if prefix != self.completer.completionPrefix():
                self.completer.setCompletionPrefix(prefix)
                self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0,0))
            cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            super().keyPressEvent(e)

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


