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
from .graph import Graph

class MainWindow(QMainWindow):
    def __init__(self, a: app.Chyp):
        super().__init__()
        conf = QSettings('chyp', 'chyp')
        self.app = a

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

        view = GraphView()

        g = Graph()
        v0 = g.add_vertex(-4, -1)
        v1 = g.add_vertex(-4, 1)
        v2 = g.add_vertex(0, 0)
        v3 = g.add_vertex(4, -1)
        v4 = g.add_vertex(4, 0)
        v5 = g.add_vertex(4, 1)
        e0 = g.add_edge([v0, v1], [v2], -2, 0, "f")
        e1 = g.add_edge([v2], [v3,v4,v5], 2, 0, "g")

        view.set_graph(g)

        w.layout().addWidget(view)


    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('chyp', 'chyp')
        conf.setValue("main_window_geometry", self.saveGeometry())
        e.accept()
