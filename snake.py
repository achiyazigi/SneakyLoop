from dataclasses import field
import math
from random import randint, random
from typing import Dict
import random
from pygame import K_LEFT, K_RIGHT, K_SPACE, K_UP
from fruit import Fruit, FruitsSpawner, ShieldFruit
from globals import *
from pyengine import *
from ui import Bar, Score
from utils import draw_arrow, draw_border, shortest_vector, wrap, wrap_ip


class SnakeCollisionManager(SingeltonEntity):
    SKIN_DISAPPEAR_AFTER_SECS = 10
    BLINK_SKIN_FREQ = 0.5
    REJOIN_R = 20

    @dataclass
    class NodeData:
        timer: float = 0
        nodes: List[Pos] = field(default_factory=list)

    def __init__(self):
        super().__init__()
        self.snakes: List[Snake] = []
        self.cut_skins: Dict[int, SnakeCollisionManager.NodeData] = {}
        self.circle_sur = pygame.Surface(
            (Snake.NODE_R * 2, Snake.NODE_R * 2), pygame.SRCALPHA
        )

    def reset(self):
        self.cut_skins.clear()
        self.snakes.clear()

    def add(self, snake: "Snake"):
        self.snakes.append(snake)

    def on_collision(
        self, snake_attacker: "Snake", snake_attacked: "Snake", node_attacked_idx: int
    ):
        assert node_attacked_idx > 0
        self.cut_skins[snake_attacked.id] = SnakeCollisionManager.NodeData(
            SnakeCollisionManager.SKIN_DISAPPEAR_AFTER_SECS,
            snake_attacked.nodes[node_attacked_idx:],
        )
        snake_attacked.nodes = snake_attacked.nodes[:node_attacked_idx]

        snake_attacked.speed = snake_attacked.calc_speed()

    def check_attack(self, snake_attacker: "Snake", snake_attacked: "Snake"):
        assert len(snake_attacked.nodes) > 1
        for i in range(1, len(snake_attacked.nodes)):
            if (
                snake_attacker.nodes[0].distance_to(snake_attacked.nodes[i])
                < Snake.NODE_R
            ):
                self.on_collision(snake_attacker, snake_attacked, i)
                break

    def rejoin(self, snake: "Snake"):
        self.cut_skins[snake.id].nodes.extend(snake.nodes)
        snake.nodes = self.cut_skins[snake.id].nodes
        self.cut_skins.pop(snake.id)
        snake.transform.pos = snake.nodes[0]
        snake.speed = snake.calc_speed()
        if len(snake.nodes) > 1:
            snake.dir = (snake.nodes[0] - snake.nodes[1]).normalize()

    def check_collisions(self):
        if len(self.snakes) < 2:
            return
        for cur in self.snakes:
            for other in self.snakes[1:]:
                if len(other.nodes) > 1 and other.shield_timer <= 0:
                    self.check_attack(cur, other)
                if len(cur.nodes) > 1 and cur.shield_timer <= 0:
                    self.check_attack(other, cur)

            # check rejoin tail:
            if cur.id in self.cut_skins:
                if (
                    cur.transform.pos.distance_to(self.cut_skins[cur.id].nodes[-1])
                    < SnakeCollisionManager.REJOIN_R
                ):
                    self.rejoin(cur)

    def update(self, dt):
        super().update(dt)
        to_remove = []
        for i, node_data in self.cut_skins.items():
            if node_data.timer <= 0:
                to_remove.append(i)
            node_data.timer -= dt
        for i in to_remove:
            self.cut_skins.pop(i)

    def render(self, sur):
        for i, node_data in self.cut_skins.items():
            self.circle_sur.fill(Color(0, 0, 0, 0))
            color_with_alpha = Color(self.snakes[i].color)
            alpha = int(
                (
                    (
                        sin(
                            2
                            * math.pi
                            * SnakeCollisionManager.BLINK_SKIN_FREQ
                            * node_data.timer
                        )
                        + 1
                    )
                    / 4
                    + 0.5
                )
                * 255
            )
            color_with_alpha.a = alpha
            pygame.draw.circle(
                self.circle_sur,
                color_with_alpha,
                (Snake.NODE_R, Snake.NODE_R),
                Snake.NODE_R,
            )
            for node in node_data.nodes:
                sur.blit(self.circle_sur, node - Size(self.circle_sur.size) / 2)
            pygame.draw.circle(
                sur,
                color_with_alpha,
                node_data.nodes[-1],
                SnakeCollisionManager.REJOIN_R,
                1,
            )

    def kill(self):
        super().kill()
        self.reset()


