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
#Date of Last Update 24hr time
__updated__ = '2026-04-13 13:26:10'


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



# imports above bring in pygame, file tools, settings constants, sprites, helpers, states, and json saving


# the game class that will be instantiated in order to run the game...
# Main game class that owns the window, assets, save data, level loading, and game loop.
class Game:  # "The pen factory", all products are "products", not also the "factory"
    def __init__(self):
        # boot pygame systems before any window, sound, or font work happens
        pg.init()
        pg.mixer.init()
        # setting up pygame screen using tuple value for width height
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True #creating variables for the state of the game, and they are boolean so the game cant be half running for example
        self.playing = True
        # cooldown objects track timed actions without needing extra frame counters
        self.game_cooldown = Cooldown(3000) #in milliseconds
        self.mob_damage_cd = Cooldown(MOB_DAMAGE_COOLDOWN)
        # this makes mob damage available immediately instead of waiting once at startup
        self.mob_damage_cd.start_time = -MOB_DAMAGE_COOLDOWN
        # these level fields are set before loading data so saves can change the starting level
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

        # registers the game flow states and enters the first one in the list
        self.state_machine.start_machine(self.game_states)

    def ensure_save_dir(self):
        # create the saves folder if it does not already exist
        if not path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def get_save_data(self):
        # packages the minimum progress data needed to restore the game later
        # only small serializable values go into the save file, not live sprite objects
        return {"timestamp": datetime.now().isoformat(),"current_level_index": self.current_level_index,"current_level_file": self.levels[self.current_level_index],}

    def save_progress(self):
        # writes a new timestamped save file, then removes older extras
        # ensure the folder exists before trying to open a save path inside it
        self.ensure_save_dir()
        # timestamp makes each save file unique and easy to sort by date
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = path.join(self.save_dir, f"save_{timestamp}.json")

        with open(save_path, "w") as f:
            # indent keeps the json readable if the save file is opened manually
            json.dump(self.get_save_data(), f, indent=4)

        # after writing a new save, delete older extras to keep the folder small
        self.prune_old_saves(keep_count=3)


    def load_latest_save(self):
        # finds the newest save file in the saves folder and restores the saved level index
        self.ensure_save_dir()
        # build a list of candidate save files so non-json files are ignored
        save_files = [
            path.join(self.save_dir, name)
            for name in os.listdir(self.save_dir)
            if name.endswith(".json")
        ]

        # on a fresh run there may be no saves yet, so just keep the default level index
        if not save_files:
            return

        # the newest file becomes the restore target
        latest_save = max(save_files, key=path.getmtime)

        with open(latest_save, "r") as f:
            data = json.load(f)

        # read the saved level safely and clamp it to the available level list
        saved_index = data.get("current_level_index", 0)

        if 0 <= saved_index < len(self.levels):
            self.current_level_index = saved_index

    def prune_old_saves(self, keep_count=3):
        # keeps only the newest save files so disk usage does not grow forever
        self.ensure_save_dir()

        # collect all save files before sorting by modification time
        save_files = [
            path.join(self.save_dir, name)
            for name in os.listdir(self.save_dir)
            if name.endswith(".json")
        ]

        # newest files come first so anything after keep_count can be deleted
        save_files.sort(key=path.getmtime, reverse=True)

        for old_save in save_files[keep_count:]:
            # remove every save past the limit to keep only the most recent ones
            os.remove(old_save)


    # a method is a function tied to a Class

    def load_data(self):
        self.game_dir = path.dirname(__file__) #accesses file space, so it can now see my files
        # sets the directory for level files so maps can be organized in their own folder
        self.level_dir = path.join(self.game_dir, "levels")
        # automatically builds the level list by reading every txt file in the levels folder
        # this means new level files work without manually editing a list in code
        self.levels = sorted([name for name in os.listdir(self.level_dir) if name.endswith(".txt")])       

        self.img_dir = path.join(self.game_dir, 'images') #sets the directory for images
        self.snd_dir = path.join(self.game_dir, 'sounds') #sets the directory for images
        # these assets are loaded once here so all sprites can reuse the same surfaces and sounds
        self.wall_img = pg.image.load(path.join(self.img_dir, 'wall_art.png')).convert_alpha() #wall and coin image are to be deleted and moved to sprite sheet
        self.coin_img = pg.image.load(path.join(self.img_dir, 'coin.png')).convert_alpha()
        self.pickup_snd = pg.mixer.Sound(path.join(self.snd_dir, "pickup.mp3"))
        # load the current level immediately so the first call to new() can build the map
        self.map = Map(path.join(self.level_dir, self.levels[self.current_level_index]))
        print('data is loaded')

    def load_current_level(self):
        # reloads the map whenever the current level index changes
        # this method is reused by loading saves, restarting, and moving to the next level
        self.map = Map(path.join(self.level_dir, self.levels[self.current_level_index]))

    def next_level(self):
        # advances to the next level if one exists, otherwise transitions to the win state
        if self.current_level_index < len(self.levels) - 1:
            # bump the index first so load_current_level reads the next map file
            self.current_level_index += 1
            self.load_current_level()
            # rebuild all sprite groups from the new map before resuming play
            self.new()
            self.state_machine.transition("playing")
        else:
            # if there is no next level left, hand off to the win screen state
            self.state_machine.transition("game_won")

    def restart_from_title(self):
        # reset the level index so a restart always begins from the first level
        self.current_level_index = 0
        self.load_current_level()
        # rebuild all sprite groups so player health, mobs, coins, and projectiles reset cleanly
        self.new()
        # return to the title screen instead of starting gameplay immediately
        self.state_machine.transition("start")



    
    def new(self):
        # each new level starts with fresh sprite groups so old level objects disappear
        self.all_sprites = pg.sprite.Group() # these lines of code are using sprite's grouping function and tying them to variables, so I can call upon different "groups (suchs as mobs, player, or Walls)" seperately
        self.all_players = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()
        
        self.camera = Camera(self.map.width, self.map.height) #Actually instanciates the  camera
        
        for row, tiles in enumerate(self.map.data): #this section of code loads the entities (wall,player,mobs) based upon the map data we made (level1.txt), by enumerating through each cahrecter, and looking at it's value and pos.
            for col, tile, in enumerate(tiles):
                # each map character spawns a different object into the world
                # this keeps level design inside text files instead of hardcoding positions
                if tile == '1':
                    Wall(self, col, row)
                if tile =='P':
                    self.player = Player(self, col, row)
                if tile =='M':
                    self.mob = Mob(self, col, row)
                if tile =='C':
                    self.coin = Coin(self, col, row)
        # every fresh level rebuild gives the player full health for a clean level start
        self.player.health = 100
        # restarting the level also restarts the background music loop for a clean reset
        pg.mixer.music.load(path.join(self.snd_dir, "background_soundtrack.mp3"))
        pg.mixer.music.play(loops=-1)


    def run(self):
        while self.running:
            # tick locks the game to FPS and returns the time since the last frame
            self.dt = (
                self.clock.tick(FPS) / 1000
            )  # divided by 1000 bc we want milliseconds, this is delta time
            
            # every frame follows the same order: handle input, update state, then draw
            self.events() #these three functions are constantly called, allowing for things to be drawn, evenets to happen, constantly updating
            self.update()
            self.draw()
            
    def events(self):
        # all global keyboard and window events are handled here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                # closing the window should stop both the active run and the outer game loop
                if self.playing:
                    self.playing = False
                self.running = False

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    # escape is treated as a full quit shortcut from anywhere in the game
                    if self.playing:
                        self.playing = False
                    self.running = False

                elif event.key == pg.K_p: #transition into or out of pause state
                    # pause only toggles between the two gameplay-related states
                    current_state = self.state_machine.current_state.get_state_name()
                    if current_state == "playing":
                        self.state_machine.transition("paused")
                    elif current_state == "paused":
                        self.state_machine.transition("playing")

                elif event.key == pg.K_g: #transition into game over (test)
                    self.state_machine.transition("game_over")

                elif event.key == pg.K_RETURN: #transition into playing state
                    current_state = self.state_machine.current_state.get_state_name()
                    if current_state == "start":
                        # enter starts the run from the title screen
                        self.state_machine.transition("playing")
                elif event.key == pg.K_TAB:
                    # manual save hotkey for testing the save system
                    self.save_progress()
                elif event.key == pg.K_r:
                    current_state = self.state_machine.current_state.get_state_name()
                    if current_state == "game_won" or current_state == "game_over":
                        # R only restarts from finished states, so gameplay cannot be reset by accident mid-run
                        self.restart_from_title()


    
    

            

                    

    

    def update(self):
        # lets the active game-flow state decide what should update this frame
        # the state machine controls whether gameplay runs, pauses, or waits on a menu
        self.state_machine.update()
        # self.all_sprites.update() #updating sprites for dynamics (movement of player)
        # if self.camera is not None: #if the camera exists
        #     self.camera.update(self.player) #the camera is updating for player, so it locks onto player
        
    def draw(self):
        self.screen.fill(BLUE)  # screen color
        # current_state is used to decide whether to draw the world, HUD, or only menu text
        current_state = self.state_machine.current_state.get_state_name()
        # self.draw_text("Hello World", 24, WHITE, WIDTH / 2, TILESIZE)  # calling of draw text
        # self.draw_text(str(self.dt), 24, WHITE, WIDTH / 2, HEIGHT / 4)  # calling of draw text
        # self.draw_text(str(self.game_cooldown.ready()), 24, WHITE, WIDTH / 2, HEIGHT / 3) # calling of draw text
        # self.draw_text(str(self.player.pos), 24, WHITE, WIDTH / 2, HEIGHT-TILESIZE*3) # calling of draw text
        
        if current_state != "start":
            # world sprites are drawn before HUD so health and sprint text stay visible on top
            for sprite in self.all_sprites: #looks through all sprites
                self.screen.blit(sprite.image, self.camera.apply(sprite)) #for each sprite, replace the image with it's image AND apply the camera to it
            # red vignette is drawn over the world before HUD text so damage is visible without hiding the UI
            self.draw_damage_vignette()
            draw_health_bar(self.screen, 10, 10, self.player.health) # draw overlay text after the world so state-specific UI appears on top
            # sprint timer is part of the HUD layer, so it renders after the world just like the health bar
            self.draw_sprint_timer()
        
        if current_state == "paused":
            self.draw_text("PAUSED", 48, WHITE, WIDTH / 2, HEIGHT / 2 - 24)

        if current_state == "game_over":
            # game over replaces the whole screen with red so the fail state is immediately obvious
            self.screen.fill(RED)
            self.draw_text("GAME OVER", 48, BLACK, WIDTH / 2, HEIGHT / 2 - 24)
            self.draw_text("Press R to restart", 24, BLACK, WIDTH / 2, HEIGHT / 2 + 30)
        
        if current_state == "start":
            # start screen intentionally skips world drawing so no map sprites show behind the title
            self.draw_text("VANTABLADE", 64, WHITE, WIDTH / 2, HEIGHT / 3)
            self.draw_text("Press ENTER to start", 28, WHITE, WIDTH / 2, HEIGHT / 2)
        if current_state == "game_won":
            # win screen keeps the restart prompt consistent with the game over screen
            self.draw_text("YOU WIN", 48, WHITE, WIDTH / 2, HEIGHT / 2 - 24)
            self.draw_text("Press R to restart", 24, WHITE, WIDTH / 2, HEIGHT / 2 + 30)


        pg.display.flip()

    def draw_damage_vignette(self):
        # missing health controls how strong the edge effect becomes
        damage_pct = max(0, min(100, 100 - self.player.health)) / 100
        if damage_pct <= 0:
            return

        # alpha controls visibility while thickness controls how far the red edges grow inward
        alpha = int(170 * damage_pct)
        thickness = int(160 * damage_pct)
        vignette = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)

        # draw four transparent red edge rectangles to fake a simple damage vignette
        pg.draw.rect(vignette, (255, 0, 0, alpha), (0, 0, WIDTH, thickness))
        pg.draw.rect(vignette, (255, 0, 0, alpha), (0, HEIGHT - thickness, WIDTH, thickness))
        pg.draw.rect(vignette, (255, 0, 0, alpha), (0, 0, thickness, HEIGHT))
        pg.draw.rect(vignette, (255, 0, 0, alpha), (WIDTH - thickness, 0, thickness, HEIGHT))
        self.screen.blit(vignette, (0, 0))

    def draw_sprint_timer(self):
        # picks a different HUD message depending on whether sprint is active, cooling down, or ready
        if self.player.sprinting:
            remaining_ms = max(0, SPRINT_DURATION - (pg.time.get_ticks() - self.player.sprint_start_time))
            sprint_text = f"Sprint: {remaining_ms / 1000:.1f}s"
        elif self.player.sprint_cooling_down:
            remaining_ms = max(0, SPRINT_RESET_TIME - (pg.time.get_ticks() - self.player.sprint_reset_cd.start_time))
            sprint_text = f"Sprint CD: {remaining_ms / 1000:.1f}s"
        else:
            sprint_text = "Sprint: READY"

        # draws the sprint status in the top-right corner so the player can track the timer mid-run
        font_name = pg.font.match_font("arial")
        font = pg.font.Font(font_name, 24)
        text_surface = font.render(sprint_text, True, WHITE)
        text_rect = text_surface.get_rect()
        text_rect.topright = (WIDTH - 10, 10)
        self.screen.blit(text_surface, text_rect)

    def draw_text(self, text, size, color, x, y):  # function that draws text on the screen
        # create a font object for the requested size each time text needs to be drawn
        font_name = pg.font.match_font("arial") #font
        font = pg.font.Font(font_name, size)
        # render returns a surface containing the visible text pixels
        text_surface = font.render(text, True, color) #actually puts it on screen
        text_rect = text_surface.get_rect() #makes it a rect
        text_rect.midtop = (x, y) #pos of text
        self.screen.blit(text_surface, text_rect)


if __name__ == "__main__":
    g = Game() #instanciates game class, so it can be used
    g.new()
    g.run()
    pg.quit()
