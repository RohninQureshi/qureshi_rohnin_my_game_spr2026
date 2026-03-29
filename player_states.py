
from state_machine import State


# Player state for standing still and waiting for movement input.
class PlayerIdleState(State):
    def __init__(self, player):
        # player reference is needed so the state can inspect movement flags and transition
        self.player = player

    def get_state_name(self):
        return "idle"

    def enter(self):
        self.player.walking = False
        self.player.sprinting = False

    def exit(self):
        pass

    def update(self):
        # idle changes to sprint or move as soon as the player starts moving
        if self.player.wants_to_sprint():
            self.player.state_machine.transition("sprint")
        elif self.player.wants_to_move():
            self.player.state_machine.transition("move")


# Player state for normal movement without sprinting.
class PlayerMoveState(State):
    def __init__(self, player):
        self.player = player

    def get_state_name(self):
        return "move"

    def enter(self):
        self.player.walking = True
        self.player.sprinting = False

    def exit(self):
        pass

    def update(self):
        # move changes either to sprint if shift is active or back to idle if motion stops
        if self.player.wants_to_sprint():
            self.player.state_machine.transition("sprint")
        elif not self.player.wants_to_move():
            self.player.state_machine.transition("idle")


# Player state for faster movement while sprinting is active.
class PlayerSprintState(State):
    def __init__(self, player):
        self.player = player

    def get_state_name(self):
        return "sprint"

    def enter(self):
        self.player.start_sprint()

    def exit(self):
        self.player.stop_sprint()

    def update(self):
        # sprint drops to idle if movement stops, otherwise falls back to move when sprint ends
        if not self.player.wants_to_move():
            self.player.state_machine.transition("idle")
        elif not self.player.should_keep_sprinting():
            self.player.state_machine.transition("move")
