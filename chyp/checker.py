from typing import Callable, Optional

from .rule import Rule
from .state import ProofQedPart, ProofStartPart, State, Part, TheoremPart, ApplyTacticPart, RewritePart
from .proofstate import ProofState, Goal
from .tactic import Tactic
from .tactic.simptac import SimpTac
from .tactic.ruletac import RuleTac

def get_tactic(proof_state: ProofState, name: str, args: list[str]) -> Tactic:
    if name == 'rule':
        return RuleTac(proof_state, args)
    elif name == 'simp':
        return SimpTac(proof_state, args)
    elif name == 'refl':
        return Tactic(proof_state, args)
    else:
        proof_state.error('Unknown tactic: ' + name)
        return Tactic(proof_state, args)

def next_rhs(state: State, part: RewritePart, term: str) -> Optional[str]:
    if part.lhs:
        # not in a proof, make a fake proof state to send to the tactic
        proof_state = ProofState(state, part.sequence, [Goal(Rule(part.lhs, part.lhs))])
    else:
        # in a proof, take a copy of the prior proof state
        p = state.parts[part.index-1] if part.index > 0 else None
        if p and isinstance(p, RewritePart) and p.proof_state:
            proof_state = p.proof_state.copy()
        else:
            proof_state = None

    if proof_state:
        t = get_tactic(proof_state, part.tactic, part.tactic_args)
        return t.next_rhs(term)
    else:
        return None


def check(state: State, get_revision: Callable[[],int]) -> None:
    current_proof_state = None
    current_theorem_part = None
    for p in state.parts:
        if state.revision != get_revision(): break
        if p.status != Part.UNCHECKED: continue

        if isinstance(p, TheoremPart):
            p.status = Part.CHECKING
            current_theorem_part = p

        elif isinstance(p, ProofStartPart):
            if not current_theorem_part:
                raise RuntimeError('Get proof without theorem')
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
            if current_proof_state:
                p.proof_state = current_proof_state.snapshot(p)
            elif p.lhs:
                rhs = p.rhs if p.rhs else p.lhs
                p.proof_state = ProofState(state,
                                           p.sequence,
                                           [Goal(Rule(p.lhs, rhs))])
                p.proof_state.line = p.line

            if p.proof_state:
                t = get_tactic(p.proof_state, p.tactic, p.tactic_args)
                p.status = Part.CHECKING

                if p.side and p.rhs:
                    if p.side == 'LHS': p.proof_state.replace_lhs(p.rhs)
                    else: p.proof_state.replace_rhs(p.rhs)

                num_goals = p.proof_state.num_goals()
                if t.run():
                    if p.proof_state.num_goals() < num_goals:
                        p.proof_state.try_close_goal()
                        p.status = Part.VALID
                    else:
                        p.status = Part.INVALID
                else:
                    p.status = Part.INVALID

                if current_proof_state:
                    current_proof_state = p.proof_state
            else:
                p.status = Part.INVALID
