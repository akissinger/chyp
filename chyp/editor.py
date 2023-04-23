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
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


# from . import app
from .layout import convex_layout
from .graphview import GraphView
from .graph import Graph
from .state import State
from .codeview import CodeView

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
        self.code_view.setPlainText("""gen f : 2 -> 1
gen g : 1 -> 2
let h1 = g * id
let h2 = id * f
rule frob: g * id ; id * f = f ; g

rewrite f1:
  f ; g * id ; id * f ; f
  = ? by frob
  = ? by frob
""")

        splitter_state = conf.value("editor_splitter_state")
        if splitter_state: self.splitter.restoreState(splitter_state)

        run = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_R), self)
        run.activated.connect(self.update)
        self.code_view.cursorPositionChanged.connect(self.show_at_cursor)

    def show_at_cursor(self):
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


    def update(self):
        self.code_view.set_current_region(None)
        self.state.update(self.code_view.toPlainText())
        for err in self.state.errors:
            print("%d: %s" % err)

        self.lhs_view.set_graph(Graph())
        self.show_at_cursor()


    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('chyp', 'chyp')
        conf.setValue("editor_window_geometry", self.saveGeometry())
        conf.setValue("editor_splitter_state", self.splitter.saveState())
        e.accept()
