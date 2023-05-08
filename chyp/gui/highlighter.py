from typing import Optional, Tuple
import re
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextDocument

NO_STATUS = 0
STATUS_GOOD = 1
STATUS_BAD = 2

# palette from: https://github.com/catppuccin/catppuccin
FG =      '#cad3f5'
BG =      '#24273a'
SEL =     '#363a4f'
KEYWORD = '#8aadf4'
IDENT =   '#91d7e3'
NUM =     '#ed8796'
OP =      '#eed49f'
COMMENT = '#8087a2'
BG_GOOD = '#36504f'
BG_BAD  = '#863a4f'

class ChypHighlighter(QSyntaxHighlighter):
    def __init__(self, doc: QTextDocument) -> None:
        super().__init__(doc)
        self.region: Optional[Tuple[int,int]] = None
        self.region_status = NO_STATUS

    def set_current_region(self, region: Optional[Tuple[int,int]], status: int) -> None:
        self.region = region
        self.region_status = status
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        ident = '[a-zA-Z_][a-zA-Z0-9_]*'
        for m in re.finditer('(^|\\W)(let|gen|rule|by|rewrite)\\s+\\-?\\s*(%s)?' % ident, text):
            x,y = m.span(2)
            self.setFormat(x, y-x, QColor(KEYWORD))
            x,y = m.span(3)
            self.setFormat(x, y-x, QColor(IDENT))

        for m in re.finditer('[?~.><:;*=\\-\\[\\]]', text):
            self.setFormat(m.start(), 1, QColor(OP))

        for m in re.finditer('(\\W|^)([0-9]+)(\\W|$)', text):
            x,y = m.span(2)
            self.setFormat(x, y-x, QColor(NUM))

        for m in re.finditer('#.*$', text):
            x,y = m.span(0)
            self.setFormat(x, y-x, QColor(COMMENT))

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

                    if self.region_status == STATUS_GOOD:
                        f.setBackground(QColor(BG_GOOD))
                    elif self.region_status == STATUS_BAD:
                        f.setBackground(QColor(BG_BAD))
                    else:
                        f.setBackground(QColor(SEL))
                    self.setFormat(c, 1, f)

