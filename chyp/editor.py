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
from PyQt5.QtCore import Qt, QPointF, QRectF, QSettings
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from chyp.layout import layer_layout

# from . import app
from .graphview import GraphView
from .graph import Graph
from .state import State

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
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        w.layout().addWidget(self.splitter)

        self.state = State()

        self.code_view = QTextEdit()
        self.graph_view = GraphView()
        self.splitter.addWidget(self.code_view)
        self.splitter.addWidget(self.graph_view)

        splitter_state = conf.value("editor_splitter_state")
        if splitter_state: self.splitter.restoreState(splitter_state)

        run = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_R), self)
        run.activated.connect(self.update)
        self.code_view.cursorPositionChanged.connect(self.show_at_cursor)

    def show_at_cursor(self):
        pos = self.code_view.textCursor().position()
        statement = self.state.statement_at(pos)
        if (statement and
            (statement[2] == 'let' or statement[2] == 'gen') and
            statement[3] in self.state.graphs):
            g = self.state.graphs[statement[3]].copy()
            layer_layout(g)
            self.graph_view.set_graph(g)

    def update(self):
        self.state.update(self.code_view.toPlainText())
        for err in self.state.errors:
            print("%d: %s" % err)

        self.graph_view.set_graph(Graph())
        self.show_at_cursor()


    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('chyp', 'chyp')
        conf.setValue("editor_window_geometry", self.saveGeometry())
        conf.setValue("editor_splitter_state", self.splitter.saveState())
        e.accept()
