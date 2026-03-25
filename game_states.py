from state_machine import State


class GamePlayingState(State):
    def __init__(self, game):
        self.game = game

    def get_state_name(self):
        return "playing"

    def enter(self):
        self.game.playing = True

    def exit(self):
        pass

    def update(self):
        self.game.all_sprites.update()
        if self.game.camera is not None:
            self.game.camera.update(self.game.player)


class GamePausedState(State):
    def __init__(self, game):
        self.game = game

    def get_state_name(self):
        return "paused"

    def enter(self):
        self.game.playing = False

    def exit(self):
        pass

    def update(self):
        pass


class GameOverState(State):
    def __init__(self, game):
        self.game = game

    def get_state_name(self):
        return "game_over"

    def enter(self):
        self.game.playing = False

    def exit(self):
        pass

    def update(self):
        pass
