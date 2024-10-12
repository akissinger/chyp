from typing import List, Literal, Optional, Tuple

from .graph import Graph
from .rule import Rule
from .proofstate import ProofState

class Part:
    """Class representing a single statement or sub-statement in a chyp document

    A `Part` represents a chunk of text that will be highlighted when the cursor is
    over it and is (in the case of proof steps) can be checked by `checker.check`.
    """
    UNCHECKED = 0
    CHECKING = 1
    VALID = 2
    INVALID = 3

    start: int
    end: int
    line: int
    name: str
    status: int
    layed_out: bool
    index: int

    def __init__(self, start: int, end: int, line: int, name: str):
        self.start = start
        self.end = end
        self.line = line
        self.name = name
        self.status = Part.UNCHECKED
        self.layed_out = False
        self.index = -1

class GraphPart(Part):
    graph: Graph
    def __init__(self, start: int, end: int, line: int, name: str, graph: Graph):
        Part.__init__(self, start, end, line, name)
        self.graph = graph

class LetPart(GraphPart): pass
class GenPart(GraphPart): pass

class TwoGraphPart(Part):
    lhs: Optional[Graph]
    rhs: Optional[Graph]
    def __init__(self, start: int, end: int, line: int, name: str, lhs: Optional[Graph]=None, rhs: Optional[Graph]=None):
        Part.__init__(self, start, end, line, name)
        self.lhs = lhs
        self.rhs = rhs

class RulePart(TwoGraphPart):
    rule: Rule
    def __init__(self, start: int, end: int, line: int, rule: Rule):
        TwoGraphPart.__init__(self, start, end, line, rule.name, rule.lhs, rule.rhs)
        self.rule = rule

class TheoremPart(TwoGraphPart):
    sequence: int
    formula: Rule
    def __init__(self,
                 start: int,
                 end: int,
                 line: int,
                 formula: Rule,
                 sequence: int):
        TwoGraphPart.__init__(self, start, end, line, formula.name, formula.lhs, formula.rhs)
        self.sequence = sequence
        self.formula = formula

class ProofStepPart(TwoGraphPart):
    sequence: int
    proof_state: Optional[ProofState]
    def __init__(self,
                 start: int,
                 end: int,
                 line: int,
                 name: str,
                 sequence: int,
                 lhs: Optional[Graph]=None,
                 rhs: Optional[Graph]=None):
        TwoGraphPart.__init__(self, start, end, line, name, lhs, rhs)
        self.proof_state = None
        self.sequence = sequence

class ProofStartPart(ProofStepPart): pass
class ProofQedPart(ProofStepPart): pass

class ApplyTacticPart(ProofStepPart):
    tactic: str
    tactic_args: List[str]
    def __init__(self,
                 start: int,
                 end: int,
                 line: int,
                 name: str,
                 sequence: int,
                 tactic: str='',
                 tactic_args: Optional[List[str]] = None):
        ProofStepPart.__init__(self, start, end, line, name, sequence)
        self.tactic = tactic
        self.tactic_args = [] if tactic_args is None else tactic_args

class RewritePart(ProofStepPart):
    tactic: str
    tactic_args: List[str]
    side: Optional[Literal['LHS', 'RHS']]
    stub: bool
    term_pos: Tuple[int,int]
    def __init__(self,
                 start: int,
                 end: int,
                 line: int,
                 name: str,
                 sequence: int,
                 term_pos: Tuple[int,int]=(0,0),
                 side: Optional[Literal['LHS', 'RHS']]=None,
                 lhs: Optional[Graph]=None,
                 rhs: Optional[Graph]=None,
                 tactic: str='',
                 tactic_args: Optional[List[str]] = None,
                 stub: bool = False):
        ProofStepPart.__init__(self, start, end, line, name, sequence, lhs=lhs, rhs=rhs)
        self.term_pos = term_pos
        self.tactic = tactic
        self.tactic_args = [] if tactic_args is None else tactic_args
        self.side = side
        self.stub = stub

class ImportPart(Part): pass


