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

from typing import Optional, Tuple
import re
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextDocument

from .colors import current_theme

NO_STATUS = 0
STATUS_GOOD = 1
STATUS_BAD = 2

# palette from: https://github.com/catppuccin/catppuccin
theme = current_theme()
FG =      theme['fg']
BG =      theme['bg']
SEL =     theme['bg_sel']
KEYWORD = theme['fg_keyword']
IDENT =   theme['fg_ident']
NUM =     theme['fg_num']
OP =      theme['fg_op']
COMMENT = theme['fg_comment']
STRING  = theme['fg_string']
BG_GOOD = theme['bg_good']
BG_BAD  = theme['bg_bad']

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
        ident = '[a-zA-Z_][\\.a-zA-Z0-9_]*'
        for m in re.finditer('(^|\\W)(let|def|gen|rule|by|rewrite|import|as|show)\\s+\\-?\\s*(%s)?' % ident, text):
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

        for m in re.finditer('"[^"]*"', text):
            x,y = m.span(0)
            self.setFormat(x, y-x, QColor(STRING))

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

