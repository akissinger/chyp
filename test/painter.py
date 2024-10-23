from __future__ import annotations
from typing import Dict, List, Optional, Tuple

import os.path
from typing import Any, Dict, List, Optional, Tuple
import lark
from lark import v_args
from lark.tree import Meta

from chyp import parser
from chyp.graph import Graph, GraphError, gen, perm, identity, redistributer
from chyp.rule import Rule, RuleError
from chyp.tactic import Tactic
from chyp.tactic.simptac import SimpTac
from chyp.tactic.ruletac import RuleTac
from chyp.gui.graphscene import GraphScene
from chyp.layout import convex_layout

from PySide6.QtWidgets import QApplication
import sys
from IPython.display import Image

class Painter: 
    def __init__(self): 
        # Counter for images
        self.cnt = 0 
        self.app = QApplication(sys.argv)
        self.gs = GraphScene()

    def draw(self, g: Graph, scale=1): 
        convex_layout(g)
        self.gs.set_graph(g)
        self.gs.save(f'graph-{self.cnt}.png', scale=scale)
        img = Image(filename=f'graph-{self.cnt}.png')
        self.cnt += 1
        return img


p = Painter()
def draw(g: Graph, scale=1): 
    return p.draw(g, scale=scale)
