import pygame as pg
from pygame.sprite import Sprite
from settings import *
from utils import *
import sys
from os import path
from ctypes import Array
from player_states import *
from state_machine import *


vec = pg.math.Vector2 #using vectors


def collide_hit_rect(one, two):  #creating a function so that all classes can use this function, checks for collision between 2 entities, one and two, part of git library
    # hit_rect is used instead of rect so collision can stay stable even if animation frames change size
    return one.hit_rect.colliderect(two.rect)

def collide_with_walls(sprite, group, dir): # A function that checks for collision on the x and y plane, and does physics based on it
    if dir == 'x': #checks for dir (only does x)
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            # print("collided with wall in the x dir")
            if hits[0].rect.centerx > sprite.hit_rect.centerx: #if the first item in the list of things that collided's center pos is greater then the sprite we are checking (player) y-dir
                sprite.pos.x = hits[0].rect.left - sprite.hit_rect.width/2 #the pos of sprite (player) will bounce off to the left by a factor of the hitbox of the thing it collided with - player's hitbox divided by 2
            if hits[0].rect.centerx < sprite.hit_rect.centerx: #if the first item in the list of things that collided's center pos is less then the sprite we are checking (player) y-dir
                sprite.pos.x = hits[0].rect.right + sprite.hit_rect.width/2 #the pos of sprite (player) will bounce off to the right by a factor of the hitbox of the thing it collided with - player's hitbox divided by 2
            sprite.vel.x = 0 #setting the original velocity to 0
            sprite.hit_rect.centerx = sprite.pos.x # setting the center of the player to be the position
    if dir == 'y': #checks for dir (only does y)
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            # print("collided with wall in the y dir")
            if sprite.vel.y > 0 and hits[0].rect.centery > sprite.hit_rect.centery: #only count as landing if the sprite was falling onto the tile
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height/2 #move the sprite so it stands on top of the tile it landed on
                sprite.on_ground = True
            elif sprite.vel.y < 0 and hits[0].rect.centery < sprite.hit_rect.centery: #if the sprite was moving upward, treat the collision as a head hit instead
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.height/2 #push the sprite back below the tile it hit from underneath
            sprite.vel.y = 0 #setting the original velocity to 0
            sprite.hit_rect.centery = sprite.pos.y # setting the center of the player to be the position
            

