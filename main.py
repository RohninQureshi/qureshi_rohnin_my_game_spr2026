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
'''
All TODOS to make it easy to keep track


#TODO: update mob's movement, have it chase player, if collision game over, if coin is collected mob stops, level is completed.   

#TODO Add textures to all sprites, update wall texture        


#TODO Fix porjectiles to actually spawn on the player

'''
#Date of Last Update
__updated__ = '2026-03-25 12:30:08'


import pygame as pg
import sys
from random import *
import os
from settings import *
from sprites import *
from utils import *
from state_machine import StateMachine
from game_states import *
import json
from datetime import datetime



#imports


# the game class that will be instantiated in order to run the game...
class Game:  # "The pen factory", all products are "products", not also the "factory"
    def __init__(self):
        pg.init()
        pg.mixer.init()
        # setting up pygame screen using tuple value for width height
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True #creating variables for the state of the game, and they are boolean so the game cant be half running for example
        self.playing = True
        self.game_cooldown = Cooldown(3000) #in milliseconds
        self.camera = None
        self.current_level_index = 0
        self.load_data()
        # saves are stored in a folder inside the project directory
        self.save_dir = path.join(self.game_dir, "saves")
        # restores the newest save before the map is built for play
        self.load_latest_save()
        self.load_current_level()
        # this state machine controls game flow like start, pause, win, and game over
        self.state_machine = StateMachine()
        self.game_states = [
            GameStartState(self),
            GamePlayingState(self),
            GamePausedState(self),
            GameOverState(self),
            GameLevelClearState(self),
            GameWonState(self),
        ]


        self.state_machine.start_machine(self.game_states)

    def ensure_save_dir(self):
        # create the saves folder if it does not already exist
        if not path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def get_save_data(self):
        # packages the minimum progress data needed to restore the game later
        return {
            "timestamp": datetime.now().isoformat(),
            "current_level_index": self.current_level_index,
            "current_level_file": self.levels[self.current_level_index],
        }

    def save_progress(self):
        # writes a new timestamped save file, then removes older extras
        self.ensure_save_dir()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = path.join(self.save_dir, f"save_{timestamp}.json")

        with open(save_path, "w") as f:
            json.dump(self.get_save_data(), f, indent=4)

        self.prune_old_saves(keep_count=3)


    def load_latest_save(self):
        # finds the newest save file in the saves folder and restores the saved level index
        self.ensure_save_dir()
        save_files = [
            path.join(self.save_dir, name)
            for name in os.listdir(self.save_dir)
            if name.endswith(".json")
        ]

        if not save_files:
            return

        latest_save = max(save_files, key=path.getmtime)

        with open(latest_save, "r") as f:
            data = json.load(f)

        saved_index = data.get("current_level_index", 0)

        if 0 <= saved_index < len(self.levels):
            self.current_level_index = saved_index

    def prune_old_saves(self, keep_count=1):
        # keeps only the newest save files so disk usage does not grow forever
        self.ensure_save_dir()

        save_files = [
            path.join(self.save_dir, name)
            for name in os.listdir(self.save_dir)
            if name.endswith(".json")
        ]

        save_files.sort(key=path.getmtime, reverse=True)

        for old_save in save_files[keep_count:]:
            os.remove(old_save)


    # a method is a function tied to a Class

    def load_data(self):
        self.game_dir = path.dirname(__file__) #accesses file space, so it can now see my files
        # sets the directory for level files so maps can be organized in their own folder
        self.level_dir = path.join(self.game_dir, "levels")
        # automatically builds the level list by reading every txt file in the levels folder
        self.levels = sorted(
            [name for name in os.listdir(self.level_dir) if name.endswith(".txt")]
        )       

        self.img_dir = path.join(self.game_dir, 'images') #sets the directory for images
        self.snd_dir = path.join(self.game_dir, 'sounds') #sets the directory for images
        self.wall_img = pg.image.load(path.join(self.img_dir, 'wall_art.png')).convert_alpha() #wall and coin image are to be deleted and moved to sprite sheet
        self.coin_img = pg.image.load(path.join(self.img_dir, 'coin.png')).convert_alpha()
        self.pickup_snd = pg.mixer.Sound(path.join(self.snd_dir, "pickup.mp3"))
        self.map = Map(path.join(self.level_dir, self.levels[self.current_level_index]))
        print('data is loaded')

    def load_current_level(self):
        # reloads the map whenever the current level index changes
        self.map = Map(path.join(self.level_dir, self.levels[self.current_level_index]))

    def next_level(self):
        # advances to the next level if one exists, otherwise transitions to the win state
        if self.current_level_index < len(self.levels) - 1:
            self.current_level_index += 1
            self.load_current_level()
            self.new()
            self.state_machine.transition("playing")
        else:
            self.state_machine.transition("game_won")



    
    def new(self):
        self.all_sprites = pg.sprite.Group() # these lines of code (55-59) are using sprite's grouping function and tying them to variables, so I can call upon different "groups (suchs as mobs, player, or Walls)" seperately
        self.all_players = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()
        
        self.camera = Camera(self.map.width, self.map.height) #Actually instanciates the  camera
        
        for row, tiles in enumerate(self.map.data): #this section of code loads the entities (wall,player,mobs) based upon the map data we made (level1.txt), by enumerating through each cahrecter, and looking at it's value and pos.
            for col, tile, in enumerate(tiles):
                if tile == '1':
                    Wall(self, col, row)
                if tile =='P':
                    self.player = Player(self, col, row)
                if tile =='M':
                    self.mob = Mob(self, col, row)
                if tile =='C':
                    self.coin = Coin(self, col, row)
        # restarts the background music whenever a fresh level is built
        pg.mixer.music.load(path.join(self.snd_dir, "background_soundtrack.mp3"))
        pg.mixer.music.play(loops=-1)


    def run(self):
        while self.running:
            self.dt = (
                self.clock.tick(FPS) / 1000
            )  # divided by 1000 bc we want milliseconds, this is delta time
            
            self.events() #these three functions are constantly called, allowing for things to be drawn, evenets to happen, constantly updating
            self.update()
            self.draw()
            
    def events(self):
        # all global keyboard and window events are handled here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if self.playing:
                        self.playing = False
                    self.running = False

                elif event.key == pg.K_p:
                    current_state = self.state_machine.current_state.get_state_name()
                    if current_state == "playing":
                        self.state_machine.transition("paused")
                    elif current_state == "paused":
                        self.state_machine.transition("playing")

                elif event.key == pg.K_g:
                    self.state_machine.transition("game_over")

                elif event.key == pg.K_RETURN:
                    current_state = self.state_machine.current_state.get_state_name()
                    if current_state == "start":
                        self.state_machine.transition("playing")
                elif event.key == pg.K_TAB:
                    # manual save hotkey for testing the save system
                    self.save_progress()
                elif event.key == pg.K_r:
                    current_state = self.state_machine.current_state.get_state_name()
                    if current_state == "game_won":
                        # winning can reset the game back to level one and the start screen
                        self.current_level_index = 0
                        self.load_current_level()
                        self.new()
                        self.state_machine.transition("start")


    
    

            

                    

    

    def update(self):
        # lets the active game-flow state decide what should update this frame
        self.state_machine.update()
        # self.all_sprites.update() #updating sprites for dynamics (movement of player)
        # if self.camera is not None: #if the camera exists
        #     self.camera.update(self.player) #the camera is updating for player, so it locks onto player
        
    def draw(self):
        self.screen.fill(BLUE)  # screen color
        # self.draw_text("Hello World", 24, WHITE, WIDTH / 2, TILESIZE)  # calling of draw text
        # self.draw_text(str(self.dt), 24, WHITE, WIDTH / 2, HEIGHT / 4)  # calling of draw text
        # self.draw_text(str(self.game_cooldown.ready()), 24, WHITE, WIDTH / 2, HEIGHT / 3) # calling of draw text
        # self.draw_text(str(self.player.pos), 24, WHITE, WIDTH / 2, HEIGHT-TILESIZE*3) # calling of draw text
        
        for sprite in self.all_sprites: #looks through all sprites
            self.screen.blit(sprite.image, self.camera.apply(sprite)) #for each sprite, replace the image with it's image AND apply the camera to it
        
        # draw overlay text after the world so state-specific UI appears on top
        current_state = self.state_machine.current_state.get_state_name()

        if current_state == "paused":
            self.draw_text("PAUSED", 48, WHITE, WIDTH / 2, HEIGHT / 2 - 24)
            print("paused")

        if current_state == "game_over":
            self.draw_text("GAME OVER", 48, WHITE, WIDTH / 2, HEIGHT / 2 - 24)
            print("game_over")
        
        if current_state == "start":
            self.draw_text("VANTABLADE", 64, WHITE, WIDTH / 2, HEIGHT / 3)
            self.draw_text("Press ENTER to start", 28, WHITE, WIDTH / 2, HEIGHT / 2)
        if current_state == "game_won":
            self.draw_text("YOU WIN", 48, WHITE, WIDTH / 2, HEIGHT / 2 - 24)
            self.draw_text("Press R to restart", 24, WHITE, WIDTH / 2, HEIGHT / 2 + 30)


        pg.display.flip()

    def draw_text(self, text, size, color, x, y):  # function that draws text on the screen
        font_name = pg.font.match_font("arial") #font
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color) #actually puts it on screen
        text_rect = text_surface.get_rect() #makes it a rect
        text_rect.midtop = (x, y) #pos of text
        self.screen.blit(text_surface, text_rect)


if __name__ == "__main__":
    g = Game() #instanciates game class, so it can be used
    g.new()
    g.run()
    pg.quit()
