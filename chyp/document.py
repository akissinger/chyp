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
from PyQt5.QtCore import QDir, QFileInfo, Qt, QSettings, QObject, pyqtSlot
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from . import editor

class Document(QObject):
    def __init__(self, editor: "editor.Editor"):
        super().__init__()
        self.editor = editor
        self.code_view = editor.code_view
        self.file_name = ''

    def recent_files(self) -> List[str]:
        conf = QSettings('chyp', 'chyp')
        return conf.value('recent_files', [])

    def add_to_recent_files(self, file_name: str):
        conf = QSettings('chyp', 'chyp')
        recent_files: List[str] = conf.value('recent_files', [])
        recent_files = [f for f in recent_files if f != file_name]
        recent_files.insert(0, file_name)
        recent_files = recent_files[:10]
        conf.setValue('recent_files', recent_files)
        self.editor.update_open_recent()

    def new(self):
        self.file_name = ''
        self.code_view.setPlainText('')

    def load(self, file_name: str):
        self.file_name = file_name
        with open(file_name) as f:
            self.code_view.setPlainText(f.read())
        self.add_to_recent_files(self.file_name)

    def save(self):
        if self.file_name:
            with open(self.file_name, 'w') as f:
                f.write(self.code_view.toPlainText())
            self.add_to_recent_files(self.file_name)
        else:
            self.save_as()

    def open(self):
        conf = QSettings('chyp', 'chyp')
        last_dir = conf.value('last_dir', QDir.home().absolutePath())
        file_name, _ = QFileDialog.getOpenFileName(self.editor,
                                                   self.tr("Open File"),
                                                   last_dir,
                                                   'chyp files (*.chyp)')
        if file_name:
            conf.setValue('last_dir', QFileInfo(file_name).absolutePath())
            self.load(file_name)

    def save_as(self):
        conf = QSettings('chyp', 'chyp')
        last_dir = conf.value('last_dir', QDir.home().absolutePath())
        file_name, _ = QFileDialog.getSaveFileName(self.editor,
                                                   self.tr("Save File"),
                                                   last_dir,
                                                   'chyp files (*.chyp)')
        if file_name:
            self.file_name = file_name
            conf.setValue('last_dir', QFileInfo(file_name).absolutePath())
            self.save()