class SnakeInfoDisplay(Entity):
    PAD = 10
    H = 70
    SCORE_MAX_SCALE = 2

    def __init__(self, snake: "Snake"):
        super().__init__()
        self.snake = snake

        self.transform.size = Size(
            (W - Snake.INFO_PAD * (settings.snakes_count() + 1))
            / settings.snakes_count(),
            SnakeInfoDisplay.H,
        )
        self.transform.pos = Pos(
            self.transform.size.w * self.snake.id
            + (self.snake.id + 1) * Snake.INFO_PAD,
            H - self.transform.size.h - Snake.INFO_PAD,
        )
        self.bar_size = Size(self.transform.size.w - SnakeInfoDisplay.PAD * 2, 20)
        self.score_size = Size(
            (self.transform.size.w - SnakeInfoDisplay.PAD * 2) / 2, 20
        )

        self.dash_bar = GameManager().instatiate(
            Bar(
                0,
                2,
                self.transform.pos + Size(SnakeInfoDisplay.PAD),
                self.bar_size,
                "Dash",
            )
        )
        self.score = GameManager().instatiate(
            Score(
                self.dash_bar.transform.rect().bottomleft
                + Size(0, SnakeInfoDisplay.PAD),
                self.score_size,
                SnakeInfoDisplay.SCORE_MAX_SCALE,
            )
        )
        self.z_index = -1

    def render(self, sur):
        draw_border(self, sur, self.snake.color)


