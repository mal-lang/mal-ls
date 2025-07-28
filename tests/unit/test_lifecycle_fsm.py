import pytest

from malls.lsp.fsm import STATES, LifecycleFSM, State


@pytest.fixture
def fsm() -> LifecycleFSM:
    return LifecycleFSM()


def test_initial_state_is_start(fsm: LifecycleFSM):
    assert fsm.current_state == State.START


# Test that all transitions that should be valid are valid
acceptance_parameters = {
    State.START: {State.INITIALIZE},
    State.INITIALIZE: {State.INITIALIZED},
    # Should be fuzzable
    State.INITIALIZED: {State.SHUTDOWN, "some_lsp_method"},
    State.SHUTDOWN: {State.EXIT},
}
acceptance_parameters = [
    (start_state, accepted_state)
    for start_state in acceptance_parameters
    for accepted_state in sorted(acceptance_parameters[start_state])
]


@pytest.mark.parametrize("start_state,symbol_state", acceptance_parameters)
def test_state_may_accept(start_state: State, symbol_state: State):
    fsm = LifecycleFSM(start_state)
    assert fsm.may_accept(symbol_state)


# Test that the FSM properly rejects invalid transitions or symbols
rejection_parameters = {
    State.START: set(STATES) - {State.INITIALIZE} | {"some_lsp_method"},
    State.INITIALIZE: set(STATES) - {State.INITIALIZED} | {"some_lsp_method"},
    State.INITIALIZED: {State.START, State.INITIALIZE, State.EXIT},
    State.SHUTDOWN: set(STATES) - {State.EXIT} | {"some_lsp_method"},
    State.EXIT: set(STATES) | {"some_lsp_method"},
}

rejection_parameters = [
    ("fsm_" + start_state, rejected_state)
    for start_state in rejection_parameters
    for rejected_state in sorted(rejection_parameters[start_state])
]


@pytest.mark.parametrize("start_state,symbol_state", rejection_parameters)
def test_state_may_reject(start_state: State, symbol_state: State):
    fsm = LifecycleFSM(start_state)
    assert not fsm.may_accept(symbol_state)
