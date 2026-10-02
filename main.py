import pygame
import random
import math
import asyncio
from pygame.math import Vector2

WIDTH, HEIGHT = 1400, 900

class Robot:
    def __init__(self, pos, v=Vector2(0,0), theta=0, w=0, reload = 0):
        self.pos = pos
        self.v = v
        self.theta = theta
        self.w = w
        self.held = 0
        self.reload = reload

    def update(self):
        self.v *= .9
        self.w *= .8
        self.pos += self.v
        self.theta += self.w
        self.reload = max(0, self.reload - 1/60)

    # returns the unit vector forward
    def forward(self):
        return Vector2(-1, 0).rotate(-self.theta)

class Pumpkin:
    camera_height = 75**2 / 2

    def __init__(self, pos, v=Vector2(0, 0), v_up = 0, height = 0, r = 10):
        self.pos = pos
        self.v = v
        self.height = height
        self.v_up = v_up
        self.r = r

    def update(self):
        self.pos += self.v
        self.height += self.v_up

        if self.height == 0:
            self.v *= .95
            return

        if self.height < 0:
            self.height = 0
            self.v_up = 0
            return

        self.v_up -= 1
        self.r = 10 * self.camera_height / (self.camera_height - self.height)


async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    clock = pygame.time.Clock()

    player_image = pygame.image.load("assets/player.png").convert_alpha()
    player_image = pygame.transform.scale(player_image, (60, 60))

    player = Robot(Vector2(WIDTH/2, HEIGHT/2))

    pumpkins = []

    running = True
    while running:    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        keys = pygame.key.get_pressed()
        val = 2
        if ((keys[pygame.K_a] or keys[pygame.K_d]) and (keys[pygame.K_w] or keys[pygame.K_s])):
            val = math.sqrt(2)
        if keys[pygame.K_j] or keys[pygame.K_l]:
            val *= .8
        if keys[pygame.K_a]:
            player.v.x -= val
        if keys[pygame.K_d]:
            player.v.x += val
        if keys[pygame.K_w]:
            player.v.y -= val
        if keys[pygame.K_s]:
            player.v.y += val
        if keys[pygame.K_j]:
            player.w += 2
        if keys[pygame.K_l]:
            player.w -= 2
        player.update()

        if keys[pygame.K_SPACE] and player.reload == 0:
            pumpkins.append(Pumpkin(player.pos.copy(), player.forward() * 10, 10))
            player.reload = .1

        for p in pumpkins:
            p.update()


        screen.fill((0,0,0))

        player_rotated = pygame.transform.rotate(player_image, player.theta)
        screen.blit(player_rotated, player_rotated.get_rect(center=player.pos))

        for p in pumpkins:
            pygame.draw.circle(screen, (254, 117, 24), p.pos, p.r)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())