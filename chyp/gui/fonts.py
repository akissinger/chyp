from platform import system

from PySide6.QtGui import QFont


monospace_font_name = "monospace" if system() != "Darwin" else "Menlo"
sans_font_name = "monospace" if system() != "Darwin" else ""

monospace_font = lambda size: QFont(monospace_font_name, size)
sans_font = lambda size: QFont(sans_font_name, size)
