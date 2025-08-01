from random import randint
from globals import H, W
from pyengine import *


class FruitsSpawner(Entity, metaclass=Singelton):
    INTERVAL_SECS = 2

    def __init__(self):
        super().__init__()
        GameManager().instatiate(self)
        self.fruits: List[Fruit] = []
        self.spawn_timer = FruitsSpawner.INTERVAL_SECS

    def update(self, dt):
        super().update(dt)
        if self.spawn_timer >= FruitsSpawner.INTERVAL_SECS:
            self.spawn_timer = 0
            self.spawn(Pos(randint(0, W), randint(0, H)))
        self.spawn_timer += dt

    def spawn(self, pos: Pos):
        random_fruit_type = randint(0, 2)
        if random_fruit_type == 0:
            self.fruits.append(GameManager().instatiate(Fruit(pos)))
        elif random_fruit_type == 1:
            self.fruits.append(GameManager().instatiate(SpeedFruit(pos)))
        elif random_fruit_type == 2:
            self.fruits.append(GameManager().instatiate(ShieldFruit(pos)))


class Fruit(Entity):
    R = 10
    COLOR = Color("Red")

    def __init__(self, pos: Pos):
        super().__init__()
        self.transform.pos = pos
        self.color = self.COLOR

    def trigger_hit(self, snake):
        FruitsSpawner().fruits.remove(self)
        GameManager().destroy(self)

    def render(self, sur):
        pygame.draw.circle(sur, self.color, self.transform.pos, Fruit.R)


class SpeedFruit(Fruit):
    MULTIPLIER = 1.5
    DUR_SECS = 3
    COLOR = Color("Blue")

    def __init__(self, pos):
        super().__init__(pos)
        self.snake = None
        self.timer = SpeedFruit.DUR_SECS

    def update(self, dt):
        super().update(dt)
        if self.snake:
            if self.timer < 0:
                self.snake.speed_multiplier /= SpeedFruit.MULTIPLIER
                GameManager().destroy(self)
            self.timer -= dt

    def render(self, sur):
        if not self.snake:
            super().render(sur)

    def trigger_hit(self, snake):
        self.snake = snake
        self.snake.speed_multiplier *= SpeedFruit.MULTIPLIER
        FruitsSpawner().fruits.remove(self)


class ShieldFruit(Fruit):
    DUR_SECS = 3
    COLOR = Color("White")

    def trigger_hit(self, snake):
        snake.shield_timer = ShieldFruit.DUR_SECS
        super().trigger_hit(snake)