# Player sprite class that handles movement, animation, collisions, and player states.
class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_players #group
        Sprite.__init__(self, self.groups)
        # store the game reference so the player can access assets, groups, and global states
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "sprite_sheet.png"))
        self.load_images()
        self.image = pg.Surface((TILESIZE,TILESIZE))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect() #creating rect for vector math
        self.vel = vec(0,0) #velocity
        self.pos = vec(x,y) * TILESIZE #postion
        self.hit_rect = PLAYER_HIT_RECT.copy()
        self.sprinting = False
        self.walking = False
        self.on_ground = False
        self.health = 100
        self.move_dir = 0
        self.jump_pressed = False
        self.down_pressed = False
        self.sprint_held = False
        self.aim_dir = vec(1, 0)
        self.last_update = 0
        self.current_frame = 0
        self.projectile_cd = Cooldown(500)
        self.sprint_reset_cd = Cooldown(SPRINT_RESET_TIME)
        self.sprint_cooling_down = False
        self.sprint_start_time = 0
        # player has its own movement-focused state machine separate from the game-wide one
        self.state_machine = StateMachine()
        self.states: Array[State] = [PlayerIdleState(self), PlayerMoveState(self), PlayerSprintState(self)]
        self.state_machine.start_machine(self.states)

        
    def get_key_movement(self): #function for movement
        self.vel.x = 0 #only reset x movement so gravity can keep affecting y velocity
        # sprint only changes horizontal speed; gravity still owns the y axis
        speed = PLAYER_SPEED
        if self.sprinting:
            speed = PLAYER_SPRINT_SPEED

        if self.move_dir < 0: #move left using the input direction cached earlier this frame
            self.vel.x = -speed
        if self.move_dir > 0:
            self.vel.x = speed
        # jumping only applies when the player is grounded so there is no infinite air jump
        if self.jump_pressed and self.on_ground:
            self.vel.y = JUMP_VELOCITY
            self.on_ground = False

    def get_key_projectile(self): #looking for key press of specific key, and will insanciate a projectile when that key is pressed
        keys = pg.key.get_pressed()
        if keys[pg.K_f]:
            if self.projectile_cd.ready():
                # firing starts the cooldown immediately so holding F cannot spam projectiles every frame
                self.projectile_cd.start()
                # fire from the player's current center using the latest aim direction
                Projectile(self.game, self.rect.centerx, self.rect.centery, self.aim_dir)
    
    def load_images(self):
        # each list stores animation frames for a single player movement state
        self.standing_frames = [self.spritesheet.get_image(0, 0, TILESIZE, TILESIZE), 
                                self.spritesheet.get_image(TILESIZE, 0, TILESIZE, TILESIZE) ]
        self.walking_frames = [self.spritesheet.get_image(0, TILESIZE, TILESIZE, TILESIZE),
                                self.spritesheet.get_image(TILESIZE, TILESIZE, TILESIZE, TILESIZE)]
        self.sprinting_frames = [self.spritesheet.get_image(0, TILESIZE*2, TILESIZE, TILESIZE),
                                self.spritesheet.get_image(TILESIZE, TILESIZE*2, TILESIZE, TILESIZE)]
        for frame in self.standing_frames:
            frame.set_colorkey(BLACK)
        for frame in self.walking_frames:
            frame.set_colorkey(BLACK)
        for frame in self.sprinting_frames:
            # black is treated as transparent so the sprite sheet background does not render in-game
            frame.set_colorkey(BLACK)

    def update_input_flags(self): #read current controls once so the state machine can decide movement state
        keys = pg.key.get_pressed() #gets the keys pressed
        # cache movement intent once here so both the player logic and state logic read the same input
        self.move_dir = 0
        if keys[pg.K_a]:
            self.move_dir -= 1
        if keys[pg.K_d]:
            self.move_dir += 1
        self.jump_pressed = keys[pg.K_w]
        self.down_pressed = keys[pg.K_s]
        self.sprint_held = keys[pg.K_LSHIFT]

        # vertical aim has priority so W can jump and still aim upward, while S aims downward
        if self.jump_pressed:
            self.aim_dir = vec(0, -1)
        elif self.down_pressed:
            self.aim_dir = vec(0, 1)
        elif self.move_dir < 0:
            self.aim_dir = vec(-1, 0)
        elif self.move_dir > 0:
            self.aim_dir = vec(1, 0)

        if self.sprint_cooling_down and self.sprint_reset_cd.ready(): #once cooldown finishes, sprint becomes available again
            # once the cooldown timer reports ready, sprint can be started again
            self.sprint_cooling_down = False

    def wants_to_move(self): #movement states use this to determine whether the player intends to move horizontally
        return self.move_dir != 0

    def wants_to_sprint(self): #sprint can only start while moving and while its reset cooldown is inactive
        return self.sprint_held and self.wants_to_move() and not self.sprint_cooling_down

    def start_sprint(self): #called by the sprint state when sprinting begins
        if not self.sprinting:
            # starting sprint flips the state flag and stores the exact time so duration can be measured later
            self.sprinting = True
            self.walking = True
            self.sprint_start_time = pg.time.get_ticks()

    def stop_sprint(self): #called when leaving sprint so cooldown begins cleanly once
        if self.sprinting:
            # stopping sprint immediately starts the reset cooldown so sprint cannot be reused right away
            self.sprinting = False
            self.sprint_cooling_down = True
            self.sprint_reset_cd.start()

    def should_keep_sprinting(self): #active sprint ends when its duration expires or input is released
        if not self.sprinting:
            return False
        if not self.sprint_held:
            return False
        # compares the live clock against sprint_start_time to decide whether the sprint window is still active
        return pg.time.get_ticks() - self.sprint_start_time < SPRINT_DURATION

    def animate(self): #I made my spritesheet differently, making each row a state, rather then a charencter or thing
        now = pg.time.get_ticks() #gets current time
        if not self.sprinting and not self.walking: #only while static, need to update self.walking and self.jumping
            if now - self.last_update > 350: #cooldown for sprite update, 350 milliseconds per frame
                self.last_update = now #updates now
                self.current_frame = (self.current_frame + 1) % len(self.standing_frames) #this line iterates through all frames, and if you are on the last one, it goes back to the beginning
                # keep the rect centered when swapping images so animation does not shift the player visually
                center = self.rect.center
                self.image = self.standing_frames[self.current_frame] #sets the current image to be that frame
                self.rect = self.image.get_rect()
                self.rect.center = center
        
        if self.walking and not self.sprinting: #only when walking, works the same as standing frames
            if now - self.last_update > 350: #cooldown for sprite update, 350 milliseconds per frame
                self.last_update = now #updates now
                self.current_frame = (self.current_frame + 1) % len(self.walking_frames) #this line iterates through all frames, and if you are on the last one, it goes back to the beginning
                # re-center after the frame change so collision and rendering stay aligned
                center = self.rect.center
                self.image = self.walking_frames[self.current_frame] #sets the current image to be that frame
                self.rect = self.image.get_rect()
                self.rect.center = center
        if self.sprinting and self.walking: #only when sprinting, use the sprinting animation row
            if now - self.last_update > 200: #slightly faster frame timing helps sprinting read visually
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.sprinting_frames)
                # sprint animation also preserves center so faster frames do not cause visible jitter
                center = self.rect.center
                self.image = self.sprinting_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.center = center

    def update(self): #frame-by-frame player update for movement, physics, and objective checks
        self.update_input_flags() #refresh player input before the state machine decides how to move
        self.state_machine.update() #the player state machine now replaces the old state() method
        # input intent is turned into actual velocity after the state machine sets sprint / walk state
        self.get_key_movement()
        self.get_key_projectile()

        self.vel.y += GRAVITY * self.game.dt #gravity only affects vertical speed
        if self.vel.y > MAX_FALL_SPEED:
            self.vel.y = MAX_FALL_SPEED

        # horizontal motion is resolved first so wall collisions are stable before the vertical pass
        self.pos.x += self.vel.x * self.game.dt
        self.hit_rect.centerx = self.pos.x #recentering hitbox
        collide_with_walls(self, self.game.all_walls, 'x') #loading collide with walls for x

        self.on_ground = False #reset grounded state before checking vertical collision this frame
        # the vertical pass applies gravity, landing, and head collisions separately from horizontal movement
        self.pos.y += self.vel.y * self.game.dt
        self.hit_rect.centery = self.pos.y #recentering hitbox
        collide_with_walls(self, self.game.all_walls, 'y') #loading collide with walls for y
        self.rect.center = self.hit_rect.center # centering hitbox again to the regular visual center
        self.animate()

        c_hits = pg.sprite.spritecollide(self,self.game.all_coins,True)
        if c_hits:
            # coin pickup belongs to the game-wide flow, so it triggers the game state machine
            self.game.pickup_snd.play()
            self.game.state_machine.transition("level_clear")

            

        
