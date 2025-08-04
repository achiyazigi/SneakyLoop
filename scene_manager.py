from math import ceil
from random import randint
from color_pallete import ColorPalette
from fruit import FruitsSpawner
from globals import *
from pyengine import *
from snake import Snake, SnakeAI, SnakeCollisionManager, SnakeKeys
from pygame import *

from ui import CheckBox, Slider
from utils import draw_border, generate_color, get_mono_font, resource_path


class ColorPicker(UiButton):
    PALETTE_SIZE = Size(100, 100)

    def __init__(
        self,
        center: Pos,
        radius: int,
        default: Color,
        on_color_picked: Callable[[Color], None] = None,
    ):
        super().__init__()
        self.transform.pos = center - Size(radius)
        self.transform.size = Size(radius * 2)
        self.r = radius
        self.color = default
        self.z_index = 1
        self.on_color_picked = on_color_picked

    def on_mouse_released(self):
        super().on_mouse_released()
        color_palette = GameManager().instatiate(
            ColorPalette(Pos(self.transform.rect().topright), ColorPicker.PALETTE_SIZE)
        )
        color_palette.on_pick = lambda color: self.on_pick(color_palette, color)

    def on_pick(self, color_palette: ColorPalette, color: Color):
        self.color = color
        if self.on_color_picked:
            self.on_color_picked(self.color)
        GameManager().destroy(color_palette)

    def render(self, sur):
        pygame.draw.circle(sur, self.color, self.transform.rect().center, self.r)


class PlayerSettings(Entity):
    COLOR_PICK_BUTTON_R = 10
    H = 20
    H_GAP = 10
    COLOR = Color(255, 255, 255)

    def __init__(self, snake_id: int, pos: Pos):
        super().__init__()
        self.transform.pos = pos
        self.snake_id = snake_id
        self.color_picker = GameManager().instatiate(
            ColorPicker(
                self.transform.pos + Size(PlayerSettings.COLOR_PICK_BUTTON_R),
                PlayerSettings.COLOR_PICK_BUTTON_R,
                settings.colors[settings.bots_count + snake_id],
                self.on_color_picked,
            )
        )
        self.keys = settings.keys[self.snake_id]
        self.font = get_mono_font(PlayerSettings.H)
        self.left_key_sur = self.font.render(
            pygame.key.name(self.keys.k_left), True, PlayerSettings.COLOR
        )
        self.right_key_sur = self.font.render(
            pygame.key.name(self.keys.k_right), True, PlayerSettings.COLOR
        )
        self.dash_key_sur = self.font.render(
            pygame.key.name(self.keys.k_dash), True, PlayerSettings.COLOR
        )

    def on_color_picked(self, color):
        settings.colors[settings.bots_count + self.snake_id] = color

    def render(self, sur):
        sur.blit(
            self.left_key_sur,
            self.transform.pos
            + 1 * Size(PlayerSettings.H_GAP + self.color_picker.transform.size.w, 0),
        )
        sur.blit(
            self.right_key_sur,
            self.transform.pos
            + Size(self.left_key_sur.get_width(), 0)
            + 2 * Size(PlayerSettings.H_GAP + self.color_picker.transform.size.w, 0),
        )
        sur.blit(
            self.dash_key_sur,
            self.transform.pos
            + Size(self.left_key_sur.get_width() + self.right_key_sur.get_width(), 0)
            + 3 * Size(PlayerSettings.H_GAP + self.color_picker.transform.size.w, 0),
        )

    def kill(self):
        super().kill()
        GameManager().destroy(self.color_picker)


