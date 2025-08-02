from random import randint
import pygame
import math

from globals import H, W, settings
from pyengine import Entity, Pos, Size


def draw_arrow(
    sur: pygame.Surface,
    origin: pygame.Vector2,
    target: pygame.Vector2,
    head_size: Size,
    thickness,
    color,
):

    offset_vec = target - origin
    if offset_vec.length() == 0:
        return
    left_head = offset_vec.rotate_rad(math.pi / 2).normalize() * head_size.w / 2
    right_head = offset_vec.rotate_rad(-math.pi / 2).normalize() * head_size.w / 2
    head_vert = offset_vec.normalize() * head_size.h
    pygame.draw.line(
        sur,
        color,
        origin,
        target - head_vert,
        width=thickness,
    )
    pygame.draw.polygon(
        sur,
        color,
        [
            left_head + target - head_vert,
            right_head + target - head_vert,
            target,
        ],
    )


def replace_color(
    surface: pygame.Surface, old_color: pygame.Color, new_color: pygame.Color
):
    # Lock the surface for pixel access
    surface.lock()
    pxarray = pygame.PixelArray(surface)
    pxarray.replace(old_color, new_color)
    del pxarray
    surface.unlock()


def wrap(pos: Pos):
    return Pos(pos.x % W, pos.y % H)


def wrap_ip(pos: Pos):
    wrapped = wrap(pos)
    pos.x = wrapped.x
    pos.y = wrapped.y


def shortest_vector(from_pos: pygame.Vector2, to_pos: pygame.Vector2):
    dx = (to_pos.x - from_pos.x + W / 2) % W - W / 2
    dy = (to_pos.y - from_pos.y + H / 2) % H - H / 2
    return pygame.Vector2(dx, dy)


def draw_border(entity: Entity, sur: pygame.Surface, color: pygame.Color, width=1):
    rect = entity.transform.rect()
    pygame.draw.lines(
        sur,
        color,
        True,
        [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft],
        width,
    )


def generate_color():
    return pygame.Color(randint(0, 255), randint(0, 255), randint(0, 255))
