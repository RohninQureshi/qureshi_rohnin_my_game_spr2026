is_log_enabled: bool = False

# Parent class for all states so they share the same interface.
class State:
    # Base state class; concrete states override whichever methods they need.
    def enter(self):
        # enter is called once when a state becomes active
        pass

    def exit(self):
        # exit is called once right before the machine switches away from a state
        pass

    def update(self):
        # update is called every frame while the state remains active
        pass

    def get_state_name(self):
        # concrete states return the string used to register them in the machine
        return ""

# Generic state machine that stores states and handles transitions between them.
class StateMachine:
    def __init__(self):
        # current_state stores whichever state object is active right now.
        self.current_state = None
        # states is a dictionary so states can be looked up by string name.
        self.states = {}

    def start_machine(self, init_states):
        # clear the dictionary so restarting the machine rebuilds state data fresh
        self.states = {}

        for state in init_states:
            # register each state by whatever string its get_state_name method returns
            self.states[state.get_state_name()] = state

        if not init_states:
            return

        # first item in the list becomes the starting state
        self.current_state = init_states[0]

        if is_log_enabled:
            print("starting state machine...")

        # run any setup code tied to entering the first state
        self.current_state.enter()

    def update(self):
        # every frame, delegate behavior to the active state
        if self.current_state is not None:
            # if no current state exists yet, update safely does nothing
            self.current_state.update()

    def transition(self, new_state_name):
        # tries to find the target state from the dictionary
        new_state = self.states.get(new_state_name)

        if new_state is None:
            if is_log_enabled:
                print("attempting to transition to non existent state:", new_state_name)
            return

        # ignore transitions to the same state so enter/exit does not rerun unnecessarily
        if new_state == self.current_state:
            return

        # leave the old state cleanly before switching to the new one
        if self.current_state is not None:
            self.current_state.exit()

        self.current_state = new_state
        # run setup code for the new active state
        self.current_state.enter()

        if is_log_enabled:
            print("transitioned to", self.current_state.get_state_name())