class MainMenu(Entity):

    BUTTONS_SIZE = Size(100, 30)
    BUTTONS_GAP = 20
    BUTTONS_MARGIN_TOP = 100
    SLIDERS_COLOR = Color(70, 70, 70)
    MIN_BOTS = 0
    MAX_BOTS = 10
    MIN_PLAYERS = 1
    MAX_PLAYERS = 4
    COLOR_PICK_BUTTON_R = PlayerSettings.COLOR_PICK_BUTTON_R
    COLOR_PICK_BUTTONS_GAP = 5

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
        self.theme_music_checkbox = GameManager().instatiate(
            CheckBox(
                self.play_button.transform.rect().bottomleft
                + Size(0, MainMenu.BUTTONS_GAP),
                MainMenu.BUTTONS_SIZE.h,
                settings.music,
                "music",
                self.on_toggle_music,
            )
        )
        self.sound_effects_checkbox = GameManager().instatiate(
            CheckBox(
                self.theme_music_checkbox.transform.rect().topright
                + Size(MainMenu.BUTTONS_GAP, 0),
                MainMenu.BUTTONS_SIZE.h,
                settings.sound_effects,
                "sound effects",
                self.on_toggle_sound_effects,
            )
        )
        self.bots_slider = GameManager().instatiate(
            Slider(
                MainMenu.BUTTONS_SIZE.w,
                settings.bots_count,
                self.on_bots_change,
                MainMenu.MIN_BOTS,
                MainMenu.MAX_BOTS,
                1,
                MainMenu.SLIDERS_COLOR,
                "Bots",
            )
        )
        self.bots_slider.transform.pos = (
            self.theme_music_checkbox.transform.rect().bottomleft
            + Size(0, MainMenu.BUTTONS_GAP)
        )
        self.bots_color_pickers: List[ColorPicker] = []
        self.update_bots_color_pickers()
        self.players_slider = GameManager().instatiate(
            Slider(
                MainMenu.BUTTONS_SIZE.w,
                settings.players_count,
                self.on_players_change,
                MainMenu.MIN_PLAYERS,
                MainMenu.MAX_PLAYERS,
                1,
                MainMenu.SLIDERS_COLOR,
                "Players",
            )
        )
        self.players_slider.transform.pos = (
            self.bots_slider.transform.rect().bottomleft
            + Size(
                0,
                MainMenu.BUTTONS_GAP
                + MainMenu.COLOR_PICK_BUTTON_R * 2
                + MainMenu.BUTTONS_GAP,
            )
        )
        self.players_settings: List[PlayerSettings] = []
        self.update_players_settings()

    def on_toggle_music(self, selected):
        settings.music = selected

    def on_toggle_sound_effects(self, selected):
        settings.sound_effects = selected

    def update_snake_color(self, idx: int, color: Color):
        assert idx < len(settings.colors)
        settings.colors[idx] = color

    def update_bots_color_pickers(self):
        bots_colors_size = Size(
            settings.bots_count
            * (MainMenu.COLOR_PICK_BUTTON_R * 2 + MainMenu.COLOR_PICK_BUTTONS_GAP)
            - MainMenu.COLOR_PICK_BUTTONS_GAP,
            MainMenu.COLOR_PICK_BUTTON_R * 2,
        )
        bots_colors_pos = Pos(
            (W - bots_colors_size.w) / 2,
            self.bots_slider.transform.rect().bottom + MainMenu.BUTTONS_GAP,
        )

        if len(self.bots_color_pickers) < settings.bots_count:

            assert len(settings.colors) >= settings.bots_count

            for i in range(len(self.bots_color_pickers), settings.bots_count):
                self.bots_color_pickers.append(
                    GameManager().instatiate(
                        ColorPicker(
                            bots_colors_pos
                            + Pos(
                                i
                                * (
                                    MainMenu.COLOR_PICK_BUTTON_R * 2
                                    + MainMenu.COLOR_PICK_BUTTONS_GAP
                                ),
                                0,
                            ),
                            MainMenu.COLOR_PICK_BUTTON_R,
                            settings.colors[i],
                            lambda color, i=i: self.update_snake_color(i, color),
                        )
                    )
                )
        else:
            GameManager().destroy(*self.bots_color_pickers[settings.bots_count :])
            self.bots_color_pickers = self.bots_color_pickers[: settings.bots_count]
        for i in range(len(self.bots_color_pickers)):
            self.bots_color_pickers[i].transform.pos = bots_colors_pos + Pos(
                i
                * (MainMenu.COLOR_PICK_BUTTON_R * 2 + MainMenu.COLOR_PICK_BUTTONS_GAP),
                0,
            )

    def update_players_settings(self):
        if len(self.players_settings) < settings.players_count:
            for i in range(len(self.players_settings), settings.players_count):
                self.players_settings.append(
                    GameManager().instatiate(
                        PlayerSettings(
                            i,
                            self.players_slider.transform.rect().bottomleft
                            + Size(
                                0,
                                MainMenu.BUTTONS_GAP
                                + i * (MainMenu.BUTTONS_GAP + PlayerSettings.H),
                            ),
                        )
                    )
                )
        else:
            GameManager().destroy(*self.players_settings[settings.players_count :])
            self.players_settings = self.players_settings[: settings.players_count]

    def on_bots_change(self, value):
        settings.bots_count = int(value)
        if settings.snakes_count() > len(settings.colors):
            for _ in range(settings.snakes_count() - len(settings.colors)):
                settings.colors.append(generate_color())
        self.update_bots_color_pickers()

    def on_players_change(self, value):
        settings.players_count = int(value)
        if settings.snakes_count() > len(settings.colors):
            for _ in range(settings.snakes_count() - len(settings.colors)):
                settings.colors.append(generate_color())
        self.update_players_settings()

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
        FruitsSpawner().pause = True
        SnakeCollisionManager().reset()
        for _ in range(settings.bots_count):
            GameManager().instatiate(SnakeAI(Pos(randint(0, W), randint(0, H))))

        for i in range(settings.players_count):
            assert i < len(settings.keys)
            GameManager().instatiate(Snake(Pos(W, H / 2), settings.keys[i]))
        self.font = pygame.font.Font(size=Gameplay.FONT_SIZE)
        self.countdown = 3
        self.countdown_ceiled = ceil(self.countdown)
        self.game_countdown_sur = self.create_game_countdown_sur()
        self.timer_ceiled = ceil(self.timer)
        self.timer_sur = self.create_timer_sur()
        self.z_index = 1
        self.theme_sound = pygame.mixer.Sound(resource_path("assets/audio/theme.ogg"))
        if settings.music:
            self.theme_sound.play(-1)

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
                FruitsSpawner().pause = False

        if not Snake.pause:
            self.timer -= dt
            if self.timer < self.timer_ceiled:
                self.timer_ceiled = ceil(self.timer)
                self.timer_sur = self.create_timer_sur()
        if self.timer < 0:
            Snake.pause = True
            FruitsSpawner().pause = True
            GameManager().destroy(self)
            self.theme_sound.stop()
            SceneManager().set_scene(SceneType.GAME_OVER)
            SnakeCollisionManager().cut_skins.clear()  # only clear cut_skins, keep snakes alive for game over scene

    def render(self, sur):
        if self.countdown_ceiled >= 0:
            sur.blit(
                self.game_countdown_sur,
                (Size(W, H) - Size(self.game_countdown_sur.get_size())) / 2,
            )
        else:
            sur.blit(
                self.timer_sur,
                Pos((W - self.timer_sur.get_width()) / 2, Gameplay.TIMER_PAD_Y),
            )

    def kill(self):
        super().kill()
        Snake.snake_count = 0


