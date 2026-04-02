from state_machine import State


# State used while the game world is actively running and updating.
class GamePlayingState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # this key is how the main state machine refers to the active gameplay state
        return "playing"

    def enter(self):
        # marks the game as actively running gameplay
        self.game.playing = True

    def exit(self):
        # playing does not need teardown here because pause / win states handle their own setup
        pass

    def update(self):
        # only while playing do we update sprites and the camera
        self.game.all_sprites.update()
        if self.game.camera is not None:
            self.game.camera.update(self.game.player)
        
        


# State used when gameplay is frozen but the game is still open.
class GamePausedState(State):
    def __init__(self, game):
        self.game = game

    def get_state_name(self):
        # paused is a distinct flow state so gameplay updates can be skipped cleanly
        return "paused"

    def enter(self):
        # paused stops gameplay updates but still allows UI and event handling
        self.game.playing = False

    def exit(self):
        # paused has no cleanup because resuming just transitions back to playing
        pass

    def update(self):
        # no gameplay update while paused
        pass


# State used after the player loses and gameplay should stop.
class GameOverState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # game_over identifies the loss screen in the shared game state machine
        return "game_over"

    def enter(self):
        # game over also freezes gameplay so only restart / quit actions remain
        self.game.playing = False

    def exit(self):
        # no extra cleanup is needed when leaving the game over screen
        pass

    def update(self):
        # game over does not advance gameplay; it only waits for player input
        pass


# State used for the title / start screen before gameplay begins.
class GameStartState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # start is the title screen key used before gameplay begins
        return "start"

    def enter(self):
        # start screen waits for the player to begin the run
        self.game.playing = False

    def exit(self):
        # start screen also does not need teardown logic when Enter is pressed
        pass

    def update(self):
        # start screen also waits for input instead of updating gameplay
        pass
    
# Temporary transition state used to move the game from one level to the next.
class GameLevelClearState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # level_clear is a short transition state, not a long-lived gameplay screen
        return "level_clear"

    def enter(self):
        # entering level_clear immediately advances to the next level
        self.game.next_level()

    def exit(self):
        # this state finishes its work in enter, so exit remains empty
        pass

    def update(self):
        # level clear hands work off in enter, so update stays empty
        pass


# State used after the player beats the final level of the game.
class GameWonState(State):
    def __init__(self, game):
        # stores a reference to the main Game object so the state can control it
        self.game = game

    def get_state_name(self):
        # game_won marks the final completion screen after the last level
        return "game_won"

    def enter(self):
        # win state freezes gameplay and shows the end screen
        self.game.playing = False

    def exit(self):
        # restart input handles the reset, so exit does not need to do anything special
        pass

    def update(self):
        # win state waits for restart input rather than updating gameplay
        pass
