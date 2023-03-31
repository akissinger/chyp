from typing import Optional, Tuple
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import re

KEYWORD = QColor('#8aadf4')
IDENT = QColor('#91d7e3')
NUM = QColor('#ed8796')
OP = QColor('#eed49f')

class CodeView(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("monospace", 14))
        self.highlighter = CodeHighlighter(self.document())

    def set_current_region(self, region: Optional[Tuple[int,int]]):
        self.highlighter.set_current_region(region)

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, doc: QTextDocument):
        super().__init__(doc)
        self.region = None

    def set_current_region(self, region: Optional[Tuple[int,int]]):
        self.region = region
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        ident = '[a-zA-Z_][a-zA-Z0-9_]*'
        for m in re.finditer('(^|\\W)(let|gen|rule)\\s+(%s)?' % ident, text):
            x,y = m.span(2)
            self.setFormat(x, y-x, KEYWORD)
            x,y = m.span(3)
            self.setFormat(x, y-x, IDENT)

        for m in re.finditer('[>:;*=-]', text):
            self.setFormat(m.start(), 1, OP)

        for m in re.finditer('\\W([0-9]+)\\s*(->)\\s*([0-9]+)', text):
            x,y = m.span(1)
            self.setFormat(x, y-x, NUM)
            x,y = m.span(3)
            self.setFormat(x, y-x, NUM)

        # bold the region that is currently in focus, if any
        if self.region:
            x, y = self.region
            start = self.currentBlock().position()
            length = self.currentBlock().length()
            end = start + length
            if y >= start and x < end:
                # print("setting region to: %s in block %s" % (str(self.region), str((start,end))))
                x_rel = max(x - start, 0)
                y_rel = min(y - start, length)
                for c in range(x_rel, y_rel):
                    f = self.format(c)
                    f.setFontWeight(QFont.Weight.Bold)
                    self.setFormat(c, 1, f)

