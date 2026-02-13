import pygame as pg
from settings import *


#This class allows for loading up a "world" via data in txt format (look at level1.txt for reference on what Im talking about)
class Map:
    def __init__(self, filename):
        #creating the data for building the map using a list
        self.data = []
        #open a specific file and close it with 'with'
        with open(filename, 'rt') as f:
            for line in f:
                self.data.append(line.strip())
        
        
        #        
        self.tilewidth = len(self.data[0])
        self.tileheight = len(self.data)
        self.width = self.tilewidth * TILESIZE
        self.height = self.tileheight * TILESIZE

# This class creates a countdown timer for a cooldown
class Cooldown:
    def __init__(self, time):
        self.start_time = 0
        # Allows us to set propety for time until cooldown
        self.time = time

    def start(self):
        self.start_time = pg.time.get_ticks()

    def ready(self):
        # sets current time
        current_time = pg.time.get_ticks()
        # if the difference between current and start time are greater than self.time
        # return True
        
        if current_time - self.start_time >= self.time:  #If the change in time (t final - t initial) is greater than or equal to the cooldown time, you can use the item again, enough time has passed, otherwise you can't, you haven't gone long enough to where the cooldown has worn off
            return True
        return False
