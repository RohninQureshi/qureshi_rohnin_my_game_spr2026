import pygame as pg
from settings import *


# Reads a tilemap text file and stores both the raw layout and map dimensions.
class Map:
    def __init__(self, filename):
        #creating the data for building the map using a list
        self.data = []
        #open a specific file and close it with 'with'
        with open(filename, 'rt') as f:
            for line in f:
                # strip removes the newline so each map row is only tile characters
                self.data.append(line.strip())
        
        
        #        
        # tile dimensions count how many text characters wide and tall the map is
        self.tilewidth = len(self.data[0])
        self.tileheight = len(self.data)
        # pixel dimensions convert tile counts into actual world size for camera and collision logic
        self.width = self.tilewidth * TILESIZE
        self.height = self.tileheight * TILESIZE


# Loads an image file and slices out individual frames from a sprite sheet.
class Spritesheet:
    def __init__(self, filename):
        # convert makes the sheet match the display format for faster blitting later
        self.spritesheet = pg.image.load(filename).convert()

    def get_image(self, x, y, width, height):
        image = pg.Surface((width, height)) #creates an image
        image.blit(self.spritesheet, (0,0), (x, y, width, height)) #updates the actual image to be from sprite sheet
        new_image = pg.transform.scale(image, (width, height)) #scales the image to be correct, for resolution
        # return the cropped frame so player animation code can store it in a list
        image = new_image
        return image



# Simple reusable timer class.
class Cooldown:
    def __init__(self, time):
        self.start_time = 0
        # Allows us to set propety for time until cooldown
        self.time = time

    def start(self):
        # stores the moment the cooldown began so later checks can compare against it
        self.start_time = pg.time.get_ticks()

    def ready(self):
        # sets current time
        current_time = pg.time.get_ticks()
        # if the difference between current and start time are greater than self.time, return True
        
        if current_time - self.start_time >= self.time:  #If the change in time (t final - t initial) is greater than or equal to the cooldown time, you can use the item again, enough time has passed, otherwise you can't, you haven't gone long enough to where the cooldown has worn off
            return True
        return False




# Camera class that keeps the player centered while clamping view to the map bounds.
class Camera:
    def __init__(self, world_width, world_height):
        self.camera = pg.Rect(0, 0, world_width, world_height) #creates a camera as a rectangle
        # stores the size of the full world so the camera knows the limits of the map
        self.world_width = world_width
        self.world_height = world_height

    def apply(self, entity):
        # offsets an entity by the camera position so the world appears to move around the player
        return entity.rect.move(self.camera.topleft)

    def apply_point(self, point):
        # converts a world-space point into screen-space for effects that are not normal sprites
        return point.x + self.camera.x, point.y + self.camera.y

    def update(self, target):
        # moves the camera so the target stays centered on screen
        x = -target.rect.centerx + WIDTH // 2
        y = -target.rect.centery + HEIGHT // 2

        # these clamps stop the camera from showing empty space beyond the map edges
        x = min(0, x) 
        y = min(0, y)
        x = max(-(self.world_width - WIDTH), x)
        y = max(-(self.world_height - HEIGHT), y)

        # updates the camera rectangle using the new clamped offset
        self.camera = pg.Rect(x, y, self.world_width, self.world_height)
        
def draw_health_bar(surf,x,y,pct):
    # health is passed in as a percentage from 0 to 100
    if pct<0:
        # clamp negative values so the fill rectangle never draws backwards
        pct = 0
    # bar size is kept constant so only the red fill width changes with health
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (pct/100)*BAR_LENGTH
    outline_rect = pg.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pg.Rect(x, y, fill, BAR_HEIGHT)
    # draw the red fill first, then draw the white border on top for readability
    pg.draw.rect(surf, RED, fill_rect)
    pg.draw.rect(surf, WHITE, outline_rect, 2)

