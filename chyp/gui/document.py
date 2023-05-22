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
from typing import List
from PySide6.QtCore import QDir, QFileInfo, QSettings, Signal
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtWidgets import QFileDialog, QMessageBox, QPlainTextDocumentLayout, QWidget

from .highlighter import ChypHighlighter

class ChypDocument(QTextDocument):
    fileNameChanged = Signal()
    # documentReplaced = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.parent_widget = parent
        self.setDefaultFont(QFont("monospace", 14))
        self.setDocumentLayout(QPlainTextDocumentLayout(self))
        self.highlighter = ChypHighlighter(self)
        self.file_name = ''
        
    def confirm_close(self) -> bool:
        if self.isModified():
            text = "Do you wish to save changes to {}?".format(
                    self.file_name if self.file_name != '' else 'Untitled')
            res = QMessageBox.question(self.parent_widget,
                                       "Save changes",
                                       text,
                                       QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel,
                                       QMessageBox.StandardButton.Yes)

            if res == QMessageBox.StandardButton.Yes:
                return self.save()
            elif res == QMessageBox.StandardButton.No:
                return True
            else:
                return False
        else:
            return True

    def add_to_recent_files(self, file_name: str) -> None:
        conf = QSettings('chyp', 'chyp')
        o = conf.value('recent_files', [])
        recent_files: List[str] = o if isinstance(o, list) else [] 
        recent_files = [f for f in recent_files if f != file_name]
        recent_files.insert(0, file_name)
        recent_files = recent_files[:10]
        conf.setValue('recent_files', recent_files)

    def open(self, file_name: str) -> None:
        self.file_name = file_name
        with open(file_name) as f:
            self.setPlainText(f.read())
        self.add_to_recent_files(self.file_name)
        self.setModified(False)
        self.fileNameChanged.emit()

    def save(self) -> bool:
        if self.file_name:
            with open(self.file_name, 'w') as f:
                f.write(self.toPlainText())
            self.add_to_recent_files(self.file_name)
            self.setModified(False)
            self.fileNameChanged.emit()
            return True
        else:
            return self.save_as()

    def save_as(self) -> bool:
        conf = QSettings('chyp', 'chyp')
        o = conf.value('last_dir')
        last_dir = o if isinstance(o, str) else QDir.home().absolutePath()

        # open save-as box. note we confirm overwrite manually because the GTK/linux native
        # dialog doesn't do this correctly.
        file_name, _ = QFileDialog.getSaveFileName(self.parent_widget,
                                                   "Save File",
                                                   last_dir,
                                                   'chyp files (*.chyp)',
                                                   'chyp files (*.chyp)',
                                                   QFileDialog.Option.DontConfirmOverwrite)
        if file_name:
            if QFileInfo(file_name).suffix() == '':
                file_name += '.chyp'

            fi = QFileInfo(file_name)
            if fi.exists():
                res = QMessageBox.question(self.parent_widget,
                                           "Confirm overwrite",
                                           "File {} exists, do you wish to overwrite it?".format(fi.fileName()))
                if res == QMessageBox.StandardButton.No:
                    return False
            self.file_name = file_name
            conf.setValue('last_dir', QFileInfo(file_name).absolutePath())
            return self.save()
        else:
            return False


