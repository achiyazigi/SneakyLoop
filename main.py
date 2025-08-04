import asyncio
import pygame
from pyengine import *
from scene_manager import SceneManager, SceneType
from globals import *


async def main():
    pygame.init()
    pygame.mixer.init()

    pygame.display.set_caption("Sneaky Loop! by: achiyazigi")
    screen = pygame.display.set_mode((W, H))
    SceneManager().set_scene(SceneType.MAIN_MENU)
    # UpdateManager().start_fixed_update_loop()
    while not GameManager().should_exit:
        screen.fill(BG)
        GameManager().update()
        GameManager().render(screen)
        # GameManager().render_debug(screen)
        pygame.display.flip()
        await asyncio.sleep(0)
    # UpdateManager().stop_fixed_update_loop()


asyncio.run(main())
pygame.quit()
