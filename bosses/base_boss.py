import pygame as pg
from pygame.sprite import Sprite
from settings import *
from state_machine import StateMachine, State
vec = pg.math.Vector2


# Shared boss parent class that stores the common data every boss will need.
class BaseBoss(Sprite):
    def __init__(self, game, x, y, width, height, hit_rect, max_health, color, display_name):
        # every boss belongs to the main sprite group and the dedicated boss group
        self.groups = game.all_sprites, game.all_bosses
        Sprite.__init__(self, self.groups)

        # game is stored so the boss can access the player, map size, particles, and state machine
        self.game = game
        # image starts as a simple colored rectangle until real art exists
        self.image = pg.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        # hit_rect can be tuned separately from the visible image if needed later
        self.hit_rect = hit_rect.copy()
        # bosses use vector positions so movement remains delta-time based like the player and mobs
        self.pos = vec(x, y) * TILESIZE
        self.vel = vec(0, 0)

        # health and display name are shared by all future bosses and the shared HUD code
        self.health = max_health
        self.max_health = max_health
        self.display_name = display_name
        self.default_color = color
        self.hit_flash_color = (255, 120, 0)

        # these defaults let shared combat code read damage from any boss without boss-name checks.
        # Subclasses should replace these with their own values during __init__.
        self.contact_damage = 0
        self.contact_cooldown = 0
        self.projectile_damage = 0

        # hit_flash_time controls the short orange flash when the boss takes damage
        self.hit_flash_time = 0
        # each boss gets its own local state machine, just like the player and mobs do
        self.state_machine = StateMachine()

    def start_states(self, states):
        # helper keeps the "build a list and start the machine" pattern the same for every boss
        self.states: list[State] = states
        self.state_machine.start_machine(self.states)

    def sync_rects(self):
        # keeping rect and hit_rect aligned in one helper reduces copy-pasted bookkeeping in subclasses
        self.rect.center = self.pos
        self.hit_rect.center = self.pos

    def set_display_color(self, color):
        # most bosses still use flat placeholder colors, so changing color is centralized here
        self.image.fill(color)

    def get_idle_color(self):
        # subclasses can override this if their normal visual state is more complex
        return self.default_color

    def take_damage(self, amount):
        # all bosses should flash when damaged, so the base class owns that shared response
        self.health -= amount
        self.hit_flash_time = pg.time.get_ticks()

    def update_hit_flash(self):
        # after the flash window ends, restore the boss's normal current color
        if pg.time.get_ticks() - self.hit_flash_time >= 120:
            self.set_display_color(self.get_idle_color())
        else:
            self.set_display_color(self.hit_flash_color)

    def die(self):
        # defeating any boss should spawn particles and remove the sprite immediately
        self.game.spawn_hit_particles(self.rect.center, self.default_color, 45)
        self.kill()
        # defer the level transition until GamePlayingState finishes updating sprites
        # rebuilding the level from inside a sprite update can mutate groups while pygame is iterating them
        self.game.boss_defeated = True
