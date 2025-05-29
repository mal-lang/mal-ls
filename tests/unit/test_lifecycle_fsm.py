import pytest

from malls.lsp.fsm import STATES, LifecycleFSM, State


@pytest.fixture
def states() -> list[str]:
    return STATES

@pytest.fixture
def fsm() -> LifecycleFSM:
    return LifecycleFSM()

# TODO: revamp this by exacting the fixture definer in root conftest.py
@pytest.fixture
def fsm_start(fsm: LifecycleFSM) -> LifecycleFSM:
    fsm.current_state = State.START
    return fsm

@pytest.fixture
def fsm_initialize(fsm: LifecycleFSM) -> LifecycleFSM:
    fsm.current_state = State.INITIALIZE
    return fsm

@pytest.fixture
def fsm_initialized(fsm: LifecycleFSM) -> LifecycleFSM:
    fsm.current_state = State.INITIALIZED
    return fsm

@pytest.fixture
def fsm_shutdown(fsm: LifecycleFSM) -> LifecycleFSM:
    fsm.current_state = State.SHUTDOWN
    return fsm

@pytest.fixture
def fsm_exit(fsm: LifecycleFSM) -> LifecycleFSM:
    fsm.current_state = State.EXIT
    return fsm


def test_initial_state_is_start(fsm: LifecycleFSM):
    assert fsm.current_state == State.START


# Test that all transitions that should be valid are valid
acceptance_parameters = {
    State.START: {State.INITIALIZE},
    State.INITIALIZE: {State.INITIALIZED},
    # Should be fuzzable
    State.INITIALIZED: {State.SHUTDOWN, "some_lsp_method"},
    State.SHUTDOWN: {State.EXIT}
}
acceptance_parameters  = [
        ("fsm_" + start_state, accepted_state) \
        for start_state in acceptance_parameters \
        for accepted_state in sorted(acceptance_parameters[start_state])
]

@pytest.mark.parametrize("fsm_,state", acceptance_parameters)
def test_state_may_accept(fsm_: str, state: State, request: pytest.FixtureRequest):
    fsm: LifecycleFSM = request.getfixturevalue(fsm_)
    assert fsm.may_accept(state)


# Test that the FSM properly rejects invalid transitions or symbols
rejection_parameters = {
    State.START: set(STATES) - {State.INITIALIZE} | {"some_lsp_method"},
    State.INITIALIZE: set(STATES) - {State.INITIALIZED} | {"some_lsp_method"},
    State.INITIALIZED: {State.START, State.INITIALIZE, State.EXIT},
    State.SHUTDOWN: set(STATES) - {State.EXIT} | {"some_lsp_method"},
    State.EXIT: set(STATES) | {"some_lsp_method"}
}

rejection_parameters = [
        ("fsm_" + start_state, rejected_state) \
        for start_state in rejection_parameters \
        for rejected_state in sorted(rejection_parameters[start_state])
]

@pytest.mark.parametrize("fsm_,state", rejection_parameters)
def test_state_may_reject(fsm_: str, state: State, request: pytest.FixtureRequest):
    fsm: LifecycleFSM = request.getfixturevalue(fsm_)
    assert not fsm.may_accept(state)
