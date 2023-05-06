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
from typing import List
from PySide6.QtCore import QDir, QFileInfo, QSettings, Signal
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtWidgets import QFileDialog, QPlainTextDocumentLayout

from .highlighter import ChypHighlighter

from . import editor

class ChypDocument(QTextDocument):
    recentFilesChanged = Signal()
    fileNameChanged = Signal()

    def __init__(self, editor: "editor.Editor") -> None:
        super().__init__(parent=editor)
        self.setDefaultFont(QFont("monospace", 14))
        self.setDocumentLayout(QPlainTextDocumentLayout(self))
        self.highlighter = ChypHighlighter(self)
        self.editor = editor
        self.file_name = ''
        
    def recent_files(self) -> List[str]:
        conf = QSettings('chyp', 'chyp')
        o = conf.value('recent_files', [])
        return o if isinstance(o, list) else []

    def add_to_recent_files(self, file_name: str) -> None:
        conf = QSettings('chyp', 'chyp')
        o = conf.value('recent_files', [])
        recent_files: List[str] = o if isinstance(o, list) else [] 
        recent_files = [f for f in recent_files if f != file_name]
        recent_files.insert(0, file_name)
        recent_files = recent_files[:10]
        conf.setValue('recent_files', recent_files)
        self.recentFilesChanged.emit()
        # self.editor.update_open_recent()

    def new(self) -> None:
        self.file_name = ''
        self.setPlainText('')
        self.setModified(False)
        self.fileNameChanged.emit()

    def load(self, file_name: str) -> None:
        self.file_name = file_name
        with open(file_name) as f:
            self.setPlainText(f.read())
        self.add_to_recent_files(self.file_name)
        self.setModified(False)
        self.fileNameChanged.emit()

    def save(self) -> None:
        if self.file_name:
            with open(self.file_name, 'w') as f:
                f.write(self.toPlainText())
            self.add_to_recent_files(self.file_name)
            self.setModified(False)
            self.fileNameChanged.emit()
        else:
            self.save_as()

    def open(self) -> None:
        conf = QSettings('chyp', 'chyp')
        o = conf.value('last_dir')
        last_dir = o if isinstance(o, str) else QDir.home().absolutePath()
        file_name, _ = QFileDialog.getOpenFileName(self.editor,
                                                   "Open File",
                                                   last_dir,
                                                   'chyp files (*.chyp)')
        if file_name:
            conf.setValue('last_dir', QFileInfo(file_name).absolutePath())
            self.load(file_name)

    def save_as(self) -> None:
        conf = QSettings('chyp', 'chyp')
        o = conf.value('last_dir')
        last_dir = o if isinstance(o, str) else QDir.home().absolutePath()
        file_name, _ = QFileDialog.getSaveFileName(self.editor,
                                                   "Save File",
                                                   last_dir,
                                                   'chyp files (*.chyp)')
        if file_name:
            if QFileInfo(file_name).suffix() == '':
                file_name += '.chyp'
            self.file_name = file_name
            conf.setValue('last_dir', QFileInfo(file_name).absolutePath())
            self.save()


