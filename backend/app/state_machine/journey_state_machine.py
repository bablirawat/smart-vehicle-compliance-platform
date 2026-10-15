from typing import Dict, Set, Tuple
from app.models.journeys import JourneyState

class InvalidStateTransitionException(Exception):
    def __init__(self, current_state: str, target_state: str, reason: str = None):
        self.current_state = current_state
        self.target_state = target_state
        self.reason = reason or f"Cannot transition journey from '{current_state}' to '{target_state}'."
        super().__init__(self.reason)

class JourneyStateMachine:
    # Map of allowed current_state -> Set of allowed target_states
    ALLOWED_TRANSITIONS: Dict[JourneyState, Set[JourneyState]] = {
        JourneyState.ENTERED: {JourneyState.IDENTIFIED, JourneyState.HOLD},
        JourneyState.IDENTIFIED: {JourneyState.VERIFIED, JourneyState.HOLD},
        JourneyState.VERIFIED: {JourneyState.ELIGIBLE, JourneyState.NOT_ELIGIBLE, JourneyState.HOLD},
        JourneyState.ELIGIBLE: {JourneyState.QUEUED, JourneyState.HOLD},
        JourneyState.NOT_ELIGIBLE: {JourneyState.HOLD},
        JourneyState.QUEUED: {JourneyState.BAY_ASSIGNED, JourneyState.HOLD},
        JourneyState.BAY_ASSIGNED: {JourneyState.IN_SERVICE, JourneyState.QUEUED, JourneyState.HOLD},
        JourneyState.IN_SERVICE: {JourneyState.SERVICE_COMPLETED, JourneyState.HOLD},
        JourneyState.SERVICE_COMPLETED: {JourneyState.EXITED},
        JourneyState.HOLD: {JourneyState.QUEUED, JourneyState.ELIGIBLE, JourneyState.EXITED},
        JourneyState.EXITED: set() # Terminal state
    }

    @classmethod
    def validate_transition(cls, current_state: JourneyState, target_state: JourneyState, is_override: bool = False) -> bool:
        if current_state == target_state:
            return True # Idempotent transition request
        
        allowed = cls.ALLOWED_TRANSITIONS.get(current_state, set())
        
        # If operator override is enabled, allow moving out of HOLD or any state to HOLD
        if is_override:
            if target_state == JourneyState.HOLD or current_state == JourneyState.HOLD:
                return True

        if target_state not in allowed:
            raise InvalidStateTransitionException(
                current_state=current_state.value if isinstance(current_state, JourneyState) else str(current_state),
                target_state=target_state.value if isinstance(target_state, JourneyState) else str(target_state)
            )
        return True

state_machine = JourneyStateMachine()
