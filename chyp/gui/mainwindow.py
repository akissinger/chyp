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
from typing import Callable, List
from PySide6.QtCore import QByteArray, QFileInfo, QSettings
from PySide6.QtGui import QCloseEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QVBoxLayout, QWidget

from .editor import Editor


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        conf = QSettings('chyp', 'chyp')

        self.setWindowTitle("chyp")

        w = QWidget(self)
        w.setLayout(QVBoxLayout())
        self.setCentralWidget(w)
        w.layout().setContentsMargins(0,0,0,0)
        w.layout().setSpacing(0)
        self.resize(1600, 800)
        
        geom = conf.value("editor_window_geometry")
        if geom and isinstance(geom, QByteArray): self.restoreGeometry(geom)
        self.show()

        self.active_editor = Editor()
        w.layout().addWidget(self.active_editor)

        self.active_editor.doc.fileNameChanged.connect(self.update_file_name)
        self.active_editor.doc.modificationChanged.connect(self.update_file_name)
        self.update_file_name()
        self.build_menu()

    def build_menu(self) -> None:
        menu = QMenuBar()
        file_menu = menu.addMenu("&File")
        edit_menu = menu.addMenu("&Edit")
        code_menu = menu.addMenu("&Code")

        file_new = file_menu.addAction("&New")
        file_new.triggered.connect(self.new)

        file_open = file_menu.addAction("&Open")
        file_open.setShortcut(QKeySequence(QKeySequence.StandardKey.Open))
        file_open.triggered.connect(self.open)

        self.file_open_recent = file_menu.addMenu("Open &Recent")
        self.update_recent_files()

        file_menu.addSeparator()

        file_save = file_menu.addAction("&Save")
        file_save.setShortcut(QKeySequence(QKeySequence.StandardKey.Save))
        file_save.triggered.connect(self.save)

        file_save_as = file_menu.addAction("Save &As")
        file_save_as.setShortcut(QKeySequence(QKeySequence.StandardKey.SaveAs))
        file_save_as.triggered.connect(self.save_as)

        file_menu.addSeparator()

        file_exit = file_menu.addAction("E&xit")
        file_exit.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))

        app = QApplication.instance()
        if app:
            file_exit.triggered.connect(app.quit)

        edit_undo = edit_menu.addAction("&Undo")
        edit_undo.setShortcut(QKeySequence(QKeySequence.StandardKey.Undo))
        edit_undo.triggered.connect(self.undo)

        edit_redo = edit_menu.addAction("&Redo")
        edit_redo.setShortcut(QKeySequence(QKeySequence.StandardKey.Redo))
        edit_redo.triggered.connect(self.redo)

        # code_run = code_menu.addAction("&Run")
        # code_run.setShortcut(QKeySequence("Ctrl+R"))
        # code_run.triggered.connect(self.update_state)

        code_show_errors = code_menu.addAction("Show &Errors")
        code_show_errors.setShortcut(QKeySequence("F4"))
        code_show_errors.triggered.connect(self.show_errors)

        code_add_rewrite_step = code_menu.addAction("&Add Rewrite Step")
        code_add_rewrite_step.setShortcut(QKeySequence("Ctrl+Return"))
        code_add_rewrite_step.triggered.connect(self.add_rewrite_step)

        code_add_rewrite_step = code_menu.addAction("&Repeat Rewrite Step")
        code_add_rewrite_step.setShortcut(QKeySequence("Ctrl+Shift+Return"))
        code_add_rewrite_step.triggered.connect(self.repeat_rewrite_step)

        code_next_rewrite = code_menu.addAction("&Next Rewrite")
        code_next_rewrite.setShortcut(QKeySequence("Ctrl+N"))
        code_next_rewrite.triggered.connect(self.next_rewrite)

        code_menu.addSeparator()

        code_next_part = code_menu.addAction("Next &Part")
        code_next_part.setShortcut(QKeySequence("Ctrl+J"))
        code_next_part.triggered.connect(self.next_part)

        code_previous_part = code_menu.addAction("Previous &Part")
        code_previous_part.setShortcut(QKeySequence("Ctrl+K"))
        code_previous_part.triggered.connect(self.previous_part)

        self.setMenuBar(menu)

    def update_file_name(self) -> None:
        title = 'chyp - '
        if self.active_editor and self.active_editor.doc.file_name:
            fi = QFileInfo(self.active_editor.doc.file_name)
            title += fi.fileName()
        else:
            title += 'Untitled'

        if self.active_editor and self.active_editor.doc.isModified():
            title += '*'

        self.setWindowTitle(title)

    def recent_files(self) -> List[str]:
        conf = QSettings('chyp', 'chyp')
        o = conf.value('recent_files', [])
        return o if isinstance(o, list) else []

    def update_recent_files(self) -> None:
        def open_recent(f: str) -> Callable:
            return lambda: self.open_recent(f)

        self.file_open_recent.clear()
        for f in self.recent_files():
            fi = QFileInfo(f)
            action = self.file_open_recent.addAction(fi.fileName())
            action.triggered.connect(open_recent(f))

    def new(self) -> None:
        if self.active_editor:
            self.active_editor.doc.new()

    def open(self) -> None:
        if self.active_editor:
            self.active_editor.doc.open()
            self.update_recent_files()

    def open_recent(self, f: str):
        if self.active_editor:
            self.active_editor.doc.open(f)
            self.update_recent_files()

    def save(self) -> None:
        if self.active_editor:
            self.active_editor.doc.save()
            self.update_recent_files()

    def save_as(self) -> None:
        if self.active_editor:
            self.active_editor.doc.save_as()
            self.update_recent_files()
    
    def undo(self) -> None:
        if self.active_editor:
            self.active_editor.code_view.undo()

    def redo(self) -> None:
        if self.active_editor:
            self.active_editor.code_view.redo()

    def show_errors(self) -> None:
        if self.active_editor:
            self.active_editor.show_errors()

    def add_rewrite_step(self) -> None:
        if self.active_editor:
            self.active_editor.code_view.add_line_below("  = ? by ")

    def repeat_rewrite_step(self) -> None:
        if self.active_editor:
            self.active_editor.repeat_step_at_cursor()

    def next_rewrite(self) -> None:
        if self.active_editor:
            self.active_editor.next_rewrite_at_cursor()

    def next_part(self) -> None:
        if self.active_editor:
            self.active_editor.next_part(step=1)

    def previous_part(self) -> None:
        if self.active_editor:
            self.active_editor.next_part(step=-1)


    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('chyp', 'chyp')
        conf.setValue("main_window_geometry", self.saveGeometry())
        e.accept()
