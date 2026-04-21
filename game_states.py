import pygame as pg
from settings import *
from state_machine import State


# State used while the game world is actively running and updating.
class GamePlayingState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # this key is how the main state machine refers to the active gameplay state
        return "playing"

    def enter(self):
        # marks the game as actively running gameplay
        self.game.playing = True

    def exit(self):
        # playing does not need teardown here because pause / win states handle their own setup
        pass

    def update(self):
        # only while playing do we update sprites and the camera
        self.game.all_sprites.update()
        # afterimages are visual-only, so they update outside the collision sprite groups
        self.game.all_afterimages.update()
        if self.game.camera is not None:
            # camera follows the player only during active gameplay
            self.game.camera.update(self.game.player)

        # player projectiles now deal damage to mobs instead of deleting them directly
        # projectiles still disappear on hit so one shot cannot pierce through several enemies
        mob_projectile_hits = pg.sprite.groupcollide(self.game.all_mobs, self.game.all_projectiles, False, True)
        for mob, projectiles in mob_projectile_hits.items():
            # damage stacks if several projectiles hit the same mob during the same frame
            damage = PLAYER_PROJECTILE_MOB_DAMAGE * len(projectiles)
            mob.take_damage(damage)
            self.game.add_damage_number(mob.rect.center, damage, YELLOW)
            self.game.spawn_hit_particles(mob.rect.center, YELLOW, 8)

        # player projectiles damage bosses instead of instantly killing them
        boss_hits = pg.sprite.groupcollide(self.game.all_bosses, self.game.all_projectiles, False, True)
        for boss, projectiles in boss_hits.items():
            # multiply by hit count so several projectiles in one frame still all count
            damage = PLAYER_PROJECTILE_BOSS_DAMAGE * len(projectiles)
            boss.take_damage(damage)
            self.game.add_damage_number(boss.rect.center, damage, YELLOW)
            self.game.spawn_hit_particles(boss.rect.center, (255, 120, 0), 10)

        # touching a mob damages the player, but a cooldown prevents instant health deletion
        mob_contact_hits = pg.sprite.spritecollide(self.game.player, self.game.all_mobs, False)
        if mob_contact_hits and self.game.mob_damage_cd.ready():
            # damage is subtracted from the player object so the existing health bar updates automatically
            self.game.player.health -= MOB_DAMAGE
            self.game.add_damage_number(self.game.player.rect.center, MOB_DAMAGE, RED)
            self.game.spawn_hit_particles(self.game.player.rect.center, RED, 6)
            # start the cooldown after a successful hit so contact damage happens in pulses
            self.game.mob_damage_cd.start()
            if self.game.player.health <= 0:
                # health reaching zero hands control to the game flow state machine
                self.game.state_machine.transition("game_over")

        # boss body contact uses its own cooldown so the player is not deleted instantly
        boss_body_hits = pg.sprite.spritecollide(self.game.player, self.game.all_bosses, False)
        if boss_body_hits and self.game.boss_damage_cd.ready():
            self.game.player.health -= SENTINEL_CONTACT_DAMAGE
            self.game.add_damage_number(self.game.player.rect.center, SENTINEL_CONTACT_DAMAGE, RED)
            self.game.spawn_hit_particles(self.game.player.rect.center, RED, 8)
            self.game.boss_damage_cd.start()

        # boss projectiles damage the player and disappear when they hit
        boss_projectile_hits = pg.sprite.spritecollide(self.game.player, self.game.all_boss_projectiles, True)
        if boss_projectile_hits:
            damage = SENTINEL_PROJECTILE_DAMAGE * len(boss_projectile_hits)
            self.game.player.health -= damage
            self.game.add_damage_number(self.game.player.rect.center, damage, RED)
            self.game.spawn_hit_particles(self.game.player.rect.center, RED, 8)

        if self.game.player.health <= 0:
            # any boss damage source can trigger game over once health reaches zero
            self.game.state_machine.transition("game_over")


# State used when gameplay is frozen but the game is still open.
class GamePausedState(State):
    def __init__(self, game):
        self.game = game

    def get_state_name(self):
        # paused is a distinct flow state so gameplay updates can be skipped cleanly
        return "paused"

    def enter(self):
        # paused stops gameplay updates but still allows UI and event handling
        self.game.playing = False

    def exit(self):
        # paused has no cleanup because resuming just transitions back to playing
        pass

    def update(self):
        # no gameplay update while paused
        pass


# State used for changing settings from the title screen or pause screen.
class GameSettingsState(State):
    def __init__(self, game):
        # stores the main Game object so settings can change shared game values
        self.game = game

    def get_state_name(self):
        # settings is the state machine key for the options menu
        return "settings"

    def enter(self):
        # settings freezes gameplay while the player changes options
        self.game.playing = False

    def exit(self):
        # settings changes are applied immediately, so there is no exit cleanup
        pass

    def update(self):
        # settings only responds to menu input handled in main events
        pass


# State used after the player loses and gameplay should stop.
class GameOverState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # game_over identifies the loss screen in the shared game state machine
        return "game_over"

    def enter(self):
        # game over also freezes gameplay so only restart / quit actions remain
        self.game.playing = False

    def exit(self):
        # no extra cleanup is needed when leaving the game over screen
        pass

    def update(self):
        # game over does not advance gameplay; it only waits for player input
        pass


# State used for the title / start screen before gameplay begins.
class GameStartState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # start is the title screen key used before gameplay begins
        return "start"

    def enter(self):
        # start screen waits for the player to begin the run
        self.game.playing = False

    def exit(self):
        # start screen also does not need teardown logic when Enter is pressed
        pass

    def update(self):
        # start screen also waits for input instead of updating gameplay
        pass
    
# Temporary transition state used to move the game from one level to the next.
class GameLevelClearState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # level_clear is a short transition state, not a long-lived gameplay screen
        return "level_clear"

    def enter(self):
        # entering level_clear immediately advances to the next level
        self.game.next_level()

    def exit(self):
        # this state finishes its work in enter, so exit remains empty
        pass

    def update(self):
        # level clear hands work off in enter, so update stays empty
        pass


# State used after the player beats the final level of the game.
class GameWonState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # game_won marks the final completion screen after the last level
        return "game_won"

    def enter(self):
        # win state freezes gameplay and shows the end screen
        self.game.playing = False

    def exit(self):
        # restart input handles the reset, so exit does not need to do anything special
        pass

    def update(self):
        # win state waits for restart input rather than updating gameplay
        pass
