from typing import Optional, Tuple
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import re

# palette from: https://github.com/catppuccin/catppuccin
FG =      '#cad3f5'
BG =      '#24273a'
SEL =     '#363a4f'
KEYWORD = '#8aadf4'
IDENT =   '#91d7e3'
NUM =     '#ed8796'
OP =      '#eed49f'

class CodeView(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("monospace", 14))
        # self.setFont(QFont("JetBrainsMono Nerd Font", 14))
        self.setStyleSheet("QPlainTextEdit {background-color: %s; color: %s }" % (BG, FG))
        self.highlighter = CodeHighlighter(self.document())

    def set_current_region(self, region: Optional[Tuple[int,int]]):
        self.blockSignals(True)
        self.highlighter.set_current_region(region)
        self.blockSignals(False)

    def add_line_below(self, text: str):
        cursor = self.textCursor()
        if self.highlighter.region:
            cursor.setPosition(self.highlighter.region[1])
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText('\n' + text)
        self.setTextCursor(cursor)

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, doc: QTextDocument):
        super().__init__(doc)
        self.region = None

    def set_current_region(self, region: Optional[Tuple[int,int]]):
        self.region = region
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        ident = '[a-zA-Z_][a-zA-Z0-9_]*'
        for m in re.finditer('(^|\\W)(let|gen|rule|by)\\s+(%s)?' % ident, text):
            x,y = m.span(2)
            self.setFormat(x, y-x, QColor(KEYWORD))
            x,y = m.span(3)
            self.setFormat(x, y-x, QColor(IDENT))

        for m in re.finditer('(^|\\W)(rewrite)(\\W|$)', text):
            x,y = m.span(2)
            self.setFormat(x, y-x, QColor(KEYWORD))

        for m in re.finditer('[.>:;*=-\\[\\]]', text):
            self.setFormat(m.start(), 1, QColor(OP))

        for m in re.finditer('(\\W|^)([0-9]+)(\\W|$)', text):
            x,y = m.span(2)
            self.setFormat(x, y-x, QColor(NUM))

        # highlight the region that is currently in focus
        if self.region:
            x, y = self.region
            start = self.currentBlock().position()
            length = self.currentBlock().length()
            end = start + length
            if y >= start and x < end:
                x_rel = max(x - start, 0)
                y_rel = min(y - start, length)
                for c in range(x_rel, y_rel):
                    f = self.format(c)
                    f.setBackground(QColor(SEL))
                    self.setFormat(c, 1, f)

