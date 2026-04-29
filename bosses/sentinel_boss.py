import pygame as pg

from settings import *
from states.sentinel_states import *
from utils import Cooldown
from state_machine import State
from bosses.base_boss import BaseBoss, vec


# Sentinel boss implementation kept in its own file so future bosses can follow the same pattern.
class SentinelBoss(BaseBoss):
    def __init__(self, game, x, y):
        # BaseBoss handles sprite groups, rect setup, health, and the local boss state machine.
        super().__init__(
            game,
            x,
            y,
            TILESIZE * 3,
            TILESIZE * 3,
            SENTINEL_HIT_RECT,
            SENTINEL_MAX_HEALTH,
            YELLOW,
            "SENTINEL",
        )

        # Sentinel-specific combat values are stored on the object so shared combat code can stay generic.
        self.contact_damage = SENTINEL_CONTACT_DAMAGE
        self.contact_cooldown = SENTINEL_CONTACT_COOLDOWN
        self.projectile_damage = SENTINEL_PROJECTILE_DAMAGE

        # spawn_x is the far-right reset point used before every charge attack
        self.spawn_x = self.pos.x
        # spawn_y is the grounded resting point; charge_y is the raised dash height
        self.spawn_y = self.pos.y - TILESIZE // 2
        self.pos.y = self.spawn_y
        self.charge_y = self.spawn_y - SENTINEL_CHARGE_HEIGHT
        # pound_hover_y is where the boss waits before dropping straight down onto the player
        self.pound_hover_y = self.spawn_y - SENTINEL_POUND_HEIGHT
        self.charge_target_x = self.spawn_x - self.game.map.width * 0.75
        # pound_target_x is set during the lock-on phase so the drop uses a committed lane
        self.pound_target_x = self.pos.x
        self.pound_impact_done = False

        # mode is still kept as a readable summary string even though the state machine runs the logic now.
        self.mode = "wait"
        self.mode_start_time = pg.time.get_ticks()
        self.next_attack = "shoot"
        self.shot_cd = Cooldown(SENTINEL_SHOT_COOLDOWN)

        # initialize arena bounds before any state tries to use them
        self.keep_inside_arena()
        self.start_states([
            SentinelWaitState(self),
            SentinelShootState(self),
            SentinelChargeWarnState(self),
            SentinelChargeState(self),
            SentinelGroundPoundLockState(self),
            SentinelGroundPoundWarnState(self),
            SentinelGroundPoundDropState(self),
            SentinelRecoverState(self),
        ])

    def set_mode(self, mode):
        # state enter methods call set_mode so timing, movement resets, and placeholder colors stay centralized
        self.mode = mode
        self.mode_start_time = pg.time.get_ticks()

        if mode == "charge_warn":
            # warning phase always begins from the right-side starting position
            self.pos.x = self.spawn_x
            self.pos.y = self.spawn_y
            self.vel.x = 0
            self.set_display_color(YELLOW)
        elif mode == "charge":
            # charge begins from the raised height so the player can still shoot under the boss
            self.pos.y = self.charge_y
            self.set_display_color(RED)
        elif mode == "ground_pound_lock":
            # lock-on moves to a hovering position above the player before the slam is committed
            self.pos.y = self.pound_hover_y
            self.vel.x = 0
            self.pound_impact_done = False
            self.set_display_color(YELLOW)
        elif mode == "ground_pound_warn":
            # warning pause keeps the boss still so the player has a readable dodge window
            self.pos.y = self.pound_hover_y
            self.vel.x = 0
            self.set_display_color((255, 165, 0))
        elif mode == "ground_pound_drop":
            # once the drop starts, x is fixed and only vertical movement matters
            self.vel.x = 0
            self.set_display_color(RED)
        elif mode == "recover":
            # recover uses white so the player can visually read a safer damage window
            self.set_display_color(WHITE)
        else:
            self.set_display_color(YELLOW)

    def get_idle_color(self):
        # hit flash returns to a different color depending on which Sentinel state is currently active
        if self.mode == "charge":
            return RED
        if self.mode == "ground_pound_warn":
            return (255, 165, 0)
        if self.mode == "ground_pound_drop":
            return RED
        if self.mode == "recover":
            return WHITE
        return YELLOW

    def update(self):
        # sync once before logic so state code reads up-to-date positions and rectangles
        self.sync_rects()

        if self.health <= 0:
            # Sentinel currently ends the game when defeated because it is your current final boss
            self.die()
            return

        # flash handling stays separate from attack logic so all future bosses can reuse the same pattern
        self.update_hit_flash()
        # attack decisions live in sentinel_states.py instead of one giant update chain
        self.state_machine.update()

        # clamp at the end of the frame so movement states cannot push the boss through arena walls
        self.keep_inside_arena()
        self.sync_rects()

    def keep_inside_arena(self):
        # bounds use one tile of padding because the level border is made of wall tiles
        half_width = self.hit_rect.width / 2
        half_height = self.hit_rect.height / 2
        self.left_bound = TILESIZE + half_width
        right_bound = self.game.map.width - TILESIZE - half_width
        top_bound = TILESIZE + half_height
        bottom_bound = self.game.map.height - TILESIZE - half_height

        # clamp x and y separately so charge movement cannot push the boss through map edges
        self.pos.x = max(self.left_bound, min(right_bound, self.pos.x))
        self.pos.y = max(top_bound, min(bottom_bound, self.pos.y))

    def shoot_at_player(self):
        # projectile direction points from boss center toward the player's current center
        direction = vec(self.game.player.rect.center) - vec(self.rect.center)
        if direction.length_squared() == 0:
            direction = vec(-1, 0)
        SentinelProjectile(self.game, self.rect.centerx, self.rect.centery, direction)

    def apply_ground_pound_impact(self):
        # impact should only happen once per drop, even though the boss remains on the ground for several frames
        if self.pound_impact_done:
            return

        self.pound_impact_done = True
        # landing burst makes the slam feel heavy and easy to notice
        self.game.spawn_hit_particles(self.rect.midbottom, YELLOW, 22)

        # measure from the boss center to the player center so the slam checks a simple circular danger radius
        distance_to_player = vec(self.game.player.rect.center).distance_to(self.rect.center)
        if distance_to_player <= SENTINEL_POUND_RADIUS and self.game.boss_damage_cd.ready():
            damage = self.game.damage_player(SENTINEL_POUND_DAMAGE)
            self.game.add_damage_number(self.game.player.rect.center, damage, RED)
            self.game.spawn_hit_particles(self.game.player.rect.center, RED, 10)
            self.game.boss_damage_cd.start()


