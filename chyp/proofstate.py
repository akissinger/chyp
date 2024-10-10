from typing import Dict, List, Optional
from .rule import Rule

class Goal:
    rule: Rule
    assumptions: Dict[str, Rule]
    def __init__(self, rule: Rule, assumptions: Optional[Dict[str, Rule]]):
        self.rule = rule
        self.assumptions = assumptions if assumptions else dict()

class ProofState:
    def __init__(self, goals: Optional[List[Goal]] = None):
        self.goals = goals if goals else []