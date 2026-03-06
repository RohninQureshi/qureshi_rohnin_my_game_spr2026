import pygame as pg
from pygame.sprite import Sprite
from settings import *
from utils import *
from state_machine import *
from player_states import *
from ctypes import Array
import sys
from os import path


vec = pg.math.Vector2 #using vectors


def collide_hit_rect(one, two):  #creating a function so that all classes can use this function, checks for collision between 2 entities, one and two, part of git library
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
            if hits[0].rect.centery > sprite.hit_rect.centery: #if the first item in the list of things that collided's center pos is greater then the sprite we are checking (player) y-dir
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.width/2 #the pos of sprite (player) will bounce upward a factor of the hitbox of the thing it collided with - player's hitbox divided by 2
            if hits[0].rect.centery < sprite.hit_rect.centery: #if the first item in the list of things that collided's center pos is greater then the sprite we are checking (player) y-dir
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.width/2 #the pos of sprite (player) will bounce downward by a factor of the hitbox of the thing it collided with - player's hitbox divided by 2
            sprite.vel.y = 0 #setting the original velocity to 0
            sprite.hit_rect.centery = sprite.pos.y # setting the center of the player to be the position
            

class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_players #group
        Sprite.__init__(self, self.groups)
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "sprite_sheet.png"))
        self.load_images()
        self.image = pg.Surface((TILESIZE,TILESIZE))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect() #creating rect for vector math
        self.vel = vec(0,0) #velocity
        self.pos = vec(x,y) * TILESIZE #postion
        self.hit_rect = PLAYER_HIT_RECT
        self.sprinting = False
        self.walking = False
        self.last_update = 0
        self.current_frame = 0
        self.projectile_cd = Cooldown(500)
        self.sprinting_cd = Cooldown(3000)
        self.state_machine = StateMachine()
        self.states: Array[State] = [PlayerIdleState(self), PlayerMoveState(self)]
        self.state_machine.start_machine(self.states)
        
    def get_key_movement(self): #function for movement
        self.vel = vec(0,0) #making sure player doesnt constantly move
        keys = pg.key.get_pressed() #gets the keys pressed
        
        if keys[pg.K_a]: #if tree, looks for specific keys, changes vel only on these keys (wasd)
            self.vel.x = -PLAYER_SPEED
        if keys[pg.K_d]:
            self.vel.x = PLAYER_SPEED
        if keys[pg.K_w]:
            self.vel.y = -PLAYER_SPEED
        if keys[pg.K_s]:
            self.vel.y = PLAYER_SPEED
        if self.vel.x != 0 and self.vel.y != 0:
            self.vel *= 0.7071 #a^2+b^2=c^2 so if a = and b = 1 then c = sqrt(2), so we multiply by root 2, prevents movement being faster diagonally
    def get_key_projectile(self): #looking for key press of specific key, and will insanciate a projectile when that key is pressed
        keys = pg.key.get_pressed()
        if keys[pg.K_f]:
            if self.projectile_cd.ready():
                self.projectile_cd.start()
                print("Projectile fired")
                p = Projectile(self.game, self.rect.x, self.rect.y)
            else:
                print("Cooldown still active")
    
    def load_images(self):
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
            frame.set_colorkey(BLACK)
    
    def state(self): #made a method that gets state, better for organization purposes
        keys = pg.key.get_pressed() #gets the keys pressed
        if self.vel: #if player moves
            self.walking = True
        
        else:
            self.walking = False
            
        if keys[pg.K_LSHIFT]: #if the left shift key is pressed down
            if self.sprinting_cd.ready():
                self.sprinting_cd.start()
                self.sprinting = True
                
            else:
                print("Cooldown active")
        else:
            self.sprinting = False
    
    def animate(self): #I made my spritesheet differently, making each row a state, rather then a charencter or thing
        now = pg.time.get_ticks() #gets current time
        if not self.sprinting and not self.walking: #only while static, need to update self.walking and self.jumping
            if now - self.last_update > 350: #cooldown for sprite update, 350 milliseconds per frame
                self.last_update = now #updates now
                self.current_frame = (self.current_frame + 1) % len(self.standing_frames) #this line iterates through all frames, and if you are on the last one, it goes back to the beginning
                bottom = self.rect.bottom
                self.image = self.standing_frames[self.current_frame] #sets the current image to be that frame
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom
        
        if self.walking and not self.sprinting: #only when walking, works the same as standing frames
            if now - self.last_update > 350: #cooldown for sprite update, 350 milliseconds per frame
                self.last_update = now #updates now
                self.current_frame = (self.current_frame + 1) % len(self.walking_frames) #this line iterates through all frames, and if you are on the last one, it goes back to the beginning
                bottom = self.rect.bottom
                self.image = self.walking_frames[self.current_frame] #sets the current image to be that frame
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom
        
        if self.sprinting and self.walking: #when wprinting while walking (can only sprint while also walking)
            self.vel.x = self.vel.x * PLAYER_SPRINT_SPEED/PLAYER_SPEED #set both velocitys to sprint speed by multiplying existing values so they keep negatives, this a way to remove normal player speed because the velocity is player speed, and anything divided by itself is 1, leaving player spritn speed as the only thing remaining
            self.vel.y = self.vel.y * PLAYER_SPRINT_SPEED/PLAYER_SPEED
            if now - self.last_update > 350: #cooldown for sprite update, 350 milliseconds per frame
                self.last_update = now #updates now
                self.current_frame = (self.current_frame + 1) % len(self.sprinting_frames) #this line iterates through all frames, and if you are on the last one, it goes back to the beginning
                bottom = self.rect.bottom
                self.image = self.sprinting_frames[self.current_frame] #sets the current image to be that frame
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom
        
    def update(self): #constantly updating and checking for this
        self.get_key_movement() #callign getkey and animate
        self.get_key_projectile()
        self.state()
        self.animate()
        self.rect.center = self.pos #these next couple lines of code are what allow for movement and change of position
        self.pos += self.vel * self.game.dt
        
        self.hit_rect.centerx = self.pos.x #recentering hitbox
        collide_with_walls(self, self.game.all_walls, 'x') #loading collide with walls for x
        self.hit_rect.centery = self.pos.y #recentering hitbox
        collide_with_walls(self, self.game.all_walls, 'y') #loading collide with walls for y
        self.rect.center = self.hit_rect.center # centering hitbox again to the regular visual center
        

        