# Enemy sprite class that currently moves toward the player. Will soon use pathfinding to hunt player
class Mob(Sprite): 
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_mobs #group
        Sprite.__init__(self, self.groups)
        # mobs use the same vector-based position and collision pattern as the player
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(RED) #only difference from player, the color
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.hit_rect = MOB_HIT_RECT

    def update(self): 
        # current mob logic is placeholder movement and still needs to be replaced by real AI
        self.pos += self.game.player.pos*self.game.dt 
        self.rect.center = self.pos
        # keep the same collision pass order so mobs obey solid walls too
        self.pos += self.vel * self.game.dt
        self.hit_rect.centerx = self.pos.x #recentering hitbox
        collide_with_walls(self, self.game.all_walls, 'x') #loading collide with walls for x
        self.hit_rect.centery = self.pos.y #recentering hitbox
        collide_with_walls(self, self.game.all_walls, 'y') #loading collide with walls for y
        self.rect.center = self.hit_rect.center # centering hitbox again to the regular visual center

# Wall sprite class that represents solid map tiles the player and mobs collide with.
class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        # wall sprites are static map tiles loaded from the level text file
        self.game = game
        self.image = game.wall_img
        # self.image = pg.Surface((TILESIZE, TILESIZE))
        # self.image.fill(GREEN) #only difference, color
        self.rect = self.image.get_rect()
        self.pos = vec(x,y) * TILESIZE
    
    def update(self): #same as player, but no movement
        # walls never move, so update only keeps the rect aligned with the stored position
        self.rect.center = self.pos

# Coin sprite class that acts as the level objective when collected by the player.
class Coin(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_coins
        Sprite.__init__(self, self.groups)
        # coins are the objective tiles placed directly from the map text
        self.game = game
        self.image = game.coin_img
        self.rect = self.image.get_rect()
        self.pos = vec(x,y) * TILESIZE
    
    def update(self): #same as player, but no movement 
        # coins are static, so they only need their rect centered on their map position
        self.rect.center = self.pos

# Projectile sprite class used for shots fired by the player.
class Projectile(Sprite):
    def __init__(self, game, x, y, direction):
        self.groups = game.all_sprites, game.all_projectiles
        Sprite.__init__(self, self.groups)
        # projectile uses pixel coordinates and moves immediately after being fired
        self.game = game
        self.image = pg.Surface((TILESIZE // 2, TILESIZE // 2))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos
        self.hit_rect = self.rect.copy()
        # normalize keeps projectile speed consistent even if direction changes later
        self.vel = direction.normalize() * PROJECTILE_SPEED
        self.spawn_time = pg.time.get_ticks()

    def update(self):
        # move the projectile in world space using delta time just like other moving objects
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos

        # remove old projectiles so they do not live forever and fill the sprite groups
        if pg.time.get_ticks() - self.spawn_time >= PROJECTILE_LIFETIME:
            self.kill()
            return

        # remove projectiles as soon as they hit a solid wall tile
        if pg.sprite.spritecollideany(self, self.game.all_walls):
            self.kill()

        
