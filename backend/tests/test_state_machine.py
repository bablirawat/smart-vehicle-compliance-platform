import pytest
from app.models.journeys import JourneyState
from app.state_machine.journey_state_machine import JourneyStateMachine, InvalidStateTransitionException

def test_valid_state_transitions():
    assert JourneyStateMachine.validate_transition(JourneyState.ENTERED, JourneyState.IDENTIFIED) is True
    assert JourneyStateMachine.validate_transition(JourneyState.IDENTIFIED, JourneyState.VERIFIED) is True
    assert JourneyStateMachine.validate_transition(JourneyState.VERIFIED, JourneyState.ELIGIBLE) is True
    assert JourneyStateMachine.validate_transition(JourneyState.ELIGIBLE, JourneyState.QUEUED) is True
    assert JourneyStateMachine.validate_transition(JourneyState.QUEUED, JourneyState.BAY_ASSIGNED) is True
    assert JourneyStateMachine.validate_transition(JourneyState.BAY_ASSIGNED, JourneyState.IN_SERVICE) is True
    assert JourneyStateMachine.validate_transition(JourneyState.IN_SERVICE, JourneyState.SERVICE_COMPLETED) is True
    assert JourneyStateMachine.validate_transition(JourneyState.SERVICE_COMPLETED, JourneyState.EXITED) is True

def test_invalid_state_transitions():
    # Cannot jump directly from ENTERED to IN_SERVICE
    with pytest.raises(InvalidStateTransitionException):
        JourneyStateMachine.validate_transition(JourneyState.ENTERED, JourneyState.IN_SERVICE)

    # Cannot jump directly from QUEUED to EXITED
    with pytest.raises(InvalidStateTransitionException):
        JourneyStateMachine.validate_transition(JourneyState.QUEUED, JourneyState.EXITED)

    # Terminal EXITED state cannot transition anywhere
    with pytest.raises(InvalidStateTransitionException):
        JourneyStateMachine.validate_transition(JourneyState.EXITED, JourneyState.IN_SERVICE)
