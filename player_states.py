
from state_machine import State


class PlayerIdleState(State):
    def __init__(self, player):
        self.player = player

    def get_state_name(self):
        return "idle"

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self):
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
        if not self.player.walking:
            self.player.state_machine.transition("idle")
        elif not self.player.sprinting:
            self.player.state_machine.transition("move")