class Snake(Entity):
    NODE_R = 5
    DIST_BETWEEN_NODES = NODE_R * 2
    SPEED_MULTIPLIER_FOR_NODES = 7
    DASH_MULTIPLIER = 1.5
    MIN_SPEED = 100
    MAX_DASH_LEVEL_SECS = 2
    DASH_INC_PER_SEC = 0.2
    INFO_PAD = 30
    snake_count = 0
    pause = False

    def __init__(self, pos: Pos, keys=SnakeKeys()):
        super().__init__()
        SnakeCollisionManager().add(self)
        self.id = Snake.snake_count
        assert self.id < len(settings.colors)
        self.color = settings.colors[self.id]
        Snake.snake_count += 1
        self.transform.pos = pos
        self.dir = Vector2(random.random() - 0.5, random.random() - 0.5).normalize()
        self.turning_dir = 0
        self.nodes: List[Vector2] = [self.transform.pos.copy()]
        self.speed_multiplier = 1
        self.shield_timer = 0
        self.speed = self.calc_speed()
        self.dash = False
        self.left_is_down = False
        self.right_is_down = False
        self.info_display = GameManager().instatiate(SnakeInfoDisplay(self))
        InputManager().register_key_down(keys.k_right, self, self.on_right_down)
        InputManager().register_key_down(keys.k_left, self, self.on_left_down)
        InputManager().register_key_up(keys.k_right, self, self.on_right_up)
        InputManager().register_key_up(keys.k_left, self, self.on_left_up)
        InputManager().register_key_down(keys.k_dash, self, self.on_dash_down)
        InputManager().register_key_up(keys.k_dash, self, self.on_dash_up)
        for _ in range(10):
            self.add_node()

    @staticmethod
    def score_func(nodes_loop_count):
        return nodes_loop_count**2

    def calc_speed(self):
        return max(Snake.SPEED_MULTIPLIER_FOR_NODES * len(self.nodes), Snake.MIN_SPEED)

    def on_hit_fruit(self, fruit: Fruit):
        self.add_node()
        fruit.trigger_hit(self)

    def add_node(self):
        self.nodes.insert(0, self.nodes[0] + self.dir * Snake.DIST_BETWEEN_NODES)
        self.transform.pos = self.nodes[0]
        self.speed = self.calc_speed()

    def on_right_down(self):
        self.right_is_down = True
        self.turning_dir = 1

    def on_left_down(self):
        self.left_is_down = True
        self.turning_dir = -1

    def on_right_up(self):
        self.right_is_down = False
        if self.left_is_down:
            self.turning_dir = -1
        else:
            self.turning_dir = 0

    def on_left_up(self):
        self.left_is_down = False
        if self.right_is_down:
            self.turning_dir = 1
        else:
            self.turning_dir = 0

    def on_dash_down(self):
        if self.info_display.dash_bar.value > 0:
            self.dash = True

    def on_dash_up(self):
        self.dash = False

    def on_collision(self, first, last):
        del self.nodes[first:last]
        assert len(self.nodes) > 0
        self.transform.pos = self.nodes[0]
        self.speed = self.calc_speed()
        self.info_display.score.add_score(Snake.score_func(last - first))

    def check_collisions(self):
        for i in range(len(self.nodes)):
            for j in range(i + 1, len(self.nodes)):
                cur = self.nodes[i]
                other = self.nodes[j]
                if cur.distance_to(other) < Snake.NODE_R:
                    self.on_collision(i, j)
                    break

    def check_fruit_collision(self):
        for fruit in FruitsSpawner().fruits:
            if (
                fruit.transform.pos.distance_to(self.transform.pos)
                < Fruit.R + Snake.NODE_R
            ):
                self.on_hit_fruit(fruit)
                break

    def update(self, dt: float):
        super().update(dt)
        if Snake.pause:
            return
        if self.info_display.dash_bar.value < Snake.MAX_DASH_LEVEL_SECS:
            self.info_display.dash_bar.value += dt * Snake.DASH_INC_PER_SEC

        if self.info_display.dash_bar.value <= 0:
            self.info_display.dash_bar.value = 0
            self.dash = False
        if self.dash:
            self.info_display.dash_bar.value -= dt

        if self.shield_timer > 0:
            self.shield_timer -= dt
        else:
            self.shield_timer = 0

        self.dir.rotate_ip(self.turning_dir * dt * self.speed * 2)

        self.nodes[0] += (
            self.dir.normalize()
            * self.speed
            * dt
            * (Snake.DASH_MULTIPLIER if self.dash else 1)
            * self.speed_multiplier
        )
        wrap_ip(self.nodes[0])

        for i in range(1, len(self.nodes)):
            prev = self.nodes[i - 1]
            curr = self.nodes[i]

            vec_to_prev = shortest_vector(curr, prev)
            direction = vec_to_prev.normalize()
            self.nodes[i] = wrap(prev - direction * Snake.DIST_BETWEEN_NODES)

        self.check_collisions()
        self.check_fruit_collision()
        SnakeCollisionManager().check_collisions()

    def render(self, sur):
        for node_pos in self.nodes:
            if self.shield_timer > 0:
                pygame.draw.circle(sur, ShieldFruit.COLOR, node_pos, Snake.NODE_R + 2)
            pygame.draw.circle(sur, self.color, node_pos, Snake.NODE_R)
        for n, nn in zip(self.nodes, self.nodes[1:]):
            pygame.draw.line(sur, self.color, n, n + shortest_vector(n, nn))


class SnakeAiActions(Enum):
    LEFT = -1
    STRAIGHT = 0
    RIGHT = 1


class SnakeAI(Snake):
    ACTION_DUR_SECS = 3

    def __init__(self, pos):
        super().__init__(pos, SnakeKeys(None, None, None))
        self.action_timer = 0
        self.current_action = SnakeAI.random_action()

    @staticmethod
    def random_action():
        return SnakeAiActions(randint(-1, 1))

    def update(self, dt):
        super().update(dt)
        self.action_timer += dt
        if self.action_timer > SnakeAI.ACTION_DUR_SECS:
            self.action_timer = 0
            self.current_action = SnakeAI.random_action()

        self.turning_dir = self.current_action.value
