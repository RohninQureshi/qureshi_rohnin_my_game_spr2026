
from state_machine import State


class PlayerIdleState(State):
    def __init__(self, player):
        # player reference is needed so the state can inspect movement flags and transition
        self.player = player

    def get_state_name(self):
        return "idle"

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self):
        # idle changes to sprint or move as soon as the player starts moving
        if self.player.sprinting and self.player.walking:
            self.player.state_machine.transition("sprint")
        elif self.player.walking:
            self.player.state_machine.transition("move")


class PlayerMoveState(State):
    def __init__(self, player):
        self.player = player

    def get_state_name(self):
        return "move"

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self):
        # move changes either to sprint if shift is active or back to idle if motion stops
        if self.player.sprinting and self.player.walking:
            self.player.state_machine.transition("sprint")
        elif not self.player.walking:
            self.player.state_machine.transition("idle")


class PlayerSprintState(State):
    def __init__(self, player):
        self.player = player

    def get_state_name(self):
        return "sprint"

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self):
        # sprint drops to idle if movement stops, otherwise falls back to move when sprint ends
        if not self.player.walking:
            self.player.state_machine.transition("idle")
        elif not self.player.sprinting:
            self.player.state_machine.transition("move")
