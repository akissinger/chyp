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
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
# from PyQt6.QtWebEngineCore import QWebEngineUrlScheme
import sys
import os
import subprocess
from typing import Optional, Literal

from . import mainwindow


class Chyp(QApplication):
    """The main chyp application

    ...
    """

    def __init__(self) -> None:
        super().__init__(sys.argv)
        self.setApplicationName('chyp')
        self.setDesktopFileName("chyp")
        self.main_window = mainwindow.MainWindow()
        self.lastWindowClosed.connect(self.quit)



def main() -> None:
    """Main entry point for chyp"""

    chyp = Chyp()
    chyp.exec()
