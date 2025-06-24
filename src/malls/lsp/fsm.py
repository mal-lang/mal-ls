from enum import StrEnum


class LifecycleState(StrEnum):
    START = "start"
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    SHUTDOWN = "shutdown"
    EXIT = "exit"


State = LifecycleState


STATES = list(State)


class LifecycleFSM:
    def __init__(self, start: State = State.START):
        self._states = set(STATES)
        self.current_state = start

    @property
    def state(self) -> State:
        return self.current_state

    def may_accept(self, symbol: State | str) -> bool:
        """
        Check if there exists a valid transition from the current state using the given symbol as
        input.
        """
        match (self.current_state, symbol):
            # T(start, "initalize") = initalize
            case (State.START, State.INITIALIZE):
                pass
            # T(initalize, "initalized") = initalized
            case (State.INITIALIZE, State.INITIALIZED):
                pass
            # T(initalize, "shutdown") = shutdown
            case (State.INITIALIZED, State.SHUTDOWN):
                pass
            # T(shutdown, "exit") = exit
            case (State.SHUTDOWN, State.EXIT):
                pass
            # T(initalized, U \ {"shutdown"}) = initalized
            case (State.INITIALIZED, call) if call not in self._states:
                pass
            # Invalid
            case _:
                return False
        return True

    def accepts(self, symbol: State | str):
        """
        Transitions the FSM into the respective state based on input symbol.

        From `State.INITIALIZED` anything is allowed as transition as long
        as it doesn't clash with the other transitions/states.
        """
        if self.may_accept(symbol):
            # abstract anything into method call unless its an existing state
            self.current_state = symbol if symbol in self._states else State.INITIALIZED
        else:
            raise KeyError(f"Lifecycle FSM does not accept {symbol} in the current state")

    def __repr__(self):
        return f"LifecycleFSM({self.current_state})"
