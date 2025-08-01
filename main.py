import random
import pygame
from pyengine import *
from scene_manager import SceneManager, SceneType
from globals import *
from snake import SnakeCollisionManager


def main():
    random.seed(0)
    pygame.init()
    pygame.display.set_caption("Template")
    screen = pygame.display.set_mode((W, H))
    SceneManager().set_scene(SceneType.MAIN_MENU)

    # UpdateManager().start_fixed_update_loop()
    while not GameManager().should_exit:
        screen.fill(BG)
        GameManager().update()
        # GameManager().render(screen)
        GameManager().render_debug(screen)
        pygame.display.flip()
    # UpdateManager().stop_fixed_update_loop()


if __name__ == "__main__":
    main()
    pygame.quit()
