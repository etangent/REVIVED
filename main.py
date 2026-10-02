import pygame
import random
import math
import asyncio
from pygame.math import Vector2

WIDTH, HEIGHT = 1400, 900

class Robot:
    def __init__(self, pos, v=Vector2(0,0), theta=0, w=0):
        self.pos = pos
        self.v = v
        self.theta = theta
        self.w = w

    def update(self):
        self.v *= .9
        self.w *= .8
        self.pos += self.v
        self.theta += self.w

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    clock = pygame.time.Clock()

    player_image = pygame.image.load("assets/player.jpg").convert_alpha()
    player_image = pygame.transform.scale(player_image, (60, 60))

    player = Robot(Vector2(WIDTH/2, HEIGHT/2))

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

        screen.fill((0,0,0))

        player_rotated = pygame.transform.rotate(player_image, player.theta)
        screen.blit(player_rotated, player_rotated.get_rect(center=player.pos))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())