class GameOver(Entity):
    BUTTONS_SIZE = MainMenu.BUTTONS_SIZE

    class RestartButton(UiButton):
        def __init__(self, pos: Pos):
            super().__init__()
            self.transform.size = GameOver.BUTTONS_SIZE
            self.transform.pos = pos
            self.text = "Restart"

        def on_left_click(self):
            super().on_left_click()
            SceneManager().set_scene(SceneType.GAMEPLAY)

    class MainMenuButton(UiButton):
        def __init__(self, pos: Pos):
            super().__init__()
            self.transform.size = GameOver.BUTTONS_SIZE
            self.transform.pos = pos
            self.text = "Main Menu"

        def on_left_click(self):
            super().on_left_click()
            SceneManager().set_scene(SceneType.MAIN_MENU)

    BG = Color(30, 30, 30)
    BORDER_RADIUS = 15
    BORDER_WIDTH = 2
    BORDER_COLOR = Color(255, 255, 255)
    TITLE_COLOR = Color(255, 255, 255)
    TEXT_SIZE = 20
    TITLE_SIZE = 30
    PAD_TOP = 20
    SCORES_PAD = 10
    SCORES_GAP = 10
    BUTTONS_GAP = 10
    SIZE = Size(W * 3 / 4, (H - PAD_TOP - TITLE_SIZE) * 3 / 4)

    def __init__(self):
        super().__init__()
        self.scores_font = get_mono_font(GameOver.TEXT_SIZE)
        self.title_font = pygame.font.Font(size=GameOver.TITLE_SIZE)

        self.score_surs: List[Surface] = self.create_score_surs()
        self.transform.size = GameOver.SIZE
        self.transform.pos = (
            Size(W, H - GameOver.PAD_TOP - GameOver.TITLE_SIZE) - self.transform.size
        ) / 2
        self.title = self.title_font.render("Game Over", True, GameOver.TITLE_COLOR)

        self.restart_button = GameManager().instatiate(
            GameOver.RestartButton(
                Pos((W - GameOver.BUTTONS_SIZE.w) / 2, self.transform.rect().bottom)
            )
        )
        self.restart_button = GameManager().instatiate(
            GameOver.MainMenuButton(
                Pos(
                    (W - GameOver.BUTTONS_SIZE.w) / 2,
                    self.restart_button.transform.rect().bottom + GameOver.BUTTONS_GAP,
                )
            )
        )

    def create_score_surs(self):
        res = []
        for snake in sorted(
            SnakeCollisionManager().snakes,
            key=lambda s: s.info_display.score.score,
            reverse=True,
        ):
            is_bot = snake.id < settings.bots_count
            name = f"{'Bot' if is_bot else 'Player'} {snake.id}:"
            res.append(
                self.scores_font.render(
                    f"{name:<10}{snake.info_display.score.score:<5}",
                    True,
                    snake.color,
                )
            )
        return res

    def render(self, sur):
        pygame.draw.rect(
            sur,
            GameOver.BG,
            self.transform.rect(),
            border_radius=GameOver.BORDER_RADIUS,
        )
        pygame.draw.rect(
            sur,
            GameOver.BORDER_COLOR,
            self.transform.rect(),
            border_radius=GameOver.BORDER_RADIUS,
            width=GameOver.BORDER_WIDTH,
        )
        sur.blit(self.title, Pos((W - self.title.get_width()) / 2, GameOver.PAD_TOP))
        score_sur_y = self.transform.pos.y + GameOver.SCORES_PAD

        score_sur_x = self.transform.pos.x + GameOver.SCORES_PAD
        for score_sur in self.score_surs:
            if score_sur_y + score_sur.get_height() > self.transform.rect().bottom:
                score_sur_y = self.transform.pos.y + GameOver.SCORES_PAD
                score_sur_x += score_sur.get_width() + GameOver.SCORES_PAD
            sur.blit(score_sur, Pos(score_sur_x, score_sur_y))
            score_sur_y += score_sur.get_height() + GameOver.SCORES_GAP


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

    def scene_gameover(self):
        GameManager().instatiate(GameOver())

    def set_scene(self, scene_type: SceneType):
        GameManager().clear_scene(exceptions={FruitsSpawner(), SnakeCollisionManager()})

        self.scene_type = scene_type
        if scene_type == SceneType.MAIN_MENU:
            self.scene_main_menu()
        elif scene_type == SceneType.GAMEPLAY:
            self.scene_gameplay()
        elif scene_type == SceneType.GAME_OVER:
            self.scene_gameover()
