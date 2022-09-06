#     Hyp - A simple hypergraph editor
#     Copyright (C) 2021 - Aleks Kissinger
#
# This file is part of Hyp
#
# Hyp is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hyp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hyp. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from PyQt6.QtCore import Qt, QPointF, QRectF, QSettings
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import os

from . import app
from . import graphview

class MainWindow(QMainWindow):
    def __init__(self, a: app.Hyp):
        super().__init__()
        conf = QSettings('hyp', 'hyp')
        self.app = a

        # icon = os.path.dirname(__file__) + '/hyp.svg'
        # if os.path.exists(icon):
        #     self.setWindowIcon(QIcon(icon))
        self.setWindowTitle("Hyp")

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
        conf = QSettings('hyp', 'hyp')
        conf.setValue("main_window_geometry", self.saveGeometry())
        e.accept()
