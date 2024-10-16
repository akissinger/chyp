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

CHYP_EXAMPLES_DIR = '/Users/vd20909/projects/chyp/examples'

def load_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def load_example(filename):
    return load_file(f'{CHYP_EXAMPLES_DIR}/{filename}')



code = """
gen g: A -> B
gen f: B -> A
"""



    
def main():
    app = QApplication(sys.argv)
    
    state = parser.parse(code)
    gs = GraphScene()


    g = state.graphs['g']
    f = state.graphs['f']

    g.compose(f)

    convex_layout(g)
    gs.set_graph(g)
    gs.save('g.png', scale=2)
    














if __name__ == '__main__':
    main()
