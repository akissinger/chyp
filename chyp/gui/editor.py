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
from typing import Callable, Optional, cast
from PySide6.QtCore import QByteArray, QFileInfo, QObject, QThread, QTimer, Qt, QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QTreeView, QVBoxLayout, QWidget, QTabWidget

from .. import parser
from .. import checker
from ..layout import convex_layout
from ..graph import Graph
from ..state import Part, ProofStepPart, State, RewritePart, GraphPart, ImportPart, TwoGraphPart
from .. import proofstate

from . import mainwindow
from .colors import current_theme
from .errorlistmodel import ErrorListModel
from .proofstatemodel import ProofStateModel
from .graphview import GraphView
from .codeview import CodeView
from .document import ChypDocument
# from .. import state

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

        self.state = State() # latest parsed state
        self.code = "" # source code used to produce latest parsed state

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

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.splitter.addWidget(self.tabs)

        self.goal_view = QTreeView()
        self.goal_view.setIndentation(0)
        self.goal_view.setModel(ProofStateModel())
        self.goal_view.setHeaderHidden(True)
        self.goal_view.clicked.connect(self.show_selected_formula)
        self.tabs.addTab(self.goal_view, "Goals")

        self.error_view = QTreeView()
        self.error_view.setIndentation(0)
        self.error_view.setModel(ErrorListModel())
        self.error_view.clicked.connect(self.jump_to_error)
        self.tabs.addTab(self.error_view, "Errors")

        splitter_state = conf.value("editor_splitter_state")
        if splitter_state and isinstance(splitter_state, QByteArray): self.splitter.restoreState(splitter_state)

        self.code_view.cursorPositionChanged.connect(self.show_at_cursor)
        self.code_view.textChanged.connect(self.invalidate_text)
        self.parsed = True

        # keep a revision count, so we don't trigger parsing until the user stops typing for a bit
        self.revision = 0

        # index of the part of the parsed document we're currently looking at
        # self.current_part = -1


    def title(self) -> str:
        if self.doc.file_name:
            fi = QFileInfo(self.doc.file_name)
            title = fi.fileName()
        else:
            title = 'Untitled'

        if self.doc.isModified():
            title += '*'

        return title

    def set_state(self, state: State) -> None:
        self.state = state
        self.code_view.set_state(state)

    def reset_state(self) -> None:
        cursor = self.code_view.textCursor()
        cursor.setPosition(0)
        self.code_view.setTextCursor(cursor)

    def invalidate_text(self) -> None:
        self.parsed = False
        self.state.set_current_part(None)
        self.code_view.state_changed()
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
        p = self.state.part_at(pos)
        i = p.index if p else 0
        i += step

        if i >= 0 and i < len(self.state.parts):
            p1 = self.state.parts[i]
            cursor.setPosition(p1.end)
            self.code_view.setTextCursor(cursor)

    def show_selected_formula(self) -> None:
        model = cast(ProofStateModel, self.goal_view.model())
        i = self.goal_view.currentIndex().row()
        if model.proof_state != None:
            _, rule = model.formula_at_index(i)
            self.lhs_view.set_graph(rule.lhs)
            self.rhs_view.set_graph(rule.rhs)
        else:
            self.lhs_view.set_graph(Graph())
            self.rhs_view.set_graph(Graph())

    def jump_to_error(self) -> None:
        model = self.error_view.model()
        window = self.window()
        i = self.error_view.currentIndex().row()
        if isinstance(model, ErrorListModel) and isinstance(window, mainwindow.MainWindow):
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

    def update_proof_state(self, proof_state: Optional[proofstate.ProofState], status: int=Part.UNCHECKED) -> None:
        proof_state_model = cast(ProofStateModel, self.goal_view.model())
        proof_state_model.set_proof_state(proof_state)
        if proof_state:
            self.tabs.setTabText(0, f'Goals ({proof_state.num_goals()})')
            if status == Part.VALID:
                self.tabs.tabBar().setTabTextColor(0, current_theme()['fg_good'])
            elif status == Part.INVALID:
                self.tabs.tabBar().setTabTextColor(0, current_theme()['fg_bad'])
            else:
                self.tabs.tabBar().setTabTextColor(0, current_theme()['fg_button'])
            if len(proof_state.goals) > 0:
                goal_i = len(proof_state.goals[0].assumptions)
                self.goal_view.setCurrentIndex(proof_state_model.index(goal_i, 0))
        else:
            self.tabs.setTabText(0, f'Goals')
            self.tabs.tabBar().setTabTextColor(0, current_theme()['fg_button'])

    def show_at_cursor(self) -> None:
        if not self.parsed: return
        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        self.state.set_current_part(part)
        self.code_view.state_changed()
        if not part: return

        if isinstance(part, ProofStepPart) and part.proof_state:
            if not part.layed_out and part.proof_state:
                for g in part.proof_state.goals:
                    convex_layout(g.formula.lhs)
                    convex_layout(g.formula.rhs)
                    for asm in g.assumptions.values():
                        convex_layout(asm.lhs)
                        convex_layout(asm.rhs)
                part.layed_out = True
            self.update_proof_state(part.proof_state, part.status)
            self.rhs_view.setVisible(True)
            self.show_selected_formula()

        elif isinstance(part, GraphPart) and part.name in self.state.graphs:
            if not part.layed_out:
                convex_layout(part.graph)
                part.layed_out = True
            self.update_proof_state(None)
            self.rhs_view.setVisible(False)
            self.lhs_view.set_graph(part.graph)

        elif isinstance(part, TwoGraphPart):
            lhs = part.lhs if part.lhs else Graph()
            rhs = part.rhs if part.rhs else Graph()
            if not part.layed_out:
                convex_layout(lhs)
                convex_layout(rhs)
                part.layed_out = True
            self.update_proof_state(None)
            self.rhs_view.setVisible(True)
            self.lhs_view.set_graph(lhs)
            self.rhs_view.set_graph(rhs)

        else:
            self.update_proof_state(None)
            self.rhs_view.setVisible(False)
            self.lhs_view.set_graph(Graph())

    def next_rewrite_at_cursor(self) -> None:
        self.update_state()
        if not self.parsed: return

        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        if part and isinstance(part, RewritePart):
            start, end = part.term_pos
            text = self.code_view.toPlainText()
            term = text[start:end]
            rw_term = checker.next_rhs(self.state, part, term)
            if rw_term:
                cursor = self.code_view.textCursor()
                cursor.clearSelection()
                cursor.setPosition(start)
                cursor.setPosition(end, mode=QTextCursor.MoveMode.KeepAnchor)

                cursor.insertText(rw_term)
                self.code_view.setTextCursor(cursor)

    def repeat_step_at_cursor(self) -> None:
        self.update_state()
        pos = self.code_view.textCursor().position()
        part = self.state.part_at(pos)
        if part and isinstance(part, RewritePart):
            tactic = part.tactic
            args = ', '.join(part.tactic_args)

            if tactic == 'rule':
                self.code_view.add_line_below('  = ? by ' + args)
            else:
                self.code_view.add_line_below(f'  = ? by {tactic}({args})')

            self.update_state()
            self.next_rewrite_at_cursor()

    def update_state(self) -> None:
        self.code = self.doc.toPlainText()
        def f() -> None:
            self.show_at_cursor()
            model = self.error_view.model()
            if isinstance(model, ErrorListModel):
                model.set_errors(self.state.errors)

            num_errors = len(self.state.errors)
            if num_errors == 0:
                self.parsed = True
                self.code_view.set_completions(self.state.rules.keys())
                self.show_at_cursor()
                self.tabs.setTabText(1, 'Errors')
                self.tabs.tabBar().setTabTextColor(1, current_theme()['fg_button'])
            else:
                self.tabs.setTabText(1, f'Errors ({num_errors})')
                self.tabs.tabBar().setTabTextColor(1, current_theme()['fg_bad'])
        self.show_at_cursor()
        update = UpdateThread(self.revision, self)
        update.finished.connect(f)
        update.start()

        

    def import_at_cursor(self) -> str:
        p = self.state.part_at(self.code_view.textCursor().position())
        if p and isinstance(p, ImportPart):
            return p.name
        else:
            return ''

class UpdateThread(QThread):
    def __init__(self, revision: int, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.revision = revision
        if parent and isinstance(parent, Editor):
            self.editor = parent

    def run(self) -> None:
        if not self.editor: return

        state = parser.parse(self.editor.code, self.editor.doc.file_name)
        state.revision = self.revision
        if state.revision != self.editor.revision: return

        def update_gui() -> None:
            self.editor.show_at_cursor()
        def gui_revision() -> int:
            return self.editor.revision

        self.editor.set_state(state)
        timer = QTimer()
        timer.setInterval(200)
        timer.timeout.connect(update_gui)
        timer.start()
        checker.check(state, gui_revision)
        timer.stop()

