from pyengine import *
import pygame
import math

from utils import get_mono_font, resource_path


class CheckBox(UiButton):
    DEFAULT_COLOR = Color("White")
    BORDER_THICKNESS = 2

    def __init__(
        self,
        pos: Pos,
        size: int,
        initial: bool,
        name: str = "",
        on_change: Callable[[bool], None] = None,
        color: Color = None,
    ):
        super().__init__()
        self.transform.pos = pos
        self.transform.size = Size(size)
        self.selected = initial
        self.on_change = on_change
        self.color = color if color else CheckBox.DEFAULT_COLOR
        self.name_sur = self.create_name_sur(name)

    def create_name_sur(self, name: str):
        return GameManager().font.render(name, True, self.color)

    def on_left_click(self):
        super().on_left_click()
        self.selected = not self.selected
        if self.on_change:
            self.on_change(self.selected)

    def render(self, sur):
        sur.blit(
            self.name_sur, self.transform.pos - Size(0, self.name_sur.get_height())
        )
        pygame.draw.rect(
            sur, self.color, self.transform.rect(), CheckBox.BORDER_THICKNESS
        )
        if self.selected:
            pygame.draw.line(
                sur,
                self.color,
                self.transform.rect().topleft,
                self.transform.rect().bottomright,
                CheckBox.BORDER_THICKNESS,
            )
            pygame.draw.line(
                sur,
                self.color,
                self.transform.rect().topright,
                self.transform.rect().bottomleft,
                CheckBox.BORDER_THICKNESS,
            )


class Bar(Entity):
    BGCOLOR = pygame.Color(200, 0, 0)
    FCOLOR = pygame.Color(0, 200, 0)
    TEXT_COLOR = pygame.Color(255, 255, 255)

    def __init__(
        self, initial_value: float, max_value: float, pos: Pos, size: Size, name=""
    ):
        super().__init__()
        self.initial_value = initial_value
        self.value = initial_value
        self.max_value = max_value
        self.transform.pos = pos
        self.transform.size = size
        self.edge_thickness = math.ceil(size.h / 6)
        self.name = name
        font = pygame.font.Font(
            size=int(self.transform.size.h - self.edge_thickness * 2),
        )
        self.text_sur = font.render(self.name, True, Bar.TEXT_COLOR)
        self.z_index = -1

    def render(self, sur):
        pygame.draw.rect(sur, Bar.BGCOLOR, self.transform.rect())
        precentage = self.value / self.max_value if self.max_value != 0 else 0
        bar_w = (self.transform.size.w - self.edge_thickness * 2) * precentage
        bar_h = self.transform.size.h - self.edge_thickness * 2
        pygame.draw.rect(
            sur,
            Bar.FCOLOR,
            pygame.Rect(
                self.transform.pos.x + self.edge_thickness,
                self.transform.pos.y + self.edge_thickness,
                bar_w,
                bar_h,
            ),
        )
        sur.blit(self.text_sur, self.transform.pos + Size(self.edge_thickness))


class Score(Entity):
    SCALE_ANIMATION_DUR_SECS = 1
    COLOR = Color(200, 170, 40)
    FONT_SIZE = 16
    SCALE_ANIMATION_FUNC = Animation.get_animation_func(AnimationType.Sin)

    def __init__(self, pos: Pos, normal_size: Size, animation_max_scale=1):
        super().__init__()
        self.scale_animation_timer = 0
        self.score = 0
        self.play_scale_animation = False
        self.transform.pos = pos
        self.transform.size = normal_size.copy()
        self.normal_size = normal_size
        self.animation_max_scale = animation_max_scale
        snsfmono_path = resource_path("assets/fonts/SFNSMono.ttf")
        self.font = pygame.font.Font(snsfmono_path, Score.FONT_SIZE)
        self.text_sur = self.create_text_sur()
        self.scale = 1

    def create_text_sur(self):
        return self.font.render(str(self.score), True, Score.COLOR)

    def add_score(self, value):
        self.score += value
        self.text_sur = self.create_text_sur()
        self.play_scale_animation = True

    def update(self, dt):
        super().update(dt)
        if self.play_scale_animation:
            self.scale = 1 + (
                Score.SCALE_ANIMATION_FUNC(
                    self.scale_animation_timer / Score.SCALE_ANIMATION_DUR_SECS
                )
                * (self.animation_max_scale - 1)
            )
            if self.scale_animation_timer > Score.SCALE_ANIMATION_DUR_SECS:
                self.scale_animation_timer = 0
                self.play_scale_animation = False
                self.scale = 1
            self.scale_animation_timer += dt

    def render(self, sur):
        text_sur = self.text_sur
        if self.scale != 1:
            text_sur = pygame.transform.scale_by(text_sur, self.scale)
        sur.blit(text_sur, self.transform.pos)


class Slider(Entity):
    HEIGHT = 10
    COLOR = Color("White")
    CONTROL_WIDTH = 5

    def __init__(
        self,
        width,
        initial_value,
        on_change,
        min=0,
        max=1,
        step=0.1,
        color=COLOR,
        name="",
    ):
        super().__init__()
        self.transform.size = Size(width, Slider.HEIGHT)
        self.value = initial_value
        self.on_change = on_change
        self.color = color
        self.min = min
        self.max = max
        self.step = step
        assert self.min <= self.value <= self.max
        InputManager().register_mouse_pressed(pygame.BUTTON_LEFT, self, self.on_pressed)
        InputManager().register_mouse_released(
            pygame.BUTTON_LEFT, self, self.on_release
        )
        self.dragging = False
        self.name_sur = GameManager().font.render(name, True, Slider.COLOR)

    def set_value(self, value):
        self.value = value

    def on_pressed(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.transform.rect().collidepoint(mouse_pos):
            self.dragging = True

    def on_release(self):
        self.dragging = False

    def get_control_rect_center(self):
        offset_val = self.value - self.min
        offset_max = self.max - self.min
        return self.transform.pos.x + self.transform.size.w * offset_val / offset_max

    def get_value_from_x(self, x):
        offset_x = x - self.transform.pos.x
        precentage = offset_x / self.transform.size.w
        return precentage * (self.max - self.min) + self.min

    def update(self, dt):
        super().update(dt)
        if self.dragging:
            mouse_pos = pygame.mouse.get_pos()
            self.value = pygame.math.clamp(
                (self.get_value_from_x(mouse_pos[0]) + self.step / 2)
                // self.step
                * self.step,
                self.min,
                self.max,
            )
            self.on_change(self.value)

    def render(self, sur):
        super().render(sur)
        sur.blit(self.name_sur, self.transform.pos - Pos(0, self.name_sur.get_height()))
        pygame.draw.rect(
            sur,
            Slider.COLOR,
            pygame.Rect(
                self.transform.pos.x,
                self.transform.pos.y + self.transform.size.h / 3,
                self.transform.size.w,
                self.transform.size.h / 3,
            ),
        )
        pygame.draw.rect(
            sur,
            self.color,
            pygame.Rect(
                self.get_control_rect_center() - Slider.CONTROL_WIDTH / 2,
                self.transform.pos.y,
                Slider.CONTROL_WIDTH,
                Slider.HEIGHT,
            ),
        )
        font_sur = GameManager().font.render(f"{self.value:.2f}", False, Slider.COLOR)
        sur.blit(
            font_sur,
            (
                self.get_control_rect_center() - font_sur.get_width() / 2,
                self.transform.rect().bottom,
            ),
        )
