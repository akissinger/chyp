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
from typing import Callable, List, Optional
from PySide6.QtCore import QByteArray, QDir, QFileInfo, QSettings, Qt
from PySide6.QtGui import QActionGroup, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMenuBar, QMessageBox, QTabWidget, QVBoxLayout, QWidget

from .editor import Editor


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        conf = QSettings('chyp', 'chyp')

        self.setWindowTitle("chyp")

        self.tabs = QTabWidget()
        self.tabs.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabs.currentChanged.connect(self.tab_changed)

        w = QWidget(self)
        w.setLayout(QVBoxLayout())
        self.setCentralWidget(w)
        w.layout().setContentsMargins(0,0,0,0)
        w.layout().setSpacing(0)
        w.layout().addWidget(self.tabs)
        self.resize(1600, 800)
        
        geom = conf.value("editor_window_geometry")
        if geom and isinstance(geom, QByteArray): self.restoreGeometry(geom)
        self.show()

        self.active_editor: Optional[Editor] = None
        self.add_tab(Editor(), "Untitled")
        self.update_file_name()
        self.build_menu()


    def remove_empty_editor(self) -> None:
        if self.active_editor:
            if self.active_editor.title() == 'Untitled' and self.active_editor.doc.toPlainText() == '':
                self.tabs.removeTab(self.tabs.indexOf(self.active_editor))
                self.active_editor = None

    def update_file_name(self) -> None:
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, Editor):
                self.tabs.setTabText(i, w.title())
        if self.active_editor:
            self.setWindowTitle('chyp - ' + self.active_editor.title())

    def tab_changed(self, i: int) -> None:
        w = self.tabs.widget(i)
        if isinstance(w, Editor):
            self.active_editor = w
            self.active_editor.code_view.setFocus()
            self.update_file_name()

    def update_themes(self) -> None:
        conf = QSettings('chyp', 'chyp')
        theme_name = conf.value('theme')
        if not theme_name or not isinstance(theme_name, str):
            theme_name = 'catppuccin_macchiato'

        def set_th(t: str) -> Callable:
            def f() -> None:
                conf.setValue('theme', t)
                QMessageBox.information(self, 'Theme set',
                                        'You must restart Chyp for the new theme to take effect.')
            return f

        themes_group = QActionGroup(self)

        view_themes_dark = self.view_themes.addAction("Dark")
        view_themes_dark.setCheckable(True)
        view_themes_dark.setChecked(theme_name == 'catppuccin_macchiato')
        view_themes_dark.triggered.connect(set_th('catppuccin_macchiato'))

        view_themes_light = self.view_themes.addAction("Light")
        view_themes_light.setCheckable(True)
        view_themes_light.setChecked(theme_name == 'catppuccin_latte')
        view_themes_light.triggered.connect(set_th('catppuccin_latte'))

        themes_group.addAction(view_themes_dark)
        themes_group.addAction(view_themes_light)

    def recent_files(self) -> List[str]:
        conf = QSettings('chyp', 'chyp')
        o = conf.value('recent_files', [])
        return o if isinstance(o, list) else []

    def update_recent_files(self) -> None:
        def open_recent(f: str) -> Callable:
            return lambda: self.open(f)

        self.file_open_recent.clear()
        for f in self.recent_files():
            fi = QFileInfo(f)
            action = self.file_open_recent.addAction(fi.fileName())
            action.triggered.connect(open_recent(f))

    def add_tab(self, editor: Editor, title: str) -> None:
        self.tabs.addTab(editor, title)
        editor.doc.fileNameChanged.connect(self.update_file_name)
        editor.doc.modificationChanged.connect(self.update_file_name)
        self.tabs.setCurrentWidget(editor)
        editor.reset_state()

    def close_tab(self, editor: Optional[Editor]=None) -> bool:
        if editor is None:
            editor = self.active_editor

        if editor:
            i = self.tabs.indexOf(editor)
            if i != -1 and editor.doc.confirm_close():
                editor.doc.fileNameChanged.disconnect(self.update_file_name)
                editor.doc.modificationChanged.disconnect(self.update_file_name)
                self.tabs.removeTab(i)

                if self.tabs.count() == 0:
                    app = QApplication.instance()
                    if app:
                        app.quit()

                return True

        return False

    def new(self) -> None:
        self.remove_empty_editor()
        editor = Editor()
        self.add_tab(editor, "Untitled")

    def open(self, file_name: str='') -> None:
        conf = QSettings('chyp', 'chyp')

        # if no file name provided, show open dialog
        if file_name == '':
            o = conf.value('last_dir')
            last_dir = o if isinstance(o, str) else QDir.home().absolutePath()
            file_name, _ = QFileDialog.getOpenFileName(self,
                                                       "Open File",
                                                       last_dir,
                                                       'chyp files (*.chyp)')

        # if file is already open, just focus the tab
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, Editor) and w.doc.file_name == file_name:
                self.tabs.setCurrentWidget(w)
                return

        try:
            editor = Editor()
            editor.doc.open(file_name)
            conf.setValue('last_dir', QFileInfo(file_name).absolutePath())
            self.remove_empty_editor()
            self.update_recent_files()
            editor.doc.fileNameChanged.connect(self.update_file_name)
            self.add_tab(editor, editor.title())
        except FileNotFoundError:
            QMessageBox.warning(self, "File not found", "File not found: " + file_name)


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

    def next_tab(self) -> None:
        c = self.tabs.count()
        if c != 0:
            i = (self.tabs.currentIndex() + 1) % c
            self.tabs.setCurrentIndex(i)

    def previous_tab(self) -> None:
        c = self.tabs.count()
        if c != 0:
            i = (self.tabs.currentIndex() - 1) % c
            self.tabs.setCurrentIndex(i)

    def goto_import(self) -> None:
        if self.active_editor:
            f = self.active_editor.import_at_cursor()
            if f:
                self.open(f)


    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('chyp', 'chyp')
        conf.setValue("editor_window_geometry", self.saveGeometry())

        if self.active_editor:
            conf.setValue("editor_splitter_state", self.active_editor.splitter.saveState())
            sizes = self.active_editor.splitter.sizes()
            if sizes[2] != 0:
                conf.setValue('error_panel_size', sizes[2])

        while self.tabs.count() > 0:
            w = self.tabs.widget(0)
            if isinstance(w, Editor):
                if not self.close_tab(w):
                    e.ignore()
                    return
            else:
                raise RuntimeError("Unexpected widget in tab list")

        e.accept()

    def build_menu(self) -> None:
        menu = QMenuBar()
        file_menu = menu.addMenu("&File")
        edit_menu = menu.addMenu("&Edit")
        code_menu = menu.addMenu("&Code")
        view_menu = menu.addMenu("&View")

        file_new = file_menu.addAction("&New")
        file_new.triggered.connect(lambda: self.new())

        file_open = file_menu.addAction("&Open")
        file_open.setShortcut(QKeySequence(QKeySequence.StandardKey.Open))
        file_open.triggered.connect(lambda: self.open())

        self.file_open_recent = file_menu.addMenu("Open &Recent")
        self.update_recent_files()

        file_menu.addSeparator()

        file_close = file_menu.addAction("&Close")
        file_close.setShortcut(QKeySequence(QKeySequence.StandardKey.Close))
        file_close.triggered.connect(lambda: self.close_tab())

        file_save = file_menu.addAction("&Save")
        file_save.setShortcut(QKeySequence(QKeySequence.StandardKey.Save))
        file_save.triggered.connect(lambda: self.save())

        file_save_as = file_menu.addAction("Save &As")
        file_save_as.setShortcut(QKeySequence(QKeySequence.StandardKey.SaveAs))
        file_save_as.triggered.connect(lambda: self.save_as())

        file_menu.addSeparator()

        file_exit = file_menu.addAction("E&xit")
        file_exit.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))

        app = QApplication.instance()
        if app:
            file_exit.triggered.connect(app.quit)

        edit_undo = edit_menu.addAction("&Undo")
        edit_undo.setShortcut(QKeySequence(QKeySequence.StandardKey.Undo))
        edit_undo.triggered.connect(lambda: self.undo())

        edit_redo = edit_menu.addAction("&Redo")
        edit_redo.setShortcut(QKeySequence(QKeySequence.StandardKey.Redo))
        edit_redo.triggered.connect(lambda: self.redo())

        # code_run = code_menu.addAction("&Run")
        # code_run.setShortcut(QKeySequence("Ctrl+R"))
        # code_run.triggered.connect(self.update_state)

        code_show_errors = code_menu.addAction("Show &Errors")
        code_show_errors.setShortcut(QKeySequence("F4"))
        code_show_errors.triggered.connect(lambda: self.show_errors())

        code_add_rewrite_step = code_menu.addAction("&Add Rewrite Step")
        code_add_rewrite_step.setShortcut(QKeySequence("Ctrl+Return"))
        code_add_rewrite_step.triggered.connect(lambda: self.add_rewrite_step())

        code_add_rewrite_step = code_menu.addAction("&Repeat Rewrite Step")
        code_add_rewrite_step.setShortcut(QKeySequence("Ctrl+Shift+Return"))
        code_add_rewrite_step.triggered.connect(lambda: self.repeat_rewrite_step())

        code_next_rewrite = code_menu.addAction("&Next Rewrite")
        code_next_rewrite.setShortcut(QKeySequence("Ctrl+N"))
        code_next_rewrite.triggered.connect(lambda: self.next_rewrite())

        code_menu.addSeparator()

        code_next_part = code_menu.addAction("Next &Part")
        code_next_part.setShortcut(QKeySequence("Ctrl+J"))
        code_next_part.triggered.connect(lambda: self.next_part())

        code_previous_part = code_menu.addAction("Previous &Part")
        code_previous_part.setShortcut(QKeySequence("Ctrl+K"))
        code_previous_part.triggered.connect(lambda: self.previous_part())

        view_next_tab = view_menu.addAction("&Next Tab")
        view_next_tab.setShortcut(QKeySequence("Ctrl+]"))
        view_next_tab.triggered.connect(lambda: self.next_tab())

        view_previous_tab = view_menu.addAction("&Previous Tab")
        view_previous_tab.setShortcut(QKeySequence("Ctrl+["))
        view_previous_tab.triggered.connect(lambda: self.previous_tab())

        view_menu.addSeparator()
        view_goto_import = view_menu.addAction("&Go To Import")
        view_goto_import.setShortcut(QKeySequence("Ctrl+G"))
        view_goto_import.triggered.connect(lambda: self.goto_import())

        view_menu.addSeparator()
        self.view_themes = view_menu.addMenu("&Themes")
        self.update_themes()

        self.setMenuBar(menu)
