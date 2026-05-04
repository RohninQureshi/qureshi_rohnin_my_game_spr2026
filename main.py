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
__updated__ = '2026-04-30 14:29:22'


import pygame as pg
import sys
from random import *
import os
from settings import *
from sprites import *
from utils import *
from state_machine import StateMachine
from states.game_states import *
from bosses.boss_registry import BOSS_SPAWN_TABLE
from tile_registry import TILE_SPAWN_TABLE, spawn_boss
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
        self.boss_damage_cd = Cooldown(SENTINEL_CONTACT_COOLDOWN)
        # boss contact damage should also be ready as soon as a boss fight starts
        self.boss_damage_cd.start_time = -SENTINEL_CONTACT_COOLDOWN
        # these level fields are set before loading data so saves can change the starting level
        self.camera = None
        self.current_level_index = 0
        # settings_previous_state works like a back button for settings opened from start or pause
        self.settings_previous_state = "start"
        self.settings_selected = 0
        self.music_volume = 0.5
        self.sfx_volume = 0.5
        # run progression is stored on Game so stats can survive between level rebuilds
        self.reset_player_progression()
        # keybinds keep controls in one place so the settings menu can change them
        self.keybinds = {
            "jump": pg.K_w,
            # aim_up is separate from jump so the player can jump without forcing shots upward
            "aim_up": pg.K_UP,
            "down": pg.K_s,
            "left": pg.K_a,
            "right": pg.K_d,
            # dash starts as left control, but it stays rebindable like the other gameplay actions
            "dash": pg.K_LCTRL,
            "sprint": pg.K_LSHIFT,
            "shoot": pg.K_f,
            "pause": pg.K_p,
            "settings": pg.K_o,
        }
        # these are the controls the player is allowed to change from the settings menu
        self.rebindable_actions = ["jump", "aim_up", "down", "left", "right", "dash", "sprint", "shoot", "pause", "settings"]
        # labels are separate from keybinds so the menu can show readable names instead of code keys
        self.keybind_labels = {
            "jump": "Jump",
            "aim_up": "Aim Up",
            "down": "Aim Down",
            "left": "Move Left",
            "right": "Move Right",
            # dash gets its own row in settings so players can tune movement controls without editing code
            "dash": "Dash",
            "sprint": "Sprint",
            "shoot": "Shoot",
            "pause": "Pause",
            "settings": "Settings",
        }
        # special display names keep the settings menu readable for non-letter keys
        self.special_key_names = {
            pg.K_RETURN: "ENTER",
            pg.K_SPACE: "SPACE",
            pg.K_LSHIFT: "LEFT SHIFT",
            pg.K_RSHIFT: "RIGHT SHIFT",
            pg.K_LCTRL: "LEFT CTRL",
            pg.K_RCTRL: "RIGHT CTRL",
            pg.K_UP: "UP ARROW",
            pg.K_DOWN: "DOWN ARROW",
            pg.K_LEFT: "LEFT ARROW",
            pg.K_RIGHT: "RIGHT ARROW",
            pg.K_ESCAPE: "ESC",
            pg.K_TAB: "TAB",
        }
        # None means the settings menu is not waiting for a new key press
        self.rebinding_action = None
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
            GameSettingsState(self),
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
        return {
            "timestamp": datetime.now().isoformat(),
            "current_level_index": self.current_level_index,
            "current_level_file": self.levels[self.current_level_index],
            # volume settings are saved with progress so they persist after closing the game
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            # key constants are integers, so they can be written directly into json
            "keybinds": self.keybinds,
            # progression values are simple numbers, so they can be restored before a player object exists
            "player_armor": self.player_armor,
            "player_weapon_damage": self.player_weapon_damage,
            "player_max_ammo": self.player_max_ammo,
            "player_ammo": self.player_ammo,
        }

    def save_progress(self):
        # writes a new timestamped save file, then removes older extras
        # copy live player stats first so closing mid-level saves current ammo, armor, and damage
        self.store_player_progression()
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

    def quit_game(self):
        # one quit helper keeps window close and Escape from having different save behavior
        # saving here means normal exits remember the latest level, settings, keybinds, and progression
        self.save_progress()

        # stop the inner gameplay loop first, then stop the outer application loop
        if self.playing:
            self.playing = False
        self.running = False

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

        # only use the saved level if it still exists, so broken saves cannot crash the game
        if 0 <= saved_index < len(self.levels):
            self.current_level_index = saved_index

        # older save files may not have settings yet, so defaults stay if a key is missing
        self.music_volume = max(0, min(1, data.get("music_volume", self.music_volume)))
        self.sfx_volume = max(0, min(1, data.get("sfx_volume", self.sfx_volume)))

        saved_keybinds = data.get("keybinds", {})
        for action in self.rebindable_actions:
            # only restore known actions so a bad save cannot add random controls
            # isinstance protects against save files where a key value is missing or not a pygame key number
            if action in saved_keybinds and isinstance(saved_keybinds[action], int):
                self.keybinds[action] = saved_keybinds[action]

        # restore progression if this save was made after the progression system was added
        self.player_armor = data.get("player_armor", self.player_armor)
        self.player_weapon_damage = data.get("player_weapon_damage", self.player_weapon_damage)
        self.player_max_ammo = data.get("player_max_ammo", self.player_max_ammo)
        self.player_ammo = min(data.get("player_ammo", self.player_ammo), self.player_max_ammo)

        # apply restored volume values to the already-loaded pygame sound objects
        self.apply_audio_settings()

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
        # apply saved/default volume settings as soon as sounds are loaded
        self.pickup_snd.set_volume(self.sfx_volume)
        pg.mixer.music.set_volume(self.music_volume)
        # load the current level immediately so the first call to new() can build the map
        self.map = Map(path.join(self.level_dir, self.levels[self.current_level_index]))

    def apply_audio_settings(self):
        # applies current volume variables to pygame's music channel and sound effects
        pg.mixer.music.set_volume(self.music_volume)
        self.pickup_snd.set_volume(self.sfx_volume)

    def load_current_level(self):
        # reloads the map whenever the current level index changes
        # this method is reused by loading saves, restarting, and moving to the next level
        self.map = Map(path.join(self.level_dir, self.levels[self.current_level_index]))

    def reset_player_progression(self):
        # starting a new run resets progression, but moving to the next level does not
        self.player_armor = PLAYER_STARTING_ARMOR
        self.player_weapon_damage = PLAYER_STARTING_WEAPON_DAMAGE
        self.player_max_ammo = PLAYER_MAX_AMMO
        self.player_ammo = PLAYER_MAX_AMMO

    def store_player_progression(self):
        # copy current player stats back to Game before rebuilding the level sprites
        if not hasattr(self, "player"):
            return

        self.player_armor = self.player.armor
        self.player_weapon_damage = self.player.weapon_damage
        self.player_max_ammo = self.player.max_ammo
        self.player_ammo = self.player.ammo

    def next_level(self):
        # advances to the next level if one exists, otherwise transitions to the win state
        if self.current_level_index < len(self.levels) - 1:
            # keep ammo and upgrades from the old player before the new level creates a fresh Player
            self.store_player_progression()
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
        # restarting from title resets ammo, armor, and weapon damage back to starting values
        self.reset_player_progression()
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
        self.all_bosses = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        self.all_powerups = pg.sprite.Group()
        self.all_projectiles = pg.sprite.Group()
        self.all_boss_projectiles = pg.sprite.Group()
        # particles are grouped separately so they can be added without changing gameplay collision groups
        self.all_particles = pg.sprite.Group()
        # afterimages are separate so they can be drawn behind normal sprites
        self.all_afterimages = pg.sprite.Group()
        # damage numbers are lightweight dictionaries because they only need text, position, and age
        self.damage_numbers = []
        self.boss = None
        
        self.camera = Camera(self.map.width, self.map.height) #Actually instanciates the  camera
        
        for row, tiles in enumerate(self.map.data): #this section of code loads the entities (wall,player,mobs) based upon the map data we made (level1.txt), by enumerating through each cahrecter, and looking at it's value and pos.
            for col, tile, in enumerate(tiles):
                # tile_registry.py owns what each normal level character means
                # this keeps main.py focused on loading the map instead of knowing every object class
                if tile in TILE_SPAWN_TABLE:
                    TILE_SPAWN_TABLE[tile](self, col, row)
                elif tile in BOSS_SPAWN_TABLE:
                    # boss letters stay in the boss registry because each boss has its own module and states
                    spawn_boss(self, col, row, tile)
        # every fresh level rebuild gives the player full health for a clean level start
        self.player.health = 100
        # progression stats come from Game, so ammo does not reset when entering the next level
        self.player.apply_progression(self.player_armor, self.player_weapon_damage, self.player_max_ammo, self.player_ammo)
        # restarting the level also restarts the background music loop for a clean reset
        pg.mixer.music.load(path.join(self.snd_dir, "background_soundtrack.mp3"))
        pg.mixer.music.set_volume(self.music_volume)
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
                # closing the window uses the same save-and-quit path as the keyboard quit shortcut
                self.quit_game()

            elif event.type == pg.KEYDOWN:
                current_state = self.state_machine.current_state.get_state_name()

                if current_state == "settings" and self.rebinding_action is not None:
                    # while rebinding, this key press should only edit controls, not trigger normal commands
                    if event.key == pg.K_ESCAPE:
                        # escape cancels rebinding so the player is not forced to choose a key
                        self.rebinding_action = None
                    else:
                        # the next key pressed becomes the new key for the selected action
                        self.keybinds[self.rebinding_action] = event.key
                        self.rebinding_action = None
                        # save immediately so changed controls persist next time the game opens
                        self.save_progress()
                    continue

                # menu states are handled first so hardcoded menu controls cannot be blocked by a rebind
                if current_state == "start":
                    if event.key == pg.K_ESCAPE:
                        # escape still acts as a quit shortcut from the title screen
                        self.quit_game()
                    elif event.key == pg.K_RETURN:
                        # start screen always uses Enter, even if Enter is rebound to another action
                        self.state_machine.transition("playing")
                    elif event.key == self.keybinds["settings"]:
                        # settings can still be opened from the title with the player's chosen key
                        self.settings_previous_state = current_state
                        self.state_machine.transition("settings")
                    continue

                if current_state == "settings":
                    if event.key == pg.K_ESCAPE:
                        # escape from settings returns to the menu state that opened it
                        self.state_machine.transition(self.settings_previous_state)
                    elif event.key == pg.K_RETURN and self.settings_selected >= 2:
                        # selecting a keybind option starts waiting for the next key press
                        # subtract 2 because the first two menu rows are volume settings
                        action_index = self.settings_selected - 2
                        self.rebinding_action = self.rebindable_actions[action_index]
                    elif event.key == pg.K_UP:
                        # wrap selection upward through the settings options
                        self.settings_selected = (self.settings_selected - 1) % self.settings_option_count()
                    elif event.key == pg.K_DOWN:
                        # wrap selection downward through the settings options
                        self.settings_selected = (self.settings_selected + 1) % self.settings_option_count()
                    elif event.key == pg.K_LEFT:
                        # left lowers the selected setting value
                        self.change_setting(-0.05)
                    elif event.key == pg.K_RIGHT:
                        # right raises the selected setting value
                        self.change_setting(0.05)
                    continue

                if event.key == pg.K_ESCAPE:
                    # outside settings, escape is treated as a full quit shortcut
                    self.quit_game()
                elif event.key == self.keybinds["pause"]: #transition into or out of pause state
                    # pause only toggles between the two gameplay-related states
                    if current_state == "playing":
                        self.state_machine.transition("paused")
                    elif current_state == "paused":
                        self.state_machine.transition("playing")

                elif event.key == self.keybinds["settings"]:
                    if current_state == "paused":
                        # remember where settings was opened so ESC can return to the correct screen
                        self.settings_previous_state = current_state
                        self.state_machine.transition("settings")

                elif event.key == pg.K_TAB:
                    # manual save hotkey for testing the save system
                    self.save_progress()
                elif event.key == pg.K_r:
                    if current_state == "game_won" or current_state == "game_over":
                        # R only restarts from finished states, so gameplay cannot be reset by accident mid-run
                        self.restart_from_title()


    
    

            

                    

    

    def update(self):
        # lets the active game-flow state decide what should update this frame
        # the state machine controls whether gameplay runs, pauses, or waits on a menu
        self.state_machine.update()
        # damage numbers are not sprites, so they need their own update step
        self.update_damage_numbers()
        # self.all_sprites.update() #updating sprites for dynamics (movement of player)
        # if self.camera is not None: #if the camera exists
        #     self.camera.update(self.player) #the camera is updating for player, so it locks onto player

    def damage_player(self, amount):
        # armor reduces incoming damage, but damage never drops below 1
        final_damage = max(1, amount - self.player.armor)
        self.player.health -= final_damage
        return final_damage

    def add_damage_number(self, world_pos, amount, color):
        # stores floating combat text in world coordinates so the camera moves it with the level
        # each number tracks its own position and age instead of being a full pygame sprite
        self.damage_numbers.append({
            "text": str(amount),
            "pos": pg.math.Vector2(world_pos) + pg.math.Vector2(randint(-10, 10), -12),
            "age": 0,
            "color": color,
        })

    def update_damage_numbers(self):
        # skip safely before the first level has created the damage number list
        if not hasattr(self, "damage_numbers"):
            return

        for number in self.damage_numbers:
            # age is stored in milliseconds to match the rest of pygame timing in this project
            number["age"] += self.dt * 1000
            # floating upward makes the number readable without covering the hit target for long
            number["pos"].y -= DAMAGE_NUMBER_RISE_SPEED * self.dt

        # keep only numbers that are still inside their visible lifetime
        self.damage_numbers = [
            number for number in self.damage_numbers
            if number["age"] < DAMAGE_NUMBER_LIFETIME
        ]

    def draw_damage_numbers(self):
        # damage numbers are drawn after sprites so they stay visible above enemies and particles
        if not hasattr(self, "damage_numbers") or self.camera is None:
            return

        font_name = pg.font.match_font("arial")
        font = pg.font.Font(font_name, 22)
        for number in self.damage_numbers:
            # fade out near the end so numbers disappear smoothly instead of popping off
            alpha = max(0, 255 - int(255 * number["age"] / DAMAGE_NUMBER_LIFETIME))
            text_surface = font.render(number["text"], True, number["color"])
            text_surface.set_alpha(alpha)
            text_rect = text_surface.get_rect()
            text_rect.center = self.camera.apply_point(number["pos"])
            self.screen.blit(text_surface, text_rect)

    def spawn_hit_particles(self, world_pos, color, count):
        # particles are spawned through Game so combat code does not need to manage sprite groups directly
        if not hasattr(self, "all_particles"):
            return

        for _ in range(count):
            HitParticle(self, world_pos[0], world_pos[1], color)

    def spawn_afterimage(self, image, rect):
        # afterimages are faded copies of the real sprite image at an old position
        # the image and rect are copied by AfterImage so the original sprite can keep moving normally
        if not hasattr(self, "all_afterimages"):
            return

        AfterImage(self, image, rect)
        
    def draw(self):
        self.screen.fill(BLUE)  # screen color
        # current_state is used to decide whether to draw the world, HUD, or only menu text
        current_state = self.state_machine.current_state.get_state_name()
        # self.draw_text("Hello World", 24, WHITE, WIDTH / 2, TILESIZE)  # calling of draw text
        # self.draw_text(str(self.dt), 24, WHITE, WIDTH / 2, HEIGHT / 4)  # calling of draw text
        # self.draw_text(str(self.game_cooldown.ready()), 24, WHITE, WIDTH / 2, HEIGHT / 3) # calling of draw text
        # self.draw_text(str(self.player.pos), 24, WHITE, WIDTH / 2, HEIGHT-TILESIZE*3) # calling of draw text
        
        if current_state != "start":
            # boss warnings draw under sprites so danger zones are readable without covering characters
            self.draw_boss_warnings()
            # afterimages draw before real sprites so they look like a trail behind motion
            for afterimage in self.all_afterimages:
                self.screen.blit(afterimage.image, self.camera.apply(afterimage))
            # world sprites are drawn before HUD so health and sprint text stay visible on top
            for sprite in self.all_sprites: #looks through all sprites
                self.screen.blit(sprite.image, self.camera.apply(sprite)) #for each sprite, replace the image with it's image AND apply the camera to it
            # floating damage text draws above the world but below the main HUD
            self.draw_damage_numbers()
            # red vignette is drawn over the world before HUD text so damage is visible without hiding the UI
            self.draw_damage_vignette()
            draw_health_bar(self.screen, 10, 10, self.player.health) # draw overlay text after the world so state-specific UI appears on top
            # sprint timer is part of the HUD layer, so it renders after the world just like the health bar
            self.draw_movement_timers()
            self.draw_progression_hud()
            self.draw_boss_health_bar()
        
        if current_state == "paused":
            self.draw_text("PAUSED", 48, WHITE, WIDTH / 2, HEIGHT / 2 - 24)
            self.draw_text(f"Press {self.key_name_for('settings')} for settings", 24, WHITE, WIDTH / 2, HEIGHT / 2 + 35)
            

        if current_state == "game_over":
            # game over replaces the whole screen with red so the fail state is immediately obvious
            self.screen.fill(RED)
            self.draw_text("GAME OVER", 48, BLACK, WIDTH / 2, HEIGHT / 2 - 24)
            self.draw_text("Press R to restart", 24, BLACK, WIDTH / 2, HEIGHT / 2 + 30)
        
        if current_state == "start":
            # start screen intentionally skips world drawing so no map sprites show behind the title
            self.draw_text("VANTABLADE", 64, WHITE, WIDTH / 2, HEIGHT / 3)
            self.draw_text("Press ENTER to start", 28, WHITE, WIDTH / 2, HEIGHT / 2)
            self.draw_text(f"Press {self.key_name_for('settings')} for settings", 24, WHITE, WIDTH / 2, HEIGHT / 2 + 40)
        if current_state == "game_won":
            # win screen keeps the restart prompt consistent with the game over screen
            self.draw_text("YOU WIN", 48, WHITE, WIDTH / 2, HEIGHT / 2 - 24)
            self.draw_text("Press R to restart", 24, WHITE, WIDTH / 2, HEIGHT / 2 + 30)

        if current_state == "settings":
            # settings draws last so it covers the start screen or paused gameplay underneath
            self.draw_settings_menu()

        pg.display.flip()

    def key_name_for(self, action):
        # special keys get custom labels so the settings screen says ENTER instead of RETURN, etc.
        key = self.keybinds[action]
        if key in self.special_key_names:
            return self.special_key_names[key]
        return pg.key.name(key).upper()

    def settings_option_count(self):
        # two volume settings plus every rebindable control option
        return 2 + len(self.rebindable_actions)

    def change_setting(self, amount):
        # selected index 0 controls music volume, clamped between 0 and 1
        if self.settings_selected == 0:
            self.music_volume = max(0, min(1, self.music_volume + amount))
            pg.mixer.music.set_volume(self.music_volume)
            # save immediately so volume changes persist next time the game opens
            self.save_progress()
        # selected index 1 controls sound effect volume, also clamped between 0 and 1
        elif self.settings_selected == 1:
            self.sfx_volume = max(0, min(1, self.sfx_volume + amount))
            self.pickup_snd.set_volume(self.sfx_volume)
            # save immediately so sound effect volume changes persist next time the game opens
            self.save_progress()

    def draw_slider(self, label, value, x, y, selected):
        # sliders show volume as both a percent number and a visual bar
        color = YELLOW if selected else WHITE
        self.draw_text(f"{label}: {int(value * 100)}%", 28, color, x, y)

        # bar_rect is the full slider range from 0 percent to 100 percent
        bar_width = 300
        bar_height = 8
        bar_rect = pg.Rect(0, 0, bar_width, bar_height)
        bar_rect.center = (x, y + 45)

        # filled_rect represents the active part of the slider based on the current value
        filled_rect = pg.Rect(bar_rect.left, bar_rect.top, int(bar_rect.width * value), bar_rect.height)

        # handle_x converts the 0.0 to 1.0 volume value into a screen x coordinate
        handle_x = bar_rect.left + int(bar_rect.width * value)
        handle_rect = pg.Rect(0, 0, 16, 24)
        handle_rect.center = (handle_x, bar_rect.centery)

        # draw order matters: background first, fill second, handle last
        pg.draw.rect(self.screen, WHITE, bar_rect, 2)
        pg.draw.rect(self.screen, YELLOW if selected else RED, filled_rect)
        pg.draw.rect(self.screen, color, handle_rect)

    def draw_boss_health_bar(self):
        # only draw the boss bar while a living boss exists in the current level
        if self.boss is None or not self.boss.alive():
            return

        bar_width = 500
        bar_height = 16
        x = WIDTH / 2 - bar_width / 2
        y = 45
        health_pct = max(0, self.boss.health) / self.boss.max_health
        outline_rect = pg.Rect(x, y, bar_width, bar_height)
        fill_rect = pg.Rect(x, y, bar_width * health_pct, bar_height)

        # display_name lets different bosses reuse the same HUD code without hardcoding their names here
        self.draw_text(self.boss.display_name, 24, WHITE, WIDTH / 2, 15)
        pg.draw.rect(self.screen, RED, fill_rect)
        pg.draw.rect(self.screen, WHITE, outline_rect, 2)

    def draw_boss_warnings(self):
        # this method draws boss attack telegraphs that are not normal sprites
        # it stays in main.py because warnings are screen/camera overlays, not physical level objects
        if self.boss is None or not self.boss.alive() or self.camera is None:
            return

        # Sentinel ground pound is currently the only boss attack with a floor warning
        # hasattr keeps this safe for future bosses that do not use pound_target_x or mode
        if not hasattr(self.boss, "mode") or not hasattr(self.boss, "pound_target_x"):
            return

        if self.boss.mode not in ("ground_pound_lock", "ground_pound_warn"):
            return

        # the warning column shows the full dangerous lane where the ground pound can hit
        warning_width = SENTINEL_POUND_RADIUS * 2
        warning_height = self.map.height - TILESIZE * 2
        warning_rect = pg.Rect(0, TILESIZE, warning_width, warning_height)
        warning_rect.centerx = self.boss.pound_target_x

        if self.boss.mode == "ground_pound_lock":
            # yellow means the target is still tracking the player and is not locked yet
            warning_color = (255, 255, 0)
            warning_alpha = 55
        else:
            # red opacity works like a visual timer: higher alpha means the drop is closer
            elapsed = pg.time.get_ticks() - self.boss.mode_start_time
            progress = min(1, elapsed / SENTINEL_POUND_WARN_TIME)
            warning_color = (255, 0, 0)
            warning_alpha = int(45 + progress * 185)

        # draw on a transparent screen-sized layer so off-screen warning rectangles are clipped safely
        warning_layer = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        screen_rect = warning_rect.move(self.camera.camera.topleft)
        pg.draw.rect(warning_layer, (*warning_color, warning_alpha), screen_rect)

        # outline is slightly stronger than the fill so the danger edge is readable during motion
        outline_alpha = min(255, warning_alpha + 45)
        pg.draw.rect(warning_layer, (*warning_color, outline_alpha), screen_rect, 3)
        self.screen.blit(warning_layer, (0, 0))

    def draw_settings_menu(self):
        # settings gets a plain screen so it is readable from both title and pause
        self.screen.fill(BLACK)
        self.draw_text("SETTINGS", 56, WHITE, WIDTH / 2, HEIGHT / 8)

        # volume options get drawn as sliders, but still use LEFT/RIGHT to change values
        self.draw_slider("Music Volume", self.music_volume, WIDTH / 2, HEIGHT / 4, self.settings_selected == 0)
        self.draw_slider("SFX Volume", self.sfx_volume, WIDTH / 2, HEIGHT / 4 + 90, self.settings_selected == 1)

        # keybind rows are compact so the controls guide can stay readable at the bottom
        keybind_start_y = HEIGHT / 4 + 150
        keybind_spacing = 25
        for index, action in enumerate(self.rebindable_actions):
            # menu_index accounts for the two volume rows before the keybind rows
            menu_index = index + 2
            label = self.keybind_labels[action]
            option = f"{label}: {self.key_name_for(action)}"
            color = YELLOW if menu_index == self.settings_selected else WHITE
            self.draw_text(option, 22, color, WIDTH / 2, keybind_start_y + index * keybind_spacing)

        if self.rebinding_action is not None:
            # this message sits above the controls guide so it does not overlap the settings list
            label = self.keybind_labels[self.rebinding_action]
            self.draw_text(f"Press a new key for {label}", 24, YELLOW, WIDTH / 2, HEIGHT - 150)

        # controls are shown directly on the menu so the player knows how to use it
        self.draw_text("UP/DOWN to select", 22, WHITE, WIDTH / 2, HEIGHT - 120)
        self.draw_text("LEFT/RIGHT for volume, ENTER to change keybinds", 22, WHITE, WIDTH / 2, HEIGHT - 90)
        self.draw_text("ESC to go back", 22, WHITE, WIDTH / 2, HEIGHT - 60)

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

    def draw_movement_timers(self):
        # sprint message changes depending on whether sprint is active, cooling down, or ready
        if self.player.sprinting:
            remaining_ms = max(0, SPRINT_DURATION - (pg.time.get_ticks() - self.player.sprint_start_time))
            sprint_text = f"Sprint: {remaining_ms / 1000:.1f}s"
        elif self.player.sprint_cooling_down:
            remaining_ms = max(0, SPRINT_RESET_TIME - (pg.time.get_ticks() - self.player.sprint_reset_cd.start_time))
            sprint_text = f"Sprint CD: {remaining_ms / 1000:.1f}s"
        else:
            sprint_text = "Sprint: READY"

        # dash has its own cooldown readout so the player knows when the dodge burst is ready again
        if self.player.dashing:
            remaining_ms = max(0, DASH_DURATION - (pg.time.get_ticks() - self.player.dash_start_time))
            dash_text = f"Dash: {remaining_ms / 1000:.2f}s"
        elif self.player.dash_cd.ready():
            dash_text = "Dash: READY"
        else:
            remaining_ms = max(0, DASH_COOLDOWN - (pg.time.get_ticks() - self.player.dash_cd.start_time))
            dash_text = f"Dash CD: {remaining_ms / 1000:.1f}s"

        # movement timers draw in the top-right corner so dash and sprint can be tracked together
        font_name = pg.font.match_font("arial")
        font = pg.font.Font(font_name, 24)
        sprint_surface = font.render(sprint_text, True, WHITE)
        sprint_rect = sprint_surface.get_rect()
        sprint_rect.topright = (WIDTH - 10, 10)
        self.screen.blit(sprint_surface, sprint_rect)

        # dash is drawn on its own line so sprint and dash timers can be read at the same time
        dash_surface = font.render(dash_text, True, WHITE)
        dash_rect = dash_surface.get_rect()
        dash_rect.topright = (WIDTH - 10, 36)
        self.screen.blit(dash_surface, dash_rect)

    def draw_progression_hud(self):
        # ammo, armor, and weapon damage sit under the movement timers so progression is always visible
        font_name = pg.font.match_font("arial")
        font = pg.font.Font(font_name, 22)
        hud_lines = [
            f"Ammo: {self.player.ammo}/{self.player.max_ammo}",
            f"Armor: {self.player.armor}",
            f"Damage: {self.player.weapon_damage}",
        ]

        for index, line in enumerate(hud_lines):
            text_surface = font.render(line, True, WHITE)
            text_rect = text_surface.get_rect()
            text_rect.topright = (WIDTH - 10, 68 + index * 24)
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
