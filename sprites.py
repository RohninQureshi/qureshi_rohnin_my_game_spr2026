import pygame as pg
from pygame.sprite import Sprite
from settings import *
import sys
from os import path


vec = pg.math.Vector2 #using vectors

def collide_hit_rect(one, two):  #creating a function so that all classes can use this function, checks for collision between 2 entities, one and two, part of git library
    return one.hit_rect.colliderect(two.rect)

def collide_with_walls(sprite, group, dir): # A function that finds what it colliding, the sprite, the group of the sprite, wheter to destroy, and the other fuction ^. Checks whne direction is x
    if dir == 'x':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        print(hits)

class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_players #group
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE)) #rendering 
        self.image.fill(WHITE)
        self.rect = self.image.get_rect() #creating rect for vector math
        self.vel = vec(0,0) #velocity
        self.pos = vec(x,y) * TILESIZE #postion
        self.hit_rect = PLAYER_HIT_RECT
        
    def get_key(self): #function for movement
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
    
    def update(self): #constantly updating and checking for this
        self.get_key() 
        self.rect.center = self.pos #these next couple lines of code are what allow for movement and change of position
        self.pos += self.vel * self.game.dt
        mob_hits = pg.sprite.spritecollide(self, self.game.all_mobs, False) #creating a variable that uses sprite's built in collide function to check for collision
        if mob_hits:
            print("Collided with Mob!")
        
        object_hits = pg.sprite.spritecollide(self, self.game.all_walls, False)
        if object_hits:
            print("Collided with Objects!")
        coin_hits = pg.sprite.spritecollide(self, self.game.all_coins, True)
        if coin_hits:
            print("Collided with Coin, Coin collected!")
        
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
    
    def update(self): #same from player, but different in movement
        self.pos += self.game.player.pos*self.game.dt #this means that mob will take player's pos, and rush towards it
        self.rect.center = self.pos
        self.pos += self.vel * self.game.dt
        player_hits = pg.sprite.spritecollide(self, self.game.all_players, False)
        if player_hits:
            print("Collided with Mob!")
        
        object_hits = pg.sprite.spritecollide(self, self.game.all_walls, False)
        if object_hits:
            print("Collided with Objects!")
class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN) #only difference, color
        self.rect = self.image.get_rect()
        self.pos = vec(x,y) * TILESIZE
    
    def update(self): #same as player, but no movement
        self.rect.center = self.pos
        mob_hits = pg.sprite.spritecollide(self, self.game.all_mobs, False)
        if mob_hits:
            print("Collided with Mob!")
        
        player_hits = pg.sprite.spritecollide(self, self.game.all_players, False)
        if player_hits:
            print("Collided with Player!")

class Coin(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_coins
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(YELLOW) #only difference, color
        self.rect = self.image.get_rect()
        self.pos = vec(x,y) * TILESIZE
    
    def update(self): #same as player, but no movement
        self.rect.center = self.pos
        
        player_hits = pg.sprite.spritecollide(self, self.game.all_players, False)
        if player_hits:
            print("Collided with Player!")