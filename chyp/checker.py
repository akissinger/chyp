from typing import Callable, Optional

from .rule import Rule
from .state import State
from .parts import Part, ProofStartPart, ProofQedPart, ProofStepPart, TheoremPart, ApplyTacticPart, RewritePart
from .proofstate import ProofState, Goal
from .tactic import get_tactic

def next_rhs(state: State, part: RewritePart, term: str) -> Optional[str]:
    if not part.lhs: return None

    # make a fake proof state to send to the tactic

    # set the goal equal to LHS = LHS
    g = Goal(Rule(part.lhs, part.lhs))

    # if we are inside a proof, set the assumptions equal to those of the top goal before the current
    # proof step
    if part.index > 0:
        prev_part = state.parts[part.index-1]
        if (isinstance(prev_part, ProofStepPart) and
            prev_part.proof_state and
            prev_part.proof_state.num_goals() > 0):
            g.assumptions = { n : a.copy() for n,a in prev_part.proof_state.goals[0].assumptions.items() }
    proof_state = ProofState(state, part.sequence, [g])
    t = get_tactic(proof_state, part.tactic, part.tactic_args)
    return t.next_rhs(term)


def check(state: State, get_revision: Optional[Callable[[],int]]=None) -> None:
    current_proof_state = None
    current_theorem_part = None
    for p in state.parts:
        if get_revision and state.revision != get_revision(): break

        if isinstance(p, TheoremPart):
            p.status = Part.CHECKING
            current_theorem_part = p

        elif isinstance(p, ProofStartPart):
            if not current_theorem_part:
                raise RuntimeError('Got proof without theorem')
            p.status = Part.VALID
            p.proof_state = ProofState(state,
                                       current_theorem_part.sequence,
                                       [Goal(current_theorem_part.formula)])
            current_proof_state = p.proof_state

        elif isinstance(p, ProofQedPart):
            if not current_theorem_part or not current_proof_state:
                raise RuntimeError('Get qed without theorem or proofstate')
            p.proof_state = current_proof_state.snapshot(p)
            st = Part.VALID if len(p.proof_state.goals) == 0 else Part.INVALID
            p.status = st
            current_theorem_part.status = st
            current_theorem_part = None
            current_proof_state = None

        elif isinstance(p, ApplyTacticPart):
            p.layed_out = False
            if not current_proof_state:
                raise RuntimeError('Could not get ProofState for "apply"')
            p.proof_state = current_proof_state.snapshot(p)
            p.status = Part.CHECKING
            t = get_tactic(p.proof_state, p.tactic, p.tactic_args)
            p.status = Part.VALID if t.run() else Part.INVALID
            current_proof_state = p.proof_state

        elif isinstance(p, RewritePart):
            p.layed_out = False
            proof_state = None
            if current_proof_state:
                proof_state = current_proof_state.snapshot(p)
                p.proof_state = proof_state
                if proof_state.num_goals() > 0:
                    if p.rhs_side == 'LHS':
                        p.rhs = proof_state.lhs()
                    elif p.rhs_side == 'RHS':
                        p.rhs = proof_state.rhs()

                    if p.lhs_side == 'LHS':
                        p.lhs = proof_state.lhs()
                        if p.rhs: proof_state.replace_lhs(p.rhs)
                    elif p.lhs_side == 'RHS':
                        p.lhs = proof_state.rhs()
                        if p.rhs: proof_state.replace_rhs(p.rhs)
            elif p.lhs:
                if not p.rhs: p.rhs = p.lhs
                proof_state = ProofState(state,
                                         p.sequence,
                                         [Goal(Rule(p.lhs, p.rhs))])
                proof_state.line = p.line

            if proof_state:
                t = get_tactic(proof_state, p.tactic, p.tactic_args)
                p.status = Part.CHECKING

                num_goals = proof_state.num_goals()
                if t.run():
                    if proof_state.num_goals() < num_goals:
                        proof_state.try_close_goal()
                        p.status = Part.VALID
                    else:
                        p.status = Part.INVALID
                else:
                    p.status = Part.INVALID

                if current_proof_state:
                    current_proof_state = p.proof_state
            else:
                p.status = Part.INVALID
