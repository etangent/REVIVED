from cmath import rect
import pygame
import random
import math
import asyncio
from pygame.math import Vector2

WIDTH, HEIGHT = 1400, 900
robot_hitbox = 30

class Robot:
    def __init__(self, pos, v=Vector2(0,0), theta=0, w=0, capacity = 70):
        self.pos = pos
        self.v = v
        self.theta = theta
        self.w = w
        self.held = 0
        self.reload = 0
        self.capacity = capacity

    def update(self):
        self.v *= .9
        self.w *= .8
        self.pos += self.v
        self.theta += self.w
        self.reload = max(0, self.reload - 1/60)

    def get_hitbox(self):
        h = robot_hitbox
        corners = []
        for x, y in [(-h, -h), (h, -h), (h, h), (-h, h)]:
            corners.append(self.pos + Vector2(x, y).rotate(-self.theta))
        return corners

    def collide_walls(self):
        corners = self.get_hitbox()
        xs = [c.x for c in corners]
        ys = [c.y for c in corners]

        if min(xs) < 0:
            self.pos.x += -min(xs)
            self.v.x = 0
        if max(xs) > WIDTH:
            self.pos.x -= max(xs) - WIDTH
            self.v.x = 0
        if min(ys) < 0:
            self.pos.y += -min(ys)
            self.v.y = 0
        if max(ys) > HEIGHT:
            self.pos.y -= max(ys) - HEIGHT
            self.v.y = 0

    # returns the unit vector forward
    def forward(self):
        return Vector2(-1, 0).rotate(-self.theta)

class Pumpkin:
    camera_height = 60**2 / 2

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
            self.v *= .5
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
    for i in range(-4, 5):
        for j in range(-10, 11):
            pumpkins.append(Pumpkin(Vector2(WIDTH/2 + i * 24, HEIGHT/2 + j * 24)))


    target = Vector2(WIDTH/4, HEIGHT/2)

    running = True
    while running:    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()      

            if event.type == pygame.MOUSEBUTTONDOWN:
                window_w, window_h = pygame.display.get_window_size()
                mx, my = event.pos
                target.x = mx * WIDTH / window_w
                target.y = my * HEIGHT / window_h

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
        player.collide_walls()
        pygame.draw.polygon(screen, (0, 255, 0), player.get_hitbox(), 1)

        if keys[pygame.K_SPACE] and player.held > 0 and player.reload == 0:
            v_up = random.randint(25, 35)
            tof = 2 * v_up
            v = (target - player.pos).normalize() * target.distance_to(player.pos) / tof
            v += .05 * player.v
            pumpkins.append(Pumpkin(player.pos.copy(), v, v_up))
            player.reload = .1
            player.held -= 1

        if keys[pygame.K_LSHIFT]:
            taken = []
            for p in pumpkins:
                if player.held == player.capacity:
                    break
                if p.v_up == 0 and (-1 * player.forward()).dot((p.pos - player.pos)) > .5 and p.pos.distance_to(player.pos - player.forward()) < 4 * p.r:
                    taken.append(p)
                    player.held+=1
            for t in taken:
                pumpkins.remove(t)

        for p in pumpkins:
            p.update()


        screen.fill((0,0,0))

        player_rotated = pygame.transform.rotate(player_image, player.theta)
        screen.blit(player_rotated, player_rotated.get_rect(center=player.pos))
        pygame.draw.circle(screen, (255, 255, 255), target, 5)

        for p in pumpkins:
            pygame.draw.circle(screen, (254, 117, 24), p.pos, p.r)

        font = pygame.font.Font(None, 50)
        text_surface = font.render(str(player.held) + "/" + str(player.capacity) + " held", False, (255, 255, 255))
        screen.blit(text_surface, (10, HEIGHT - 50))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())