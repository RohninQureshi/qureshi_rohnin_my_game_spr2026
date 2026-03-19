import pygame as pg

#regular game settings
WIDTH = 1024-48
HEIGHT = 768-32
TITLE = "VantaBlade"
FPS = 60
TILESIZE = 32




# tuple storing RGB color values
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0) 

# player values
PLAYER_SPEED = 280
PLAYER_SPRINT_SPEED = 560
PLAYER_HIT_RECT = pg.Rect(0, 0, TILESIZE, TILESIZE)
SPRINT_DURATION = 3000      
SPRINT_RESET_TIME = 10000    


#mob values
MOB_HIT_RECT = pg.Rect(0, 0, TILESIZE, TILESIZE)
MOB_SPEED = PLAYER_SPEED * 0.7
MOB_AGGRO_RADIUS_TILES = 12
MOB_PATH_RECALC_MS = 250
#projectile values
PROJECTILE_SPEED = 500
PROJECTILE_LIFETIME = 750  # milliseconds
