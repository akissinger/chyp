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
import sys
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .colors import apply_theme

from .mainwindow import MainWindow


cat_macchiato_p = {
  'rosewater':  '#f4dbd6',
  'flamingo':   '#f0c6c6',
  'pink':       '#f5bde6',
  'mauve':      '#c6a0f6',
  'red':        '#ed8796',
  'maroon':     '#ee99a0',
  'peach':      '#f5a97f',
  'yellow':     '#eed49f',
  'green':      '#a6da95',
  'teal':       '#8bd5ca',
  'sky':        '#91d7e3',
  'sapphire':   '#7dc4e4',
  'blue':       '#8aadf4',
  'lavender':   '#b7bdf8',
  'text':       '#cad3f5',
  'subtext1':   '#b8c0e0',
  'subtext0':   '#a5adcb',
  'overlay2':   '#939ab7',
  'overlay1':   '#8087a2',
  'overlay0':   '#6e738d',
  'surface2':   '#5b6078',
  'surface1':   '#494d64',
  'surface0':   '#363a4f',
  'base':       '#24273a',
  'mantle':     '#1e2030',
  'crust':      '#181926',
}

catppuccin_macchiato = {
  'bg': cat_macchiato_p['base'],
  'fg': cat_macchiato_p['text'],
  'fg_bright': cat_macchiato_p['lavender'],
  'fg_dim': cat_macchiato_p['overlay1'],
  'fg_good': cat_macchiato_p['green'],
  'fg_bad': cat_macchiato_p['red'],
  'bg_alt': cat_macchiato_p['crust'],
  'bg_button': cat_macchiato_p['mantle'],
  'fg_button': cat_macchiato_p['text'],
  'fg_link': cat_macchiato_p['blue'],
  'bg_highlight': cat_macchiato_p['blue'],
  'fg_highlight': cat_macchiato_p['crust'],
}

theme = catppuccin_macchiato

class Chyp(QApplication):
    """The main chyp application

    ...
    """

    def __init__(self) -> None:
        super().__init__(sys.argv)
        self.setApplicationName('chyp')
        self.setDesktopFileName("chyp")
        apply_theme()
        self.main_window = MainWindow()
        self.lastWindowClosed.connect(self.quit)


def main() -> None:
    """Main entry point for chyp"""

    chyp = Chyp()
    chyp.exec_()
