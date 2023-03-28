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
from PyQt6.QtCore import Qt, QPointF, QRectF, QSettings
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import os

from . import app
from .graphview import GraphView
from .graph import Graph, graph_from_json
from .matcher import match_graph, match_rule
from .rewrite import Rule, rewrite

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        conf = QSettings('chyp', 'chyp')

        # icon = os.path.dirname(__file__) + '/chyp.svg'
        # if os.path.exists(icon):
        #     self.setWindowIcon(QIcon(icon))
        self.setWindowTitle("chyp")

        w = QWidget(self)
        w.setLayout(QVBoxLayout())
        self.setCentralWidget(w)
        w.layout().setContentsMargins(0,0,0,0)
        w.layout().setSpacing(0)
        self.resize(1600, 800)
        
        geom = conf.value("main_window_geometry")
        if geom: self.restoreGeometry(geom)
        self.show()

        g = graph_from_json("""
        {
          "vertices": {
            "0": {"x": -4, "y": 1},
            "1": {"x": -4, "y": -1},
            "2": {"x": 0, "y": 0},
            "3": {"x": 4, "y": 2},
            "4": {"x": 4, "y": 1},
            "5": {"x": 4, "y": -2}
          },
          "edges": {
            "0": {"s": ["0", "1"], "t": ["2"], "x": -2, "y": 0, "value": "f"},
            "1": {"s": ["2"], "t": ["3", "4", "5"], "x": 2, "y": 0, "value": "g"},
            "2": {"s": ["3"], "t": [], "x": 6, "y": 2, "value": "x"},
            "3": {"s": ["4"], "t": [], "x": 6, "y": 2, "value": "y"}
          },
          "inputs": ["0", "1"],
          "outputs": ["5"]
        }
        """)

        g = Graph()
        v0 = g.add_vertex(-4, 1)
        v1 = g.add_vertex(-4, -1)
        v2 = g.add_vertex(0, 0)
        v3 = g.add_vertex(4, 2)
        v4 = g.add_vertex(4, 0)
        v5 = g.add_vertex(4, -2)
        g.add_edge([v0, v1], [v2], -2, 0, "f")
        g.add_edge([v2], [v3,v4,v5], 2, 0, "g")
        g.add_edge([v3], [], 6, 2, "x")
        g.add_edge([v4], [], 6, 0, "y")

        g1 = Graph()
        w0 = g1.add_vertex(0, 0)
        w1 = g1.add_vertex(2, 1)
        w2 = g1.add_vertex(2, 0)
        w3 = g1.add_vertex(2, -1)
        g1.add_edge([w0], [w1, w2, w3], 1, 0, "g")
        g1.add_edge([w1], [], 2, 0, "x")
        g1.set_inputs([w0])
        g1.set_outputs([w2, w3])

        g2 = Graph()
        w0 = g2.add_vertex(0, 0)
        w1 = g2.add_vertex(2, 0)
        w2 = g2.add_vertex(2, -1)
        g2.add_edge([w0], [w1, w2], 2, 0, "h")
        g2.set_inputs([w0])
        g2.set_outputs([w1, w2])

        r = Rule(g1, g2)

        ms = list(match_rule(r, g))
        if len(ms) != 0:
            print(ms[0])
            h = rewrite(r, ms[0])
        else:
            print("no matches")
            h = g

        self.view = GraphView()
        self.view.set_graph(g)
        w.layout().addWidget(self.view)

        self.graphs = [g, h]
        self.ix = 0
        def show_next() -> None:
            self.ix = (self.ix + 1) % len(self.graphs)
            self.view.set_graph(self.graphs[self.ix])

        button = QPushButton("next graph")
        button.clicked.connect(show_next)
        w.layout().addWidget(button)


    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('chyp', 'chyp')
        conf.setValue("main_window_geometry", self.saveGeometry())
        e.accept()
