import pygame as pg

from settings import *
from state_machine import State


# Wait state gives the player a short pause before the Sentinel starts its next pattern.
class SentinelWaitState(State):
    def __init__(self, boss):
        # keep a reference to the boss so the state can control its timing and transitions
        self.boss = boss

    def get_state_name(self):
        # wait is the neutral idle phase between attacks
        return "wait"

    def enter(self):
        # entering wait resets the visual mode and stops horizontal motion
        self.boss.set_mode("wait")
        self.boss.vel.x = 0

    def update(self):
        # after a short breather, switch to whichever pattern was queued previously
        if pg.time.get_ticks() - self.boss.mode_start_time > 1000:
            if self.boss.next_attack == "shoot":
                self.boss.state_machine.transition("shoot")
            else:
                self.boss.state_machine.transition("charge_warn")


# Shoot state fires aimed projectiles at the player for a brief burst.
class SentinelShootState(State):
    def __init__(self, boss):
        # keep a reference to the boss so the state can fire projectiles
        self.boss = boss

    def get_state_name(self):
        # shoot means the boss is using its ranged attack pattern
        return "shoot"

    def enter(self):
        # entering shoot refreshes timing while keeping the boss at its current arena position
        self.boss.set_mode("shoot")
        self.boss.vel.x = 0

    def update(self):
        # the cooldown gates each projectile so this burst remains readable
        if self.boss.shot_cd.ready():
            self.boss.shot_cd.start()
            self.boss.shoot_at_player()

        # after the burst, queue the charge pattern and move into recovery
        if pg.time.get_ticks() - self.boss.mode_start_time > 1800:
            self.boss.next_attack = "charge"
            self.boss.state_machine.transition("recover")


# Charge warning lifts the boss upward before the dash begins.
class SentinelChargeWarnState(State):
    def __init__(self, boss):
        # keep a reference to the boss so the state can move it into charge position
        self.boss = boss

    def get_state_name(self):
        # charge_warn is the telegraph phase before the dash attack
        return "charge_warn"

    def enter(self):
        # entering warning snaps the boss back to the right-side starting point
        self.boss.set_mode("charge_warn")

    def update(self):
        # raise the boss over time so the player can see the charge coming
        now = pg.time.get_ticks()
        rise_progress = min(1, (now - self.boss.mode_start_time) / 900)
        self.boss.vel.x = 0
        self.boss.pos.y = self.boss.spawn_y - SENTINEL_CHARGE_HEIGHT * rise_progress

        # once the warning finishes, begin the leftward charge
        if now - self.boss.mode_start_time > 900:
            self.boss.state_machine.transition("charge")


# Charge state dashes quickly from right to left across most of the arena.
class SentinelChargeState(State):
    def __init__(self, boss):
        # keep a reference to the boss so the state can move it each frame
        self.boss = boss

    def get_state_name(self):
        # charge is the active dash attack
        return "charge"

    def enter(self):
        # entering charge moves the boss to dash height and switches to danger coloring
        self.boss.set_mode("charge")

    def update(self):
        # drive the boss left until it reaches its target distance or the left arena bound
        self.boss.vel.x = -SENTINEL_CHARGE_SPEED
        self.boss.pos.x += self.boss.vel.x * self.boss.game.dt

        if self.boss.pos.x <= self.boss.charge_target_x or self.boss.pos.x <= self.boss.left_bound:
            self.boss.next_attack = "shoot"
            self.boss.state_machine.transition("recover")


# Recover state gives the player a safer window between attack patterns.
class SentinelRecoverState(State):
    def __init__(self, boss):
        # keep a reference to the boss so the state can reset its starting position
        self.boss = boss

    def get_state_name(self):
        # recover is the post-attack cooldown window
        return "recover"

    def enter(self):
        # entering recovery changes the boss color and cancels dash movement
        self.boss.set_mode("recover")
        self.boss.vel.x = 0

    def update(self):
        # once recovery ends, snap the boss back to the right and return to wait
        if pg.time.get_ticks() - self.boss.mode_start_time > 1000:
            self.boss.pos.x = self.boss.spawn_x
            self.boss.pos.y = self.boss.spawn_y
            self.boss.state_machine.transition("wait")
