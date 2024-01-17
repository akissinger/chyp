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
from typing import Callable, Tuple
from PySide6.QtCore import QByteArray, QFileInfo, QObject, QThread, QTimer, Qt, QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QTreeView, QVBoxLayout, QWidget


from .. import parser
from ..layout import convex_layout
from ..graph import Graph
from ..state import RewriteState, State
# from ..term import graph_to_term
# from ..matcher import match_rule
# from ..rewrite import rewrite

from . import mainwindow
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
        self.layout().setContentsMargins(0, 0, 0, 0)

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
        self.error_view.clicked.connect(self.jump_to_error)
        self.splitter.addWidget(self.error_view)

        splitter_state = conf.value("editor_splitter_state")
        if splitter_state and isinstance(splitter_state, QByteArray):
            self.splitter.restoreState(splitter_state)

        self.code_view.cursorPositionChanged.connect(self.show_at_cursor)
        self.code_view.textChanged.connect(self.invalidate_text)
        self.parsed = True

        # keep a cache of graphs that have already been laid out
        self.graph_cache: dict[int, Tuple[Graph, Graph | None]] = dict()

        # keep a revision count, so we don't trigger parsing
        # until the user stops typing for a bit
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

    def next_part(self, step: int = 1) -> None:
        if not self.parsed:
            return

        cursor = self.code_view.textCursor()
        pos = cursor.position()
        index_and_part = self.state.part_with_index_at(pos)
        i = index_and_part[0] if index_and_part else 0
        i += step

        if i >= 0 and i < len(self.state.parts):
            part = self.state.parts[i]
            cursor.setPosition(part.end)
            self.code_view.setTextCursor(cursor)

    def jump_to_error(self) -> None:
        model = self.error_view.model()
        window = self.window()
        i = self.error_view.currentIndex().row()
        if (isinstance(model, ErrorListModel)
           and isinstance(window, mainwindow.MainWindow)):
            if i >= 0 and i < len(model.errors):
                err = model.errors[i]
                window.open(err[0], line_number=err[1])

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
        """Perform action for part at cursor."""
        if not self.parsed:
            return
        cursor_position = self.code_view.textCursor().position()
        index_and_part = self.state.part_with_index_at(cursor_position)
        if index_and_part is None:
            return
        index, part = index_and_part

        # If current part hasn't changed, no further processing needed.
        if index == self.current_part:
            return
        else:
            self.current_part = index

        # Highlight the current region.
        self.code_view.set_current_region((part.start, part.end))
        if (part.part_type in ('let', 'gen')
           and part.identifier in self.state.graphs):
            if index not in self.graph_cache:
                graph = self.state.graphs[part.identifier].copy()
                convex_layout(graph)
                self.graph_cache[index] = (graph, None)
            else:
                graph, _ = self.graph_cache[index]
            self.rhs_view.setVisible(False)
            self.lhs_view.set_graph(graph)
        elif part.part_type == 'rule' and part.identifier in self.state.rules:
            if index not in self.graph_cache:
                lhs = self.state.rules[part.identifier].lhs.copy()
                rhs = self.state.rules[part.identifier].rhs.copy()
                convex_layout(lhs)
                convex_layout(rhs)
                self.graph_cache[index] = (lhs, rhs)
            else:
                lhs, rhs0 = self.graph_cache[index]
                if not rhs0:
                    raise ValueError("Rule in graph_cache should have RHS")
                rhs = rhs0
            self.rhs_view.setVisible(True)
            self.lhs_view.set_graph(lhs)
            self.rhs_view.set_graph(rhs)
        elif (part.part_type == 'rewrite'
              and part.identifier in self.state.rewrites):
            rewrite = self.state.rewrites[part.identifier]
            if not rewrite.stub:
                if rewrite.status == RewriteState.UNCHECKED:
                    rewrite.status = RewriteState.CHECKING

                    def check_finished(i: int) -> Callable:
                        def f() -> None:
                            self.graph_cache.pop(i, None)
                            self.current_part = -1
                            self.show_at_cursor()
                        return f

                    check_thread = CheckThread(rewrite, self)
                    check_thread.finished.connect(check_finished(index))
                    check_thread.start()

            if index not in self.graph_cache:
                lhs = rewrite.lhs.copy() if rewrite.lhs else Graph()
                rhs = rewrite.rhs.copy() if rewrite.rhs else Graph()
                convex_layout(lhs)
                convex_layout(rhs)
                self.graph_cache[index] = (lhs, rhs)
            else:
                lhs, rhs0 = self.graph_cache[index]
                if not rhs0:
                    raise ValueError("Rewrite step in graph_cache should have RHS")
                rhs = rhs0

            if rewrite.status == RewriteState.VALID:
                self.code_view.set_current_region((part.start, part.end),
                                                  status=STATUS_GOOD)
            elif rewrite.status == RewriteState.INVALID:
                self.code_view.set_current_region((part.start, part.end),
                                                  status=STATUS_BAD)

            self.rhs_view.setVisible(True)
            self.lhs_view.set_graph(lhs)
            if rhs:
                self.rhs_view.set_graph(rhs)
        else:
            self.rhs_view.setVisible(False)
            self.lhs_view.set_graph(Graph())

    def next_rewrite_at_cursor(self) -> None:
        self.update_state()
        if not self.parsed:
            return

        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        if (part and part.part_type == 'rewrite'
           and part.identifier in self.state.rewrites):
            rw = self.state.rewrites[part.identifier]
            start, end = rw.term_pos
            text = self.code_view.toPlainText()
            term = text[start:end]
            rw_term = rw.tactic.next_rhs(term)

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
        if (part and part.part_type == 'rewrite'
           and part.identifier in self.state.rewrites):
            rw = self.state.rewrites[part.identifier]
            tactic = rw.tactic.name()
            args = ', '.join(rw.tactic.args)

            if tactic == 'rule':
                self.code_view.add_line_below('  = ? by ' + args)
            else:
                self.code_view.add_line_below(f'  = ? by {tactic}({args})')

            self.update_state()
            self.next_rewrite_at_cursor()

    def update_state(self) -> None:
        self.state = parser.parse(self.doc.toPlainText(), self.doc.file_name)
        self.code_view.set_current_region(None)

        model = self.error_view.model()
        if isinstance(model, ErrorListModel):
            model.set_errors(self.state.errors)

        if len(self.state.errors) == 0:
            self.parsed = True
            self.code_view.set_completions(self.state.rules.keys())
            self.show_at_cursor()

    def import_at_cursor(self) -> str:
        part = self.state.part_at(self.code_view.textCursor().position())
        if part and part.part_type == 'import':
            return part.identifier
        else:
            return ''


class CheckThread(QThread):
    def __init__(self, rw: RewriteState,
                 parent: QObject | None = None) -> None:
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
