from bosses.sentinel_boss import SentinelBoss


# Each map character in this table represents a boss spawn.
#
# Keeping the spawn lookup inside the bosses package makes the whole boss system
# self-contained: boss classes, shared boss code, and boss spawning rules all live
# together in one place.
# When boss 2 exists, add another entry such as:
#     "R": RiftWardenBoss,
# and the level loader will automatically know how to spawn it.
BOSS_SPAWN_TABLE = {
    "S": SentinelBoss,
}
