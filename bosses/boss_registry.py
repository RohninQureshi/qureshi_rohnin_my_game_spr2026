from bosses.sentinel_boss import SentinelBoss
from bosses.warden_boss import WardenBoss


# Each map character in this table represents a boss spawn.
#
# Keeping the spawn lookup inside the bosses package makes the whole boss system
# self-contained: boss classes, shared boss code, and boss spawning rules all live
# together in one place.
# When boss 2 exists, add another entry such as:
#     "S: SentinelBoss,
# and the level loader will automatically know how to spawn it.
BOSS_SPAWN_TABLE = {
    "S": SentinelBoss,
    # H stands for Hive/Warden so W can remain the weapon-upgrade tile.
    "H": WardenBoss,
}
