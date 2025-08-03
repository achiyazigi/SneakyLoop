from dataclasses import dataclass, field
from random import randint
from typing import List
from pygame.constants import *
from pygame import Color
import random

random.seed(0)


@dataclass
class SnakeKeys:
    k_right: int = K_RIGHT
    k_left: int = K_LEFT
    k_dash: int = K_UP


@dataclass
class Settings:
    colors: List[Color]
    keys: List[SnakeKeys]
    bots_count: int = 1
    players_count: int = 1

    def snakes_count(self):
        return self.bots_count + self.players_count


settings = Settings(
    [Color(randint(0, 255), randint(0, 255), randint(0, 255)) for _ in range(10)],
    [
        SnakeKeys(),
        SnakeKeys(K_d, K_a, K_w),
        SnakeKeys(K_j, K_g, K_y),
        SnakeKeys(K_0, K_l, K_o),
    ],
)

W = 640
H = 512
BG = Color("Black")
