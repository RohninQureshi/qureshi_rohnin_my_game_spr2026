import pygame as pg

# regular game settings used by the window, clock, and tile-based map system
WIDTH = 1024-48
HEIGHT = 768-32
TITLE = "VantaBlade"
FPS = 60
# every character in a level text file becomes one square tile of this size
TILESIZE = 32





# tuple storing RGB color values used by sprites, menus, and HUD drawing
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0) 

# player movement values
# speed values are in pixels per second because movement is multiplied by delta time
PLAYER_SPEED = 280
PLAYER_SPRINT_SPEED = 560
PLAYER_HIT_RECT = pg.Rect(0, 0, TILESIZE, TILESIZE)
# sprint timing is stored in milliseconds because pygame's clock uses milliseconds
SPRINT_DURATION = 5000      
SPRINT_RESET_TIME = 10000
# gravity and jump velocity control the basic platforming feel
GRAVITY = 1800
JUMP_VELOCITY = -700
MAX_FALL_SPEED = 1200   


# mob values
# mob hit rect is separate from the image so collision size can be tuned later
MOB_HIT_RECT = pg.Rect(0, 0, TILESIZE, TILESIZE)
MOB_SPEED = PLAYER_SPEED * 0.7
# these pathfinding values are saved for future A* enemy behavior
MOB_AGGRO_RADIUS_TILES = 12
MOB_PATH_RECALC_MS = 250
# contact damage values control how much health a mob removes and how often it can happen
MOB_MAX_HEALTH = 100
MOB_DAMAGE = 25
MOB_DAMAGE_COOLDOWN = 800



# projectile values
# projectile speed is pixels per second, and lifetime is milliseconds before auto-despawn
PROJECTILE_SPEED = 500
PROJECTILE_LIFETIME = 750  # milliseconds
# one normal projectile does enough damage to defeat one regular mob
PLAYER_PROJECTILE_MOB_DAMAGE = 100

# hit feedback values
# damage numbers and particles are short-lived visual feedback, not gameplay objects
DAMAGE_NUMBER_LIFETIME = 1000
DAMAGE_NUMBER_RISE_SPEED = 45
PARTICLE_LIFETIME = 450
PARTICLE_MIN_SPEED = 80
PARTICLE_MAX_SPEED = 220
PARTICLE_GRAVITY = 500
# these timers keep constant effects from spawning too many particles every frame
SPRINT_PARTICLE_DELAY = 70
PROJECTILE_TRAIL_DELAY = 45
LANDING_PARTICLE_MIN_SPEED = 300
# afterimages are transparent image copies used to show speed during sprinting and shooting
AFTERIMAGE_LIFETIME = 220
AFTERIMAGE_START_ALPHA = 120
SPRINT_AFTERIMAGE_DELAY = 85
PROJECTILE_AFTERIMAGE_DELAY = 55

# sentinel boss values
# boss health is intentionally high so the fight lasts longer than a normal mob encounter
SENTINEL_MAX_HEALTH = 1000
SENTINEL_HIT_RECT = pg.Rect(0, 0, TILESIZE * 3, TILESIZE * 3)
SENTINEL_PROJECTILE_SPEED = 360
SENTINEL_PROJECTILE_DAMAGE = 15
SENTINEL_PROJECTILE_LIFETIME = 2500
SENTINEL_SHOT_COOLDOWN = 700
SENTINEL_CHARGE_SPEED = 900
# the boss rises this many pixels during its charge so the body is easier to shoot
SENTINEL_CHARGE_HEIGHT = TILESIZE * 4
SENTINEL_CONTACT_DAMAGE = 25
SENTINEL_CONTACT_COOLDOWN = 900
PLAYER_PROJECTILE_BOSS_DAMAGE = 100
