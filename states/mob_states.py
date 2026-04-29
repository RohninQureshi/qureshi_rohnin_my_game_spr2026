from state_machine import State


# Mob state used when the player is outside detection range.
class MobPassiveState(State):
    def __init__(self, mob):
        # keep a reference to the mob so the state can change its behavior flags
        self.mob = mob

    def get_state_name(self):
        # passive means the mob has not detected the player yet
        return "passive"

    def enter(self):
        # black color shows the player that this mob is not actively targeting them
        self.mob.targeting_player = False
        self.mob.set_base_color(self.mob.passive_color)

    def exit(self):
        # no cleanup is needed because the next state sets its own flags and color
        pass

    def update(self):
        # contact has priority over detection range because touching the player means attacking
        if self.mob.player_touching():
            self.mob.state_machine.transition("attacking")
            return

        # if the player comes close enough, swap into the targeting state
        if self.mob.player_in_detection_radius():
            self.mob.state_machine.transition("targeting")


# Mob state used when the player is inside detection range.
class MobTargetingState(State):
    def __init__(self, mob):
        # keep a reference to the mob so the state can steer it toward the player
        self.mob = mob

    def get_state_name(self):
        # targeting means the mob has detected the player and is actively chasing
        return "targeting"

    def enter(self):
        # red color shows the player that this mob is actively locked onto them
        self.mob.targeting_player = True
        self.mob.set_base_color(self.mob.targeting_color)

    def exit(self):
        # no cleanup is needed because passive state restores passive behavior
        pass

    def update(self):
        # direct contact upgrades targeting into the attack state
        if self.mob.player_touching():
            self.mob.state_machine.transition("attacking")
            return

        # if the player leaves range, go back to passive patrol behavior
        if not self.mob.player_in_detection_radius():
            self.mob.state_machine.transition("passive")
            return

        # while targeting, face and move toward the player's current horizontal position
        self.mob.target_player()


# Mob state used while the mob is physically touching the player.
class MobAttackingState(State):
    def __init__(self, mob):
        # keep a reference to the mob so the state can stop movement and trigger attack visuals
        self.mob = mob

    def get_state_name(self):
        # attacking means the mob is in contact with the player
        return "attacking"

    def enter(self):
        # attacking mobs stop chasing and flash pink while contact damage is handled by game_states.py
        self.mob.targeting_player = True
        self.mob.attacking_player = True
        self.mob.move_dir = 0
        self.mob.set_base_color(self.mob.targeting_color)

    def exit(self):
        # clear the attack flag so normal passive/targeting colors come back after contact ends
        self.mob.attacking_player = False

    def update(self):
        # stay in attack while still touching the player
        self.mob.move_dir = 0
        if self.mob.player_touching():
            return

        # after contact breaks, return to chase if still close enough, otherwise go passive
        if self.mob.player_in_detection_radius():
            self.mob.state_machine.transition("targeting")
        else:
            self.mob.state_machine.transition("passive")
