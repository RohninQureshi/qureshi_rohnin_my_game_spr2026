import pygame as pg

from settings import *
from state_machine import State


                
    class WardenShootState(State):
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

class WardenVulnerabilityState(State):
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
        # next_attack is what lets the boss rotate patterns without one giant if-chain in SentinelBoss.update()
        if pg.time.get_ticks() - self.boss.mode_start_time > 1000:
            if self.boss.next_attack == "shoot":
                self.boss.state_machine.transition("shoot")
            elif self.boss.next_attack == "charge":
                self.boss.state_machine.transition("charge_warn")
            else:
                self.boss.state_machine.transition("ground_pound_lock")
