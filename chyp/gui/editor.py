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
from typing import Callable, Dict, Optional, Tuple
from PySide6.QtCore import QByteArray, QFileInfo, QObject, QThread, Qt, QSettings
from PySide6.QtGui import QCloseEvent, QKeySequence, QTextCursor
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QMenuBar, QSplitter, QTreeView, QVBoxLayout, QWidget

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
        if geom and isinstance(geom, QByteArray): self.restoreGeometry(geom)
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
        self.doc = ChypDocument(self)
        self.code_view.setDocument(self.doc)
        self.doc.fileNameChanged.connect(self.update_file_name)
        self.doc.modificationChanged.connect(self.update_file_name)
        self.doc.recentFilesChanged.connect(self.update_recent_files)
        self.update_file_name()

        self.splitter.addWidget(self.code_view)
        self.code_view.setFocus()

        self.error_view = QTreeView()
        self.error_view.setModel(ErrorListModel())
        self.splitter.addWidget(self.error_view)

        self.build_menu()

        splitter_state = conf.value("editor_splitter_state")
        if splitter_state and isinstance(splitter_state, QByteArray): self.splitter.restoreState(splitter_state)

        self.code_view.cursorPositionChanged.connect(self.show_at_cursor)
        self.code_view.textChanged.connect(self.invalidate_text)
        self.parsed = True

        # keep a cache of graphs that have already been laid out
        self.graph_cache : Dict[int, Tuple[Graph, Optional[Graph]]] = dict()

    def build_menu(self) -> None:
        menu = QMenuBar()
        file_menu = menu.addMenu("&File")
        edit_menu = menu.addMenu("&Edit")
        code_menu = menu.addMenu("&Code")

        file_new = file_menu.addAction("&New")
        file_new.triggered.connect(self.doc.new)

        file_open = file_menu.addAction("&Open")
        file_open.setShortcut(QKeySequence(QKeySequence.StandardKey.Open))
        file_open.triggered.connect(lambda: self.doc.open())

        self.file_open_recent = file_menu.addMenu("Open &Recent")
        self.update_recent_files()

        file_menu.addSeparator()

        file_save = file_menu.addAction("&Save")
        file_save.setShortcut(QKeySequence(QKeySequence.StandardKey.Save))
        file_save.triggered.connect(self.doc.save)

        file_save_as = file_menu.addAction("Save &As")
        file_save_as.setShortcut(QKeySequence(QKeySequence.StandardKey.SaveAs))
        file_save_as.triggered.connect(self.doc.save_as)

        file_menu.addSeparator()

        file_exit = file_menu.addAction("E&xit")
        file_exit.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))

        app = QApplication.instance()
        if app:
            file_exit.triggered.connect(app.quit)

        edit_undo = edit_menu.addAction("&Undo")
        edit_undo.setShortcut(QKeySequence(QKeySequence.StandardKey.Undo))
        edit_undo.triggered.connect(self.code_view.undo)

        edit_redo = edit_menu.addAction("&Redo")
        edit_redo.setShortcut(QKeySequence(QKeySequence.StandardKey.Redo))
        edit_redo.triggered.connect(self.code_view.redo)

        # code_run = code_menu.addAction("&Run")
        # code_run.setShortcut(QKeySequence("Ctrl+R"))
        # code_run.triggered.connect(self.update_state)

        code_show_errors = code_menu.addAction("Show &Errors")
        code_show_errors.setShortcut(QKeySequence("F4"))
        code_show_errors.triggered.connect(self.show_errors)

        code_add_rewrite_step = code_menu.addAction("&Add Rewrite Step")
        code_add_rewrite_step.setShortcut(QKeySequence("Ctrl+Return"))
        code_add_rewrite_step.triggered.connect(lambda: self.code_view.add_line_below("  = ? by "))

        code_add_rewrite_step = code_menu.addAction("&Repeat Rewrite Step")
        code_add_rewrite_step.setShortcut(QKeySequence("Ctrl+Shift+Return"))
        code_add_rewrite_step.triggered.connect(self.repeat_step_at_cursor)

        code_next_rewrite = code_menu.addAction("&Next Rewrite")
        code_next_rewrite.setShortcut(QKeySequence("Ctrl+N"))
        code_next_rewrite.triggered.connect(self.next_rewrite_at_cursor)

        code_menu.addSeparator()

        code_next_part = code_menu.addAction("Next &Part")
        code_next_part.setShortcut(QKeySequence("Ctrl+J"))
        code_next_part.triggered.connect(lambda: self.next_part(step=1))

        code_previous_part = code_menu.addAction("Previous &Part")
        code_previous_part.setShortcut(QKeySequence("Ctrl+K"))
        code_previous_part.triggered.connect(lambda: self.next_part(step=-1))

        self.setMenuBar(menu)

    def update_file_name(self) -> None:
        title = 'chyp - '
        if self.doc.file_name:
            fi = QFileInfo(self.doc.file_name)
            title += fi.fileName()
        else:
            title += 'Untitled'

        if self.doc.isModified():
            title += '*'

        self.setWindowTitle(title)

    def update_recent_files(self) -> None:
        def open_recent(f: str) -> Callable:
            return lambda: self.doc.open(f)

        self.file_open_recent.clear()
        for f in self.doc.recent_files():
            fi = QFileInfo(f)
            action = self.file_open_recent.addAction(fi.fileName())
            action.triggered.connect(open_recent(f))

    def invalidate_text(self) -> None:
        self.parsed = False
        self.graph_cache = dict()
        self.code_view.set_current_region(None)
        self.update_state(quiet=True)

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
            

    def show_errors(self):
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
        if p:
            i, part = p
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
                if i not in self.graph_cache:
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
                    cursor.insertText(rw_term)
                    self.code_view.setTextCursor(cursor)
                    self.update_state()

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

    def update_state(self, quiet: bool=False) -> None:
        self.code_view.set_current_region(None)
        self.state.update(self.code_view.toPlainText())
        
        model = self.error_view.model()
        if isinstance(model, ErrorListModel):
            model.set_errors(self.state.errors)

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
        if self.doc.confirm_close():
            conf = QSettings('chyp', 'chyp')
            conf.setValue("editor_window_geometry", self.saveGeometry())
            conf.setValue("editor_splitter_state", self.splitter.saveState())
            sizes = self.splitter.sizes()
            if sizes[2] != 0:
                conf.setValue('error_panel_size', sizes[2])
            e.accept()
        else:
            e.ignore()

class CheckThread(QThread):
    def __init__(self, rw: RewriteState, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.rw = rw

    def run(self) -> None:
        self.rw.check()
