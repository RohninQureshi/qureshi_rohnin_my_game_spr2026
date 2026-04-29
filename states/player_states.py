from state_machine import State


# Player state for standing still and waiting for movement input.
class PlayerIdleState(State):
    def __init__(self, player):
        # player reference is needed so the state can inspect movement flags and transition
        self.player = player

    def get_state_name(self):
        # returns the string key used by the state machine dictionary
        return "idle"

    def enter(self):
        # idle clears movement flags so standing animation can play immediately
        self.player.walking = False
        self.player.sprinting = False

    def exit(self):
        # idle has no cleanup work because it does not start timers or effects
        pass

    def update(self):
        # dash has the highest priority because it is a burst action, not a held movement mode
        if self.player.wants_to_dash():
            self.player.state_machine.transition("dash")
        elif self.player.wants_to_sprint():
            self.player.state_machine.transition("sprint")
        elif self.player.wants_to_move():
            self.player.state_machine.transition("move")


# Player state for normal movement without sprinting.
class PlayerMoveState(State):
    def __init__(self, player):
        self.player = player

    def get_state_name(self):
        # the move state is used for normal horizontal travel without sprint speed
        return "move"

    def enter(self):
        # entering move enables walking visuals but leaves sprint off
        self.player.walking = True
        self.player.sprinting = False

    def exit(self):
        # move also has no special cleanup when another state takes over
        pass

    def update(self):
        # dash can interrupt normal movement immediately because it is a dodge input
        if self.player.wants_to_dash():
            self.player.state_machine.transition("dash")
        elif self.player.wants_to_sprint():
            self.player.state_machine.transition("sprint")
        elif not self.player.wants_to_move():
            self.player.state_machine.transition("idle")


# Player state for faster movement while sprinting is active.
class PlayerSprintState(State):
    def __init__(self, player):
        self.player = player

    def get_state_name(self):
        # sprint has its own state name so the player FSM can transition cleanly into faster movement
        return "sprint"

    def enter(self):
        # entering sprint delegates to the player helper so timing starts in one shared place
        self.player.start_sprint()

    def exit(self):
        # leaving sprint always routes through stop_sprint so cooldown logic stays centralized
        self.player.stop_sprint()

    def update(self):
        # dash can interrupt sprint because it is a stronger burst move with its own cooldown
        if self.player.wants_to_dash():
            self.player.state_machine.transition("dash")
            return

        # keep walking synced to live input so a brief turn-around pause does not cancel sprint itself
        self.player.walking = self.player.wants_to_move()
        # sprint now ends only when its timer expires or input is released
        if not self.player.should_keep_sprinting():
            if self.player.wants_to_move():
                self.player.state_machine.transition("move")
            else:
                self.player.state_machine.transition("idle")


# Player state for a short horizontal dodge burst.
class PlayerDashState(State):
    def __init__(self, player):
        self.player = player

    def get_state_name(self):
        # dash has its own state so the burst can temporarily override walk and sprint logic
        return "dash"

    def enter(self):
        # entering dash delegates setup to Player so timing and direction stay centralized
        self.player.start_dash()

    def exit(self):
        # leaving dash routes through one helper so cleanup stays in one place
        self.player.stop_dash()

    def update(self):
        # dash lasts only for its configured burst duration
        if not self.player.should_keep_dashing():
            if self.player.wants_to_sprint():
                self.player.state_machine.transition("sprint")
            elif self.player.wants_to_move():
                self.player.state_machine.transition("move")
            else:
                self.player.state_machine.transition("idle")
