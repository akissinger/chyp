#     chyp - A compositional hypergraph library
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
from typing import Optional
from PyQt5.QtCore import QFileInfo, QObject, QThread, Qt, QSettings
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from chyp.term import graph_to_term


# from . import app
from .layout import convex_layout
from .graphview import GraphView
from .graph import Graph
from .state import RewriteState, State
from .codeview import CodeView
from .document import Document
from .matcher import match_rule
from .rewrite import rewrite

class Editor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        conf = QSettings('chyp', 'chyp')

        self.setWindowTitle("chyp")

        w = QWidget(self)
        w.setLayout(QVBoxLayout())
        self.setCentralWidget(w)
        w.layout().setContentsMargins(0,0,0,0)
        w.layout().setSpacing(0)
        self.resize(1600, 800)
        
        geom = conf.value("editor_window_geometry")
        if geom: self.restoreGeometry(geom)
        self.show()

        # save splitter position
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        w.layout().addWidget(self.splitter)

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
        self.splitter.addWidget(self.code_view)
        self.code_view.setFocus()
        self.doc = Document(self)

        self.build_menu()

        splitter_state = conf.value("editor_splitter_state")
        if splitter_state: self.splitter.restoreState(splitter_state)

        self.code_view.cursorPositionChanged.connect(self.show_at_cursor)
        self.code_view.textChanged.connect(self.invalidate_text)
        self.parsed = True

    def build_menu(self):
        menu = QMenuBar()
        file_menu = menu.addMenu("&File")
        edit_menu = menu.addMenu("&Edit")
        code_menu = menu.addMenu("&Code")

        file_new = file_menu.addAction("&New")
        file_new.triggered.connect(self.doc.new)

        file_open = file_menu.addAction("&Open")
        file_open.setShortcut(QKeySequence.StandardKey.Open)
        file_open.triggered.connect(self.doc.open)

        self.file_open_recent = file_menu.addMenu("Open &Recent")
        self.update_file()

        file_menu.addSeparator()

        file_save = file_menu.addAction("&Save")
        file_save.setShortcut(QKeySequence.StandardKey.Save)
        file_save.triggered.connect(self.doc.save)

        file_save_as = file_menu.addAction("Save &As")
        file_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        file_save_as.triggered.connect(self.doc.save_as)

        file_menu.addSeparator()

        file_exit = file_menu.addAction("E&xit")
        file_exit.setShortcut(QKeySequence.StandardKey.Quit)
        file_exit.triggered.connect(QApplication.instance().quit)

        edit_undo = edit_menu.addAction(self.tr("&Undo"))
        edit_undo.setShortcut(QKeySequence.StandardKey.Undo)
        edit_undo.triggered.connect(self.code_view.undo)

        edit_redo = edit_menu.addAction(self.tr("&Redo"))
        edit_redo.setShortcut(QKeySequence.StandardKey.Redo)
        edit_redo.triggered.connect(self.code_view.redo)

        code_run = code_menu.addAction("&Run")
        code_run.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_R))
        code_run.triggered.connect(self.update)

        code_add_rewrite_step = code_menu.addAction("&Add Rewrite Step")
        code_add_rewrite_step.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return))
        code_add_rewrite_step.triggered.connect(lambda: self.code_view.add_line_below("  = ? by "))

        code_add_rewrite_step = code_menu.addAction("&Repeat Rewrite Step")
        code_add_rewrite_step.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Modifier.SHIFT | Qt.Key.Key_Return))
        code_add_rewrite_step.triggered.connect(self.repeat_step_at_cursor)

        code_next_rewrite = code_menu.addAction("&Next Rewrite")
        code_next_rewrite.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_N))
        code_next_rewrite.triggered.connect(self.next_rewrite_at_cursor)

        code_menu.addSeparator()

        code_next_part = code_menu.addAction("Next &Part")
        code_next_part.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_J))
        code_next_part.triggered.connect(lambda: self.next_part(step=1))

        code_previous_part = code_menu.addAction("Previous &Part")
        code_previous_part.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_K))
        code_previous_part.triggered.connect(lambda: self.next_part(step=-1))

        self.setMenuBar(menu)

    def update_file(self):
        if self.doc.file_name:
            fi = QFileInfo(self.doc.file_name)
            self.setWindowTitle('chyp - ' + fi.fileName())
        else:
            self.setWindowTitle('chyp')

        def open_rec(f):
            return lambda: self.doc.load(f)

        self.file_open_recent.clear()
        for f in self.doc.recent_files():
            fi = QFileInfo(f)
            action = self.file_open_recent.addAction(fi.fileName())
            action.triggered.connect(open_rec(f))

    def invalidate_text(self):
        self.parsed = False
        self.code_view.set_current_region(None)
        self.update(quiet=True)

    def next_part(self, step=1):
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
            

    def show_at_cursor(self):
        if not self.parsed: return

        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        if part:
            self.code_view.set_current_region((part[0], part[1]))
            if part[2] in ('let','gen') and part[3] in self.state.graphs:
                g = self.state.graphs[part[3]].copy()
                convex_layout(g)
                self.rhs_view.setVisible(False)
                self.lhs_view.set_graph(g)
            elif part[2] == 'rule' and part[3] in self.state.rules:
                lhs = self.state.rules[part[3]].lhs.copy()
                rhs = self.state.rules[part[3]].rhs.copy()
                convex_layout(lhs)
                convex_layout(rhs)
                self.rhs_view.setVisible(True)
                self.lhs_view.set_graph(lhs)
                self.rhs_view.set_graph(rhs)
            elif part[2] == 'rewrite' and part[3] in self.state.rewrites:
                rw = self.state.rewrites[part[3]]

                if not rw.stub:
                    if rw.status == RewriteState.UNCHECKED:
                        rw.status = RewriteState.CHECKING
                        check_thread = CheckThread(rw, self)
                        check_thread.finished.connect(self.show_at_cursor)
                        check_thread.start()
                    elif rw.status == RewriteState.VALID:
                        self.code_view.set_current_region((part[0], part[1]), status=CodeView.STATUS_GOOD)
                    elif rw.status == RewriteState.INVALID:
                        self.code_view.set_current_region((part[0], part[1]), status=CodeView.STATUS_BAD)

                lhs = rw.lhs.copy()
                rhs = rw.rhs.copy()
                convex_layout(lhs)
                convex_layout(rhs)
                self.rhs_view.setVisible(True)
                self.lhs_view.set_graph(lhs)
                self.rhs_view.set_graph(rhs)

    def next_rewrite_at_cursor(self):
        self.update()
        if not self.parsed: return

        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        if part and part[2] == 'rewrite' and part[3] in self.state.rewrites:
            rw = self.state.rewrites[part[3]]
            start, end = rw.term_pos
            text = self.code_view.toPlainText()
            term = text[start:end]

            found_prev = (term == '?')
            rw_term = None
            for m in match_rule(rw.rule, rw.lhs):
                t = graph_to_term(rewrite(rw.rule, m))
                if found_prev and term != t:
                    rw_term = t
                    break
                elif not rw_term:
                    rw_term = t

                found_prev = (term == t)

            if rw_term:
                self.code_view.setPlainText(text[:start] + rw_term + text[end:])
                cursor = self.code_view.textCursor()
                cursor.setPosition(pos + len(rw_term) - len(term))
                self.code_view.setTextCursor(cursor)
                self.update()

    def repeat_step_at_cursor(self):
        self.update()
        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        if part and part[2] == 'rewrite' and part[3] in self.state.rewrites:
            rule = self.state.rewrites[part[3]].rule
            self.code_view.add_line_below('  = ? by ' + rule.name)
            self.update()
            self.next_rewrite_at_cursor()

    def update(self, quiet=False):
        self.code_view.set_current_region(None)
        self.state.update(self.code_view.toPlainText())

        if len(self.state.errors) == 0:
            self.lhs_view.set_graph(Graph())
            self.rhs_view.setVisible(False)
            self.parsed = True
            self.show_at_cursor()
        elif not quiet:
            print('**********************************************************************')
            for err in self.state.errors:
                print("%d: %s" % err)

    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('chyp', 'chyp')
        conf.setValue("editor_window_geometry", self.saveGeometry())
        conf.setValue("editor_splitter_state", self.splitter.saveState())
        e.accept()

class CheckThread(QThread):
    def __init__(self, rw: RewriteState, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.rw = rw

    def run(self):
        self.rw.check()
