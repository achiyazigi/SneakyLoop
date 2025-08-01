from pyengine import *
import pygame
import math


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
        font = pygame.font.SysFont(
            GameManager().font.name,
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
        self.font = pygame.font.SysFont("kohinoortelugu", Score.FONT_SIZE)
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
