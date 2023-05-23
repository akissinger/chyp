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
import itertools
from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QTransform, QUndoStack
from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsItem,
                               QGraphicsPathItem, QGraphicsRectItem, QGraphicsScene,
                               QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget)

from ..graph import Graph

SCALE = 50.0

BOX_WIDTH = 1.1

class EItem(QGraphicsRectItem):
    def __init__(self, g: Graph, e: int) -> None:
        super().__init__(-0.5 * BOX_WIDTH * SCALE, -0.8 * SCALE, BOX_WIDTH * SCALE, 1.6 * SCALE)
        self.g = g
        self.e = e
        ed = g.edge_data(e)
        self.bg = ed.bg
        self.fg = ed.fg
        self.value = ed.value
        self.num_s = len(ed.s)
        self.num_t = len(ed.t)
        self.is_id = isinstance(ed.value, str) and str(ed.value) == 'id'

        self.setPos(ed.x * SCALE, ed.y * SCALE)

        if self.is_id:
            self.setRect(-0.2 * SCALE, -0.2 * SCALE, 0.4 * SCALE, 0.4 * SCALE)
            self.setPen(QPen(QColor(200,200,200)))
            self.setBrush(QBrush(QColor(200,200,200)))
            self.setVisible(False)
        else:
            if self.num_s <= 1 and self.num_t <= 1:
                self.setRect(-0.5 * BOX_WIDTH * SCALE, -0.4 * SCALE, BOX_WIDTH * SCALE, 0.8 * SCALE)

            if self.bg != '':
                self.setBrush(QBrush(QColor(self.bg)))
            else:
                self.setBrush(QBrush(QColor(200,200,255)))

            pen = QPen(QColor(0,0,0))
            if ed.highlight:
                pen.setWidth(3)
            self.setPen(pen)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None) -> None:
        super().paint(painter, option, widget)

        if self.fg != '':
            painter.setPen(QPen(QColor(self.fg)))
        painter.setFont(QFont("sans", 11))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, str(self.value)) # type:ignore

class VItem(QGraphicsEllipseItem):
    def __init__(self, g: Graph, v: int, eitem: Optional[EItem]=None, i: int=-1) -> None:
        super().__init__(-0.0625 * SCALE, -0.0625 * SCALE, 0.125 * SCALE, 0.125 * SCALE)
        self.setVisible(False)
        self.g = g
        self.v = v
        self.eitem = eitem
        self.i = i
        vd = g.vertex_data(v)
        self.setPos(vd.x * SCALE, vd.y * SCALE)
        self.setBrush(QBrush(QColor(0,0,0)))

    def refresh(self):
        if self.eitem and self.i != -1:
            x_shift = 0.7 * SCALE
            if self.eitem.num_t == 1:
                y_shift = 0
            else:
                y_shift = ((self.i / (self.eitem.num_t - 1)) - 0.5) * SCALE
            p = self.eitem.pos()
            self.setPos(p.x() + x_shift, p.y() + y_shift)

class TItem(QGraphicsPathItem):
    def __init__(self, vitem: VItem, eitem: EItem, i: int, src: bool) -> None:
        super().__init__()
        g = vitem.g
        self.vitem = vitem
        self.eitem = eitem
        if (g.vertex_data(vitem.v).highlight or
            g.edge_data(eitem.e).highlight):
            pen = QPen()
            pen.setWidth(3)
            self.setPen(pen)
        self.i = i
        self.src = src
        self.refresh()

    def refresh(self) -> None:
        path = QPainterPath()

        x_shift = (0 if self.eitem.is_id else 0.5 * BOX_WIDTH) * SCALE

        if self.src:
            if self.eitem.num_s == 1:
                y_shift = 0.0
            else:
                y_shift = ((self.i / (self.eitem.num_s - 1)) - 0.5) * SCALE

            p1x = self.vitem.pos().x()
            p1y = self.vitem.pos().y()
            p2x = self.eitem.pos().x() - x_shift
            p2y = self.eitem.pos().y() + y_shift
        else:
            if self.eitem.num_t == 1:
                y_shift = 0
            else:
                y_shift = ((self.i / (self.eitem.num_t - 1)) - 0.5) * SCALE

            p1x = self.eitem.pos().x() + x_shift
            p1y = self.eitem.pos().y() + y_shift
            p2x = self.vitem.pos().x()
            p2y = self.vitem.pos().y()

        dx = abs(p1x - p2x)
        path.moveTo(p1x, p1y)
        path.cubicTo(p1x + dx * 0.4, p1y,
                     p2x - dx * 0.4, p2y,
                     p2x, p2y)
        self.setPath(path)
        self.update(-2000,-2000,4000,4000)

class GraphScene(QGraphicsScene):
    def __init__(self) -> None:
        super().__init__()
        self.undo_stack = QUndoStack(self)

        self.setSceneRect(-2000, -2000, 4000, 4000)
        self.setBackgroundBrush(QBrush(QColor(255,255,255)))
        self.drag_start = QPointF(0,0)
        self.drag_items: List[Tuple[QGraphicsItem, QPointF]] = []

    def set_graph(self, g: Graph) -> None:
        self.g = g
        self.clear()
        self.add_items()
        self.invalidate()

    def add_items(self) -> None:
        vi = {}
        ei = {}
        for e in self.g.edges():
            ei[e] = EItem(self.g, e)
            self.addItem(ei[e])

        for v in itertools.chain(self.g.inputs(), self.g.outputs()):
            vi[v] = VItem(self.g, v)
            self.addItem(vi[v])

        for e in self.g.edges():
            ed = self.g.edge_data(e)
            for i, v in enumerate(ed.t):
                if not v in vi:
                    vi[v] = VItem(self.g, v, ei[e], i)
                    self.addItem(vi[v])

        for e in self.g.edges():
            ed = self.g.edge_data(e)
            for i, v in enumerate(ed.s):
                ti = TItem(vi[v], ei[e], i, src=True)
                self.addItem(ti)
            for i, v in enumerate(ed.t):
                ti = TItem(vi[v], ei[e], i, src=False)
                self.addItem(ti)

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(e)
        
        self.drag_start = e.scenePos()

        for it in self.items(e.scenePos(), deviceTransform=QTransform()):
            if it and (isinstance(it, EItem) or isinstance(it, VItem)):
                self.drag_items = [(it, it.scenePos())]
                break

    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent) -> None:
        p = e.scenePos()
        grid_size = SCALE / 8
        dx = round((p.x() - self.drag_start.x())/grid_size) * grid_size
        dy = round((p.y() - self.drag_start.y())/grid_size) * grid_size

        # move the items that have been dragged
        for it,pos in self.drag_items:
            it.setPos(QPointF(pos.x() + dx, pos.y() + dy))

        for it in self.items():
            # update positions for any vertices and tentacles attached to dragged items
            if isinstance(it, TItem):
                for it1,_ in self.drag_items:
                    if it.vitem == it1 or it.eitem == it1 or it.vitem.eitem == it1:
                        it.vitem.refresh()
                        it.refresh()
                        break

            # if the mouse is near a vertex or identity box, make it visible
            if isinstance(it, VItem) or (isinstance(it, EItem) and it.is_id):
                if abs(it.pos().x() - p.x()) < 10 and abs(it.pos().y() - p.y()) < 10:
                    it.setVisible(True)
                else:
                    it.setVisible(False)


    def mouseReleaseEvent(self, _: QGraphicsSceneMouseEvent) -> None:
        self.drag_items = []

