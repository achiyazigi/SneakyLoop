from dataclasses import dataclass, field
from random import randint
from typing import List
from pygame import Color


@dataclass
class Settings:
    colors: List[Color]
    bots_count: int = 1
    players_count: int = 3

    def snakes_count(self):
        return self.bots_count + self.players_count


settings = Settings(
    [Color(randint(0, 255), randint(0, 255), randint(0, 255)) for _ in range(10)]
)
W = 640
H = 512
BG = Color("Black")
