# game engine using template from Chris Bradfield's "Making Games with Python & Pygame"
#I can push from vscode
"""
Main file responsible for game loop including input, update, and draw methods.

Tools for game development.

# creating pixel art:
https://www.piskelapp.com/

# free game assets:
https://opengameart.org/

# free sprite sheets:
https://www.kenney.nl/assets

# sound effects:
https://www.bfxr.net/
# music:
https://incompetech.com/music/royalty-free/


"""

import pygame as pg
import sys
from random import *
from os import path 
from settings import *
from sprites import *
from utils import *

# import settings


# the game class that will be instantiated in order to run the game...
class Game:  # "The pen factory", all products are "products", not also the "factory"
    def __init__(self):
        pg.init()
        # setting up pygame screen using tuple value for width height
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True #creating variables for the state of the game, and they are boolean so the game cant be half running for example
        self.playing = True
        self.game_cooldown = Cooldown(3000) #in milliseconds
        self.load_data()

    # a method is a function tied to a Class

    def load_data(self):
        self.game_dir = path.dirname(__file__) #accesses file space, so it can now see my files
        self.map = Map(path.join(self.game_dir, 'level1.txt'))
        print('data is loaded')

    def new(self):
        self.all_sprites = pg.sprite.Group() # these lines of code (55-59) are using sprite's grouping function and tying them to variables, so I can call upon different "groups (suchs as mobs, player, or Walls)" seperately
        self.all_players = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        # self.player = Player(self, 15, 15) #these lines of code (59-61) actually load the class on Screen, and assigned a variable to them
        # self.mob = Mob(self, 4, 4)
        # self.wall = Wall(self,10,10)
        for row, tiles in enumerate(self.map.data):
            for col, tile, in enumerate(tiles):
                if tile == '1':
                    Wall(self, col, row)
                if tile =='P':
                    self.player = Player(self, col, row)
                if tile =='M':
                    self.mob = Mob(self, col, row)
                if tile =='C':
                    self.coin = Coin(self, col, row)
                
            
        self.run()

    def run(self):
        while self.running:
            self.dt = (
                self.clock.tick(FPS) / 1000
            )  # divided by 1000 bc we want milliseconds, this is delta time
            self.events() #these three functions are constantly called, allowing for things to be drawn, evenets to happen, constantly updating
            self.update()
            self.draw()

    def events(self):
        for event in pg.event.get():
            if (
                event.type == pg.QUIT
            ):  # allows quitting, if playing stops playing, and it stops running
                if self.playing:
                    self.playing = False
                self.running = False
            if (
                event.type == pg.MOUSEBUTTONUP
            ):  # this allows us to utilize releasing the mouse button as an input or condition
                print("i can get mouse input")
                print(event.pos)
            if event.type == pg.KEYDOWN:  # Same here but for when the key is pressed
                if event.key == pg.K_k:
                    print("i can determine when keys are pressed")
            if event.type == pg.KEYUP:  # Same here but for when the key is released
                if event.key == pg.K_k:
                    print("i can determine when keys are released")
            

                    

    def quit(self):
        pass

    def update(self):
        self.all_sprites.update() #updating sprites for dynamics (movement of player)
        
    def draw(self):
        self.screen.fill(BLUE)  # screen color
        self.draw_text("Hello World", 24, WHITE, WIDTH / 2, TILESIZE)  # calling of draw text
        self.draw_text(str(self.dt), 24, WHITE, WIDTH / 2, HEIGHT / 4)  # calling of draw text
        self.draw_text(str(self.game_cooldown.ready()), 24, WHITE, WIDTH / 2, HEIGHT / 3) # calling of draw text
        self.draw_text(str(self.player.pos), 24, WHITE, WIDTH / 2, HEIGHT-TILESIZE*3) # calling of draw text
        self.all_sprites.draw(self.screen) #drawing sprite
        pg.display.flip()

    def draw_text(self, text, size, color, x, y):  # function thatdraws text on the screen
        font_name = pg.font.match_font("arial") #font
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color) #actually puts it on screen
        text_rect = text_surface.get_rect() #makes it a rect, good for manipulating pos
        text_rect.midtop = (x, y) #pos of text
        self.screen.blit(text_surface, text_rect)


if __name__ == "__main__":
    g = Game()

while g.running:
    g.new()


pg.quit()