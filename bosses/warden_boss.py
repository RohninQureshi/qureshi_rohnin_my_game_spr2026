import pygame as pg

from bosses.base_boss import BaseBoss, vec
from settings import *
from states.warden_states import *
from utils import Cooldown


# Warden is the second boss: it tests target priority by forcing the player to clear summons.
class WardenBoss(BaseBoss):
    def __init__(self, game, x, y):
        # BaseBoss owns shared health, hitbox, sprite groups, and state-machine setup.
        super().__init__(
            game,
            x,
            y,
            TILESIZE * 3,
            TILESIZE * 3,
            WARDEN_HIT_RECT,
            WARDEN_MAX_HEALTH,
            GREEN,
            "WARDEN",
        )

        # Damage values stay on the boss object so shared combat code can read them generically.
        self.contact_damage = WARDEN_CONTACT_DAMAGE
        self.contact_cooldown = WARDEN_CONTACT_COOLDOWN
        self.projectile_damage = WARDEN_PROJECTILE_DAMAGE

        # Warden starts shielded; the summon clear creates the damage window.
        self.vulnerable = False
        self.mode = "wait"
        self.mode_start_time = pg.time.get_ticks()
        self.shot_cd = Cooldown(WARDEN_SHOT_COOLDOWN)
        self.summons = pg.sprite.Group()

        self.keep_inside_arena()
        self.start_states([
            WardenWaitState(self),
            WardenSummonState(self),
            WardenShootState(self),
            WardenVulnerableState(self),
            WardenRecoverState(self),
        ])

    def set_mode(self, mode):
        # Every state enters through this method so timing, color, and vulnerability stay centralized.
        self.mode = mode
        self.mode_start_time = pg.time.get_ticks()

        if mode == "summon":
            self.vulnerable = False
            self.set_display_color(BLUE)
        elif mode == "shoot":
            self.vulnerable = False
            self.set_display_color(YELLOW)
        elif mode == "vulnerable":
            # White means the shield is down and player projectiles can damage the boss.
            self.vulnerable = True
            self.set_display_color(WHITE)
        elif mode == "recover":
            self.vulnerable = False
            self.set_display_color(GREEN)
        else:
            self.vulnerable = False
            self.set_display_color(GREEN)

    def get_idle_color(self):
        # Hit flash returns to the correct color for the current Warden phase.
        if self.mode == "summon":
            return BLUE
        if self.mode == "shoot":
            return YELLOW
        if self.mode == "vulnerable":
            return WHITE
        return GREEN

    def take_damage(self, amount):
        # Warden only takes damage during the vulnerability state, creating the target-priority test.
        if not self.vulnerable:
            self.hit_flash_time = pg.time.get_ticks()
            return

        super().take_damage(amount)

    def update(self):
        # Sync first so state code and projectile code read current rect positions.
        self.sync_rects()

        if self.health <= 0:
            self.die()
            return

        self.update_hit_flash()
        self.state_machine.update()
        self.keep_inside_arena()
        self.sync_rects()

    def keep_inside_arena(self):
        # Warden is mostly stationary, but clamping keeps level edits from spawning it inside borders.
        half_width = self.hit_rect.width / 2
        half_height = self.hit_rect.height / 2
        left_bound = TILESIZE + half_width
        right_bound = self.game.map.width - TILESIZE - half_width
        top_bound = TILESIZE + half_height
        bottom_bound = self.game.map.height - TILESIZE - half_height

        self.pos.x = max(left_bound, min(right_bound, self.pos.x))
        self.pos.y = max(top_bound, min(bottom_bound, self.pos.y))

    def summon_mobs(self):
        # Import locally to avoid making sprites.py depend on boss files during startup.
        from sprites import Mob

        self.summons.empty()
        boss_col = max(2, int(self.pos.x // TILESIZE))
        boss_row = max(2, int(self.pos.y // TILESIZE))

        # These offsets spread adds around Warden so the player must pick targets under pressure.
        summon_offsets = [(-7, 0), (-4, -3), (-2, 0)]
        for col_offset, row_offset in summon_offsets[:WARDEN_SUMMON_COUNT]:
            summon_col = max(2, boss_col + col_offset)
            summon_row = max(2, boss_row + row_offset)
            mob = Mob(self.game, summon_col, summon_row)
            self.summons.add(mob)

    def active_summons_alive(self):
        # The group automatically loses killed mobs, so len tells whether the shield should stay up.
        return len(self.summons) > 0

    def shoot_at_player(self):
        # Warden fires slow aimed projectiles so the threat supports the crowd-control test.
        direction = vec(self.game.player.rect.center) - vec(self.rect.center)
        if direction.length_squared() == 0:
            direction = vec(-1, 0)
        WardenProjectile(self.game, self.rect.centerx, self.rect.centery, direction)


# Slow enemy projectile used by Warden's pressure phase.
class WardenProjectile(pg.sprite.Sprite):
    def __init__(self, game, x, y, direction):
        self.groups = game.all_sprites, game.all_boss_projectiles
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.damage = WARDEN_PROJECTILE_DAMAGE
        self.image = pg.Surface((TILESIZE // 2, TILESIZE // 2))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos
        self.vel = direction.normalize() * WARDEN_PROJECTILE_SPEED
        self.spawn_time = pg.time.get_ticks()
        self.last_trail_time = self.spawn_time

    def update(self):
        # Movement uses delta time so projectile speed is stable across different computers.
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos
        self.spawn_trail_particles()

        if pg.time.get_ticks() - self.spawn_time >= WARDEN_PROJECTILE_LIFETIME:
            self.kill()
            return

        if pg.sprite.spritecollideany(self, self.game.all_walls):
            self.game.spawn_hit_particles(self.rect.center, GREEN, 4)
            self.kill()

    def spawn_trail_particles(self):
        # Trail particles make slow Warden shots readable while the player is handling summons.
        now = pg.time.get_ticks()
        if now - self.last_trail_time >= PROJECTILE_TRAIL_DELAY:
            self.last_trail_time = now
            self.game.spawn_hit_particles(self.rect.center, GREEN, 1)
