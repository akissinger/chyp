from typing import Callable

from .state import State, Part, TheoremPart, ProofStepPart, ProofTacticPart, ProofRewritePart
from .proofstate import ProofState, Goal
from .tactic import Tactic
from .tactic.simptac import SimpTac
from .tactic.ruletac import RuleTac
from .tactic.rewritetac import RewriteTac

def check(state: State, get_revision: Callable[[],int]) -> None:
    current_proof_state = None
    current_theorem_part = None
    for p in state.parts:
        if state.revision != get_revision(): break
        if isinstance(p, TheoremPart) and p.status == Part.UNCHECKED:
            p.status = Part.CHECKING
            current_proof_state = ProofState(state, p.sequence, [Goal(p.formula)])
            current_theorem_part = p
        elif isinstance(p, ProofStepPart) and p.status == Part.UNCHECKED:
            if current_proof_state:
                p.layed_out = False
                p.proof_state = current_proof_state.snapshot(p)

                if isinstance(p, ProofTacticPart) or isinstance(p, ProofRewritePart):
                    t: Tactic
                    if p.tactic == 'rule':
                        t = RuleTac(p.proof_state, p.tactic_args)
                    elif p.tactic == 'simp':
                        t = SimpTac(p.proof_state, p.tactic_args)
                    else:
                        t = Tactic(p.proof_state, p.tactic_args)
                    p.status = Part.CHECKING

                    if isinstance(p, ProofRewritePart):
                        num_goals = p.proof_state.num_goals()
                        RewriteTac(p.proof_state, [p.side], p.term).run()
                        if t.run():
                            if p.proof_state.num_goals() == num_goals:
                                p.proof_state.try_close_goal()
                                p.status = Part.VALID
                            else:
                                p.status = Part.INVALID
                    else:
                        p.status = Part.VALID if t.run() else Part.INVALID

                elif p.qed:
                    st = Part.VALID if current_proof_state and len(current_proof_state.goals) == 0 else Part.INVALID
                    p.status = st
                    if current_theorem_part:
                        current_theorem_part.status = st
                else:
                    p.status = Part.VALID

                current_proof_state = p.proof_state