# Projectile fired by the Sentinel boss toward the player.
class SentinelProjectile(pg.sprite.Sprite):
    def __init__(self, game, x, y, direction):
        self.groups = game.all_sprites, game.all_boss_projectiles
        pg.sprite.Sprite.__init__(self, self.groups)

        # the projectile stores its own damage value so shared combat code does not need boss-name checks
        self.game = game
        self.damage = SENTINEL_PROJECTILE_DAMAGE
        self.image = pg.Surface((TILESIZE // 2, TILESIZE // 2))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos
        self.vel = direction.normalize() * SENTINEL_PROJECTILE_SPEED
        self.spawn_time = pg.time.get_ticks()

        # trails and afterimages make boss shots readable even before real projectile art exists
        self.last_trail_time = self.spawn_time
        self.last_afterimage_time = self.spawn_time

    def update(self):
        # boss projectile movement also uses delta time so speed stays consistent across machines
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos
        self.spawn_trail_particles()
        self.spawn_afterimage()

        if pg.time.get_ticks() - self.spawn_time >= SENTINEL_PROJECTILE_LIFETIME:
            self.kill()
            return

        # boss shots disappear on walls so they do not travel through the arena forever
        if pg.sprite.spritecollideany(self, self.game.all_walls):
            self.game.spawn_hit_particles(self.rect.center, YELLOW, 4)
            self.kill()

    def spawn_trail_particles(self):
        # yellow trail particles separate boss shots from the player's red shots
        now = pg.time.get_ticks()
        if now - self.last_trail_time >= PROJECTILE_TRAIL_DELAY:
            self.last_trail_time = now
            self.game.spawn_hit_particles(self.rect.center, YELLOW, 1)

    def spawn_afterimage(self):
        # boss projectile afterimages make enemy shots readable without mixing with player red shots
        now = pg.time.get_ticks()
        if now - self.last_afterimage_time >= PROJECTILE_AFTERIMAGE_DELAY:
            self.last_afterimage_time = now
            self.game.spawn_afterimage(self.image, self.rect.copy())
