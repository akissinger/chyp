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
from . import graphview

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

        view = graphview.GraphView()
        w.layout().addWidget(view)


    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('chyp', 'chyp')
        conf.setValue("main_window_geometry", self.saveGeometry())
        e.accept()
