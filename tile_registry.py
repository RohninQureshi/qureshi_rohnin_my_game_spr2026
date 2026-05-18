from bosses.boss_registry import BOSS_SPAWN_TABLE
from sprites import AmmoPickup, ArmorPickup, Coin, Mob, Player, Wall, WeaponPickup


# This file is the single place where level-file characters are connected to game objects.
# main.py still loops through the map, but this registry decides what each tile letter means.


def spawn_wall(game, col, row):
    # walls only need to exist in the wall/sprite groups, so they do not need to be stored on game
    Wall(game, col, row)


def spawn_player(game, col, row):
    # game.player is stored because camera, collision, saving, and combat all need the active player
    game.player = Player(game, col, row)


def spawn_mob(game, col, row):
    # mobs add themselves to sprite groups, but this keeps the old game.mob reference available
    game.mob = Mob(game, col, row)


def spawn_coin(game, col, row):
    # coins add themselves to coin and sprite groups inside the Coin class
    game.coin = Coin(game, col, row)


def spawn_armor(game, col, row):
    # armor pickups increase damage reduction when collected by the player
    if not game.is_powerup_collected(col, row, "A"):
        ArmorPickup(game, col, row)


def spawn_weapon(game, col, row):
    # weapon pickups increase projectile damage when collected by the player
    if not game.is_powerup_collected(col, row, "W"):
        WeaponPickup(game, col, row)


def spawn_ammo(game, col, row):
    # ammo pickups refill shots without resetting ammo between levels
    if not game.is_powerup_collected(col, row, "B"):
        AmmoPickup(game, col, row)


def spawn_boss(game, col, row, tile):
    # boss letters are handled by the boss registry so each boss can live in its own module
    boss_class = BOSS_SPAWN_TABLE[tile]
    game.boss = boss_class(game, col, row)


# Normal tile spawns use simple functions because each one needs slightly different setup.
# To add a new non-boss tile, create a spawn function above and add one entry here.
TILE_SPAWN_TABLE = {
    "1": spawn_wall,
    "P": spawn_player,
    "M": spawn_mob,
    "C": spawn_coin,
    "A": spawn_armor,
    "W": spawn_weapon,
    "B": spawn_ammo,
}
