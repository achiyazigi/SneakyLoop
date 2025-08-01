from math import ceil
from random import randint
from globals import *
from pyengine import *
from snake import Snake, SnakeAI, SnakeCollisionManager, SnakeKeys
from pygame import *


class MainMenu(Entity):
    BUTTONS_SIZE = Size(100, 30)
    BUTTONS_GAP = 10
    BUTTONS_MARGIN_TOP = 100

    class PlayButton(UiButton):
        def __init__(self, pos, on_play: Callable[[], None]):
            super().__init__()
            self.on_play = on_play
            self.transform.size = MainMenu.BUTTONS_SIZE
            self.transform.pos = pos
            self.text = "Start"

        def on_left_click(self):
            super().on_left_click()
            self.on_play()

    def __init__(self):
        super().__init__()
        self.play_button = GameManager().instatiate(
            MainMenu.PlayButton(
                Pos((W - MainMenu.BUTTONS_SIZE.w) / 2, MainMenu.BUTTONS_MARGIN_TOP),
                self.on_play,
            )
        )

    def kill(self):
        super().kill()
        GameManager().destroy(self.play_button)

    def on_play(self):
        GameManager().destroy(self)
        SceneManager().set_scene(SceneType.GAMEPLAY)


class Gameplay(Entity):
    COUNTDOWN_SECS = 3
    COUNTDOWN_COLOR = Color(151, 216, 121)
    FONT_SIZE = 48
    GAME_OVER_TIME_SECS = 60 * 3
    TIMER_PAD_Y = 30

    def __init__(self):
        super().__init__()
        self.timer = Gameplay.GAME_OVER_TIME_SECS

        Snake.pause = True
        for _ in range(bots_count):
            GameManager().instatiate(SnakeAI(Pos(randint(0, W), randint(0, H))))

        GameManager().instatiate(Snake(Pos(W, H / 2)))
        # GameManager().instatiate(
        #     Snake(Pos(W, H / 2), SnakeKeys(K_d, K_a, K_w))
        # )
        # GameManager().instatiate(
        #     Snake(Pos(W, H / 2), SnakeKeys(K_j, K_g, K_y))
        # )
        self.font = pygame.font.SysFont(GameManager().font.name, Gameplay.FONT_SIZE)
        self.countdown = 3
        self.countdown_ceiled = ceil(self.countdown)
        self.game_countdown_sur = self.create_game_countdown_sur()
        self.timer_ceiled = ceil(self.timer)
        self.timer_sur = self.create_timer_sur()
        self.z_index = 1

    def create_game_countdown_sur(self):
        return self.font.render(
            str(self.countdown_ceiled), True, Gameplay.COUNTDOWN_COLOR
        )

    def create_timer_sur(self):
        return self.font.render(str(self.timer_ceiled), True, self.COUNTDOWN_COLOR)

    def update(self, dt):
        super().update(dt)
        self.countdown -= dt
        if self.countdown < self.countdown_ceiled:
            self.countdown_ceiled = ceil(self.countdown)
            self.game_countdown_sur = self.create_game_countdown_sur()
        if self.countdown < -1:
            self.countdown = -1
            if Snake.pause:
                self.timer = Gameplay.GAME_OVER_TIME_SECS
                self.timer_ceiled = ceil(self.timer)
                self.timer_sur = self.create_timer_sur()
                Snake.pause = False

        if not Snake.pause:
            self.timer -= dt
            if self.timer < self.timer_ceiled:
                self.timer_ceiled = ceil(self.timer)
                self.timer_sur = self.create_timer_sur()

    def render(self, sur):
        if self.countdown_ceiled >= 0:
            sur.blit(
                self.game_countdown_sur,
                (Size(W, H) - Size(self.game_countdown_sur.size)) / 2,
            )
        else:
            sur.blit(
                self.timer_sur,
                Pos((W - self.timer_sur.width) / 2, Gameplay.TIMER_PAD_Y),
            )


class SceneType(Enum):
    MAIN_MENU = 0
    GAMEPLAY = 1
    GAME_OVER = 2


class SceneManager(metaclass=Singelton):
    def __init__(self):
        super().__init__()
        self.scene_type = SceneType.MAIN_MENU

    def scene_main_menu(self):
        GameManager().instatiate(MainMenu())

    def scene_gameplay(self):
        GameManager().instatiate(Gameplay())

    def set_scene(self, scene_type: SceneType):
        self.scene_type = scene_type
        if scene_type == SceneType.MAIN_MENU:
            self.scene_main_menu()
        elif scene_type == SceneType.GAMEPLAY:
            self.scene_gameplay()
