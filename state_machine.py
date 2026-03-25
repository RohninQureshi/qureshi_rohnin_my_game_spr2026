is_log_enabled: bool = False


class State:
    def enter(self):
        pass

    def exit(self):
        pass

    def update(self):
        pass

    def get_state_name(self):
        return ""


class StateMachine:
    def __init__(self):
        self.current_state = None
        self.states = {}

    def start_machine(self, init_states):
        self.states = {}

        for state in init_states:
            self.states[state.get_state_name()] = state

        if not init_states:
            return

        self.current_state = init_states[0]

        if is_log_enabled:
            print("starting state machine...")

        self.current_state.enter()

    def update(self):
        if self.current_state is not None:
            self.current_state.update()

    def transition(self, new_state_name):
        new_state = self.states.get(new_state_name)

        if new_state is None:
            if is_log_enabled:
                print("attempting to transition to non existent state:", new_state_name)
            return

        if new_state == self.current_state:
            return

        if self.current_state is not None:
            self.current_state.exit()

        self.current_state = new_state
        self.current_state.enter()

        if is_log_enabled:
            print("transitioned to", self.current_state.get_state_name())
