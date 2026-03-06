from state_machine import *
from settings import *

class PlayerIdleState(State):
    def __init__(self, player):
        self.player = player
        self.name = "idle"

    def get_state_name(self):
        return "idle"

    def enter(self):
        self.player.image.fill(WHITE)
        print('enter player idle state')

    def exit(self):
        print('exit player idle state')

    def update(self):
        # print('updating player idle state...')
        


class PlayerWalkingState(State):
    
    def __init__(self, player):
        self.player = player
        self.name = "walking"

    def get_state_name(self):
        return "walking"

    def enter(self):
        print('enter player walking state')

    def exit(self):
        print('exit player walking state')

    def update(self):
        # print('updating player walking state...')
        

class PlayerSprintingState:
    
    def __init__(self, player):
        self.player = player
        self.name = "sprinting"
    
    def get_state_name(self):
        return "sprinting"
    
    def enter(self):
        print("enter player sprinting state")
    
    
    def exit(self):
        print("exit player sprinting state")
    
    def update(self):
        # print('updating player sprinting state...')
class PlayerAttackingState:
    
    def __init__(self, player):
        self.player = player
        self.name = "attacking"
    
    def get_state_name(self):
        return "attacking"
    
    def enter(self):
        print("enter player attacking state")
    
    
    def exit(self):
        print("exit player attacking state")
    
    def update(self):
        # print('updating player attacking state...')