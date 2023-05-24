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

from __future__ import annotations
from typing import Callable, Dict, Optional, Tuple
from PySide6.QtCore import QByteArray, QFileInfo, QObject, QThread, QTimer, Qt, QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QTreeView, QVBoxLayout, QWidget

from ..layout import convex_layout
from ..graph import Graph
from ..state import RewriteState, State
from ..term import graph_to_term
from ..matcher import match_rule
from ..rewrite import rewrite

from .errorlist import ErrorListModel
from .graphview import GraphView
from .codeview import CodeView
from .document import ChypDocument
from .highlighter import STATUS_GOOD, STATUS_BAD

class Editor(QWidget):
    def __init__(self) -> None:
        super().__init__()
        conf = QSettings('chyp', 'chyp')

        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)

        # save splitter position
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout().addWidget(self.splitter)

        self.state = State()

        self.lhs_view = GraphView()
        self.rhs_view = GraphView()
        self.rhs_view.setVisible(False)

        self.graph_panel = QWidget(self)
        self.graph_panel.setLayout(QHBoxLayout())
        self.graph_panel.layout().addWidget(self.lhs_view)
        self.graph_panel.layout().addWidget(self.rhs_view)
        self.splitter.addWidget(self.graph_panel)

        self.code_view = CodeView()
        self.doc = ChypDocument(self)
        self.code_view.setDocument(self.doc)
        # self.doc.documentReplaced.connect(self.reset_state)

        self.splitter.addWidget(self.code_view)

        self.error_view = QTreeView()
        self.error_view.setIndentation(0)
        self.error_view.setModel(ErrorListModel())
        self.splitter.addWidget(self.error_view)

        splitter_state = conf.value("editor_splitter_state")
        if splitter_state and isinstance(splitter_state, QByteArray): self.splitter.restoreState(splitter_state)

        self.code_view.cursorPositionChanged.connect(self.show_at_cursor)
        self.code_view.textChanged.connect(self.invalidate_text)
        self.parsed = True

        # keep a cache of graphs that have already been laid out
        self.graph_cache : Dict[int, Tuple[Graph, Optional[Graph]]] = dict()

        # keep a revision count, so we don't trigger parsing until the user stops typing for a bit
        self.revision = 0

        # index of the part of the parsed document we're currently looking at
        self.current_part = -1


    def title(self) -> str:
        if self.doc.file_name:
            fi = QFileInfo(self.doc.file_name)
            title = fi.fileName()
        else:
            title = 'Untitled'

        if self.doc.isModified():
            title += '*'

        return title

    def reset_state(self) -> None:
        cursor = self.code_view.textCursor()
        cursor.setPosition(0)
        self.code_view.setTextCursor(cursor)

    def invalidate_text(self) -> None:
        self.parsed = False
        self.current_part = -1
        self.graph_cache = dict()
        self.code_view.set_current_region(None)
        self.revision += 1

        def update(r: int) -> Callable:
            def f() -> None:
                if r == self.revision:
                    self.update_state()
            return f

        QTimer.singleShot(200, update(self.revision))
        # self.update_state(sync=False)

    def next_part(self, step:int=1) -> None:
        if not self.parsed: return

        cursor = self.code_view.textCursor()
        pos = cursor.position()
        p = self.state.part_with_index_at(pos)
        i = p[0] if p else 0
        i += step

        if i >= 0 and i < len(self.state.parts):
            p1 = self.state.parts[i]
            cursor.setPosition(p1[1])
            self.code_view.setTextCursor(cursor)
            
    def show_errors(self) -> None:
        conf = QSettings('chyp', 'chyp')
        error_panel_size = conf.value('error_panel_size', 100)
        if isinstance(error_panel_size, str):
            error_panel_size = int(error_panel_size)
        if not isinstance(error_panel_size, int) or error_panel_size == 0:
            error_panel_size = 100
        
        sizes = self.splitter.sizes()
        if sizes[2] == 0:
            sizes[2] = error_panel_size
            if sizes[1] >= error_panel_size + 50:
                sizes[1] -= error_panel_size
            else:
                sizes[0] -= error_panel_size
        else:
            conf.setValue('error_panel_size', sizes[2])
            sizes[1] += sizes[2]
            sizes[2] = 0
        self.splitter.setSizes(sizes)

    def show_at_cursor(self) -> None:
        if not self.parsed: return
        pos = self.code_view.textCursor().position()
        p = self.state.part_with_index_at(pos)
        if not p: return

        i, part = p
        # print(part)

        if i == self.current_part: return
        else: self.current_part = i

        self.code_view.set_current_region((part[0], part[1]))
        if part[2] in ('let','gen') and part[3] in self.state.graphs:
            if i not in self.graph_cache:
                g = self.state.graphs[part[3]].copy()
                convex_layout(g)
                self.graph_cache[i] = (g, None)
            else:
                g, _ = self.graph_cache[i]
            self.rhs_view.setVisible(False)
            self.lhs_view.set_graph(g)
        elif part[2] == 'rule' and part[3] in self.state.rules:
            if i not in self.graph_cache:
                lhs = self.state.rules[part[3]].lhs.copy()
                rhs = self.state.rules[part[3]].rhs.copy()
                convex_layout(lhs)
                convex_layout(rhs)
                self.graph_cache[i] = (lhs, rhs)
            else:
                lhs, rhs0 = self.graph_cache[i]
                if not rhs0: raise ValueError("Rule in graph_cache should have RHS")
                rhs = rhs0
            self.rhs_view.setVisible(True)
            self.lhs_view.set_graph(lhs)
            self.rhs_view.set_graph(rhs)
        elif part[2] == 'rewrite' and part[3] in self.state.rewrites:
            rw = self.state.rewrites[part[3]]
            if not rw.stub:
                if rw.status == RewriteState.UNCHECKED:
                    rw.status = RewriteState.CHECKING
                    def check_finished(i: int) -> Callable:
                        def f() -> None:
                            self.graph_cache.pop(i, None)
                            self.show_at_cursor()
                        return f

                    check_thread = CheckThread(rw, self)
                    check_thread.finished.connect(check_finished(i))
                    check_thread.start()

            if i not in self.graph_cache:
                lhs = rw.lhs.copy() if rw.lhs else Graph()
                rhs = rw.rhs.copy() if rw.rhs else Graph()
                convex_layout(lhs)
                convex_layout(rhs)
                self.graph_cache[i] = (lhs, rhs)
            else:
                lhs, rhs0 = self.graph_cache[i]
                if not rhs0: raise ValueError("Rewrite step in graph_cache should have RHS")
                rhs = rhs0

            if rw.status == RewriteState.VALID:
                self.code_view.set_current_region((part[0], part[1]), status=STATUS_GOOD)
            elif rw.status == RewriteState.INVALID:
                self.code_view.set_current_region((part[0], part[1]), status=STATUS_BAD)

            self.rhs_view.setVisible(True)
            self.lhs_view.set_graph(lhs)
            if rhs: self.rhs_view.set_graph(rhs)
        else:
            self.rhs_view.setVisible(False)
            self.lhs_view.set_graph(Graph())

    def next_rewrite_at_cursor(self) -> None:
        self.update_state()
        if not self.parsed: return

        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        if part and part[2] == 'rewrite' and part[3] in self.state.rewrites:
            rw = self.state.rewrites[part[3]]
            if rw.rule and rw.lhs:
                start, end = rw.term_pos
                text = self.code_view.toPlainText()
                term = text[start:end]
                seen = set([term])

                found_prev = (term == '?')
                rw_term = None
                for m in match_rule(rw.rule, rw.lhs):
                    t = graph_to_term(rewrite(rw.rule, m))
                    if found_prev and not t in seen:
                        rw_term = t
                        break
                    elif not rw_term:
                        rw_term = t

                    seen.add(t)
                    found_prev = (term == t)

                if rw_term:
                    cursor = self.code_view.textCursor()
                    cursor.clearSelection()
                    cursor.setPosition(start)
                    cursor.setPosition(end, mode=QTextCursor.MoveMode.KeepAnchor)

                    # self.blockSignals(True)
                    cursor.insertText(rw_term)
                    self.code_view.setTextCursor(cursor)
                    # self.blockSignals(False)
                    # self.update_state()

    def repeat_step_at_cursor(self) -> None:
        self.update_state()
        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        if part and part[2] == 'rewrite' and part[3] in self.state.rewrites:
            rule = self.state.rewrites[part[3]].rule

            if rule:
                self.code_view.add_line_below('  = ? by ' + rule.name)
                self.update_state()
                self.next_rewrite_at_cursor()

    def update_state(self) -> None:
        self.state = State()
        self.code_view.set_current_region(None)
        
        self.state.update(self.doc.toPlainText(), self.doc.file_name)
        model = self.error_view.model()
        if isinstance(model, ErrorListModel):
            model.set_errors(self.state.errors)

        if len(self.state.errors) == 0:
            self.parsed = True
            self.code_view.set_completions(self.state.rules.keys())
            self.show_at_cursor()

    def import_at_cursor(self) -> str:
        p = self.state.part_at(self.code_view.textCursor().position())
        if p and p[2] == 'import':
            return p[3]
        else:
            return ''

class CheckThread(QThread):
    def __init__(self, rw: RewriteState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.rw = rw

    def run(self) -> None:
        self.rw.check()

# class UpdateStateThread(QThread):
#     def __init__(self, state: State, code: str, parent: Optional[QObject] = None) -> None:
#         super().__init__(parent)
#         self.state = state
#         self.code = code

#     def run(self) -> None:
#         self.msleep(300)
#         self.state.update(self.code)
