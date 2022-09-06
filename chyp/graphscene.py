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
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from typing import Optional

from .graph import Graph

SCALE = 64.0

class EItem(QGraphicsRectItem):
    def __init__(self, g: Graph, e: int):
        super().__init__(-0.5 * SCALE, -1.25 * SCALE, SCALE, 2.5 * SCALE)
        self.g = g
        self.e = e
        ed = g.edge_data(e)
        self.num_s = len(ed.s)
        self.num_t = len(ed.t)
        self.setPos(ed.x * SCALE, -ed.y * SCALE)
        self.setPen(QPen(QColor(0,0,0)))
        self.setBrush(QBrush(QColor(200,200,255)))

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        super().paint(painter, option, widget)
        ed = self.g.edge_data(self.e)
        painter.setFont(QFont("sans", 14))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, str(ed.value))

class VItem(QGraphicsEllipseItem):
    def __init__(self, g: Graph, v: int):
        super().__init__(-0.0625 * SCALE, -0.0625 * SCALE, 0.125 * SCALE, 0.125 * SCALE)
        self.g = g
        self.v = v
        vd = g.vertex_data(v)
        self.setPos(vd.x * SCALE, -vd.y * SCALE)
        self.setBrush(QBrush(QColor(0,0,0)))

class TItem(QGraphicsPathItem):
    def __init__(self, vitem: VItem, eitem: EItem, i: int, src: bool):
        self.vitem = vitem
        self.eitem = eitem
        self.i = i
        self.src = src
        super().__init__()
        self.refresh()

    def refresh(self):
        path = QPainterPath()

        if self.src:
            if self.eitem.num_s == 1: offset = 0
            else: offset = (2 * self.i / (self.eitem.num_s - 1) - 1) * SCALE

            p1x = self.vitem.pos().x()
            p1y = self.vitem.pos().y()
            p2x = self.eitem.pos().x() - 0.5 * SCALE
            p2y = self.eitem.pos().y() - offset
        else:
            if self.eitem.num_t == 1: offset = 0
            else: offset = (2 * self.i / (self.eitem.num_t - 1) - 1) * SCALE

            p1x = self.eitem.pos().x() + 0.5 * SCALE
            p1y = self.eitem.pos().y() - offset
            p2x = self.vitem.pos().x()
            p2y = self.vitem.pos().y()

        path.moveTo(p1x, p1y)
        path.cubicTo(p1x + SCALE, p1y,
                     p2x - SCALE, p2y,
                     p2x, p2y)
        self.setPath(path)
        self.update(-2000,-2000,4000,4000)

class GraphScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.undo_stack = QUndoStack(self)

        self.setSceneRect(-2000, -2000, 4000, 4000)
        self.drag_start = None
        self.drag_items: List[QGraphicsItem] = []

    def set_graph(self, g: Graph):
        self.g = g
        self.clear()
        self.add_items()

    def add_items(self):
        vi = {}
        ei = {}
        for e in self.g.edges():
            ei[e] = EItem(self.g, e)
            self.addItem(ei[e])

        for v in self.g.vertices():
            vi[v] = VItem(self.g, v)
            self.addItem(vi[v])

        for e in self.g.edges():
            ed = self.g.edge_data(e)
            for i, v in enumerate(ed.s):
                ti = TItem(vi[v], ei[e], i, src=True)
                self.addItem(ti)
            for i, v in enumerate(ed.t):
                ti = TItem(vi[v], ei[e], i, src=False)
                self.addItem(ti)

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        super().mousePressEvent(e)
        
        self.drag_start = e.scenePos()
        it = self.itemAt(e.scenePos(), QTransform())

        if it and (isinstance(it, EItem) or isinstance(it, VItem)):
            self.drag_items = [(it, it.scenePos())]

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        p = e.scenePos()
        grid_size = SCALE / 8
        dx = round((p.x() - self.drag_start.x())/grid_size) * grid_size
        dy = round((p.y() - self.drag_start.y())/grid_size) * grid_size

        # move the items that have been dragged
        for it,pos in self.drag_items:
            it.setPos(QPointF(pos.x() + dx, pos.y() + dy))

        # update positions for any tentacles attached to dragged items
        for it in self.items():
            if isinstance(it, TItem):
                for it1,_ in self.drag_items:
                    if it.vitem == it1 or it.eitem == it1:
                        it.refresh()
                        break

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        self.drag_items = []

