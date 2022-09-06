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
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
# from PyQt6.QtWebEngineCore import QWebEngineUrlScheme
import sys
import os
import subprocess
from typing import Optional, Literal

from . import mainwindow


class Hyp(QApplication):
    """The main Hyp application

    ...
    """

    def __init__(self) -> None:
        super().__init__(sys.argv)
        self.setApplicationName('Hyp')
        self.setDesktopFileName("hyp")
        self.main_window = mainwindow.MainWindow(self)
        self.lastWindowClosed.connect(self.quit)



def main() -> None:
    """Main entry point for Hyp"""

    hyp = Hyp()
    hyp.exec()