class Mob(Sprite): 
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_mobs #group
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(RED) #only difference from player, the color
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.hit_rect = MOB_HIT_RECT

    def update(self): 
        self.pos += self.game.player.pos*self.game.dt 
        self.rect.center = self.pos
        self.pos += self.vel * self.game.dt
        self.hit_rect.centerx = self.pos.x #recentering hitbox
        collide_with_walls(self, self.game.all_walls, 'x') #loading collide with walls for x
        self.hit_rect.centery = self.pos.y #recentering hitbox
        collide_with_walls(self, self.game.all_walls, 'y') #loading collide with walls for y
        self.rect.center = self.hit_rect.center # centering hitbox again to the regular visual center
        
class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = game.wall_img
        # self.image = pg.Surface((TILESIZE, TILESIZE))
        # self.image.fill(GREEN) #only difference, color
        self.rect = self.image.get_rect()
        self.pos = vec(x,y) * TILESIZE
    
    def update(self): #same as player, but no movement
        self.rect.center = self.pos
        

class Coin(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_coins
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = game.coin_img
        self.rect = self.image.get_rect()
        self.pos = vec(x,y) * TILESIZE
    
    def update(self): #same as player, but no movement 
        self.rect.center = self.pos
        
class Projectile(Sprite): #new class based on mob, projectiles
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_projectiles #group
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(RED) #only difference from player, the color
        self.rect = self.image.get_rect()
        self.vel = vec(1,0) #1,0 instead of 0,0 because we want it to move
        self.pos = vec(x,y) * TILESIZE
        self.hit_rect = MOB_HIT_RECT
        self.speed = PROJECTILE_SPEED

    

        

    def update(self):
        self.rect.center = self.pos # centering

        