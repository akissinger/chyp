from typing import Callable

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
            if p.stub: continue
            p.layed_out = False
            if p.lhs and p.rhs:
                p.proof_state = ProofState(state,
                                           p.sequence,
                                           [Goal(Rule(p.lhs, p.rhs))])
                p.proof_state.line = p.line
            elif current_proof_state:
                p.proof_state = current_proof_state.snapshot(p)

            if not p.proof_state:
                raise RuntimeError('Could not get ProofState for "rewrite"')

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
