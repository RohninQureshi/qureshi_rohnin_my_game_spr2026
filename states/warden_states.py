import pygame as pg

from settings import *
from state_machine import State


# Wait gives the player a brief reset before Warden starts the next pressure cycle.
class WardenWaitState(State):
    def __init__(self, boss):
        self.boss = boss

    def get_state_name(self):
        return "wait"

    def enter(self):
        self.boss.set_mode("wait")
        self.boss.vel.x = 0

    def update(self):
        if pg.time.get_ticks() - self.boss.mode_start_time > WARDEN_WAIT_TIME:
            self.boss.state_machine.transition("summon")


# Summon state creates mobs and keeps Warden shielded until the player clears them.
class WardenSummonState(State):
    def __init__(self, boss):
        self.boss = boss

    def get_state_name(self):
        return "summon"

    def enter(self):
        self.boss.set_mode("summon")
        self.boss.summon_mobs()

    def update(self):
        # The player must handle adds first, which makes this boss test target priority.
        if not self.boss.active_summons_alive():
            self.boss.state_machine.transition("shoot")


# Shoot state adds pressure after summons are cleared, then opens the damage window.
class WardenShootState(State):
    def __init__(self, boss):
        self.boss = boss

    def get_state_name(self):
        return "shoot"

    def enter(self):
        self.boss.set_mode("shoot")
        self.boss.vel.x = 0

    def update(self):
        if self.boss.shot_cd.ready():
            self.boss.shot_cd.start()
            self.boss.shoot_at_player()

        if pg.time.get_ticks() - self.boss.mode_start_time > WARDEN_SHOOT_TIME:
            self.boss.state_machine.transition("vulnerable")


# Vulnerable state is the reward window where Warden can actually take damage.
class WardenVulnerableState(State):
    def __init__(self, boss):
        self.boss = boss

    def get_state_name(self):
        return "vulnerable"

    def enter(self):
        self.boss.set_mode("vulnerable")

    def update(self):
        if pg.time.get_ticks() - self.boss.mode_start_time > WARDEN_VULNERABLE_TIME:
            self.boss.state_machine.transition("recover")


# Recover closes the vulnerability window and prepares the next summon cycle.
class WardenRecoverState(State):
    def __init__(self, boss):
        self.boss = boss

    def get_state_name(self):
        return "recover"

    def enter(self):
        self.boss.set_mode("recover")

    def update(self):
        if pg.time.get_ticks() - self.boss.mode_start_time > WARDEN_RECOVER_TIME:
            self.boss.state_machine.transition("wait")
