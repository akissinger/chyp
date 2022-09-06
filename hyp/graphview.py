from __future__ import annotations
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from . import graphscene

class GraphView(QGraphicsView):
    def __init__(self):
        self.scene = graphscene.GraphScene()
        super().__init__(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
