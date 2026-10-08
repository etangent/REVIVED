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
        self.intake_reload = 0
        self.capacity = capacity

    def update(self):
        self.v *= .9
        self.w *= .8
        self.pos += self.v
        self.theta += self.w
        self.reload = max(0, self.reload - 1/60)
        self.intake_reload = max(0, self.intake_reload - 1/60)

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
            self.v *= .98
            return

        if self.height < 0:
            self.height = 0
            self.v_up = 0
            return

        self.v_up -= 1
        self.r = 10 * self.camera_height / (self.camera_height - self.height)

class Hub:
    def __init__(self, pos):
        self.pos = pos
        self.held = 0

def shift(time):
    if (time < 20):
        return ("auto", math.floor(20 - time))
    elif (time < 30):
        return ("transition", math.floor(30 - time))
    elif (time < 55):
        return ("loser", math.floor(55 - time))
    elif (time < 80):
        return ("winner", math.floor(80 - time))
    elif (time < 105):
        return ("loser", math.floor(105 - time))
    elif (time < 130):
        return ("winner", math.floor(130 - time))
    elif (time < 160):
        return ("endgame", math.floor(160 - time))

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    clock = pygame.time.Clock()

    player_image = pygame.image.load("assets/player.png").convert_alpha()
    player_image = pygame.transform.scale(player_image, (60, 60))
    bg_image = pygame.image.load("assets/field.png").convert_alpha()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))

    player = Robot(Vector2(WIDTH/2 +.1, HEIGHT/2))

    player_hub = Hub(Vector2(WIDTH / 4 - 20, HEIGHT/2))
    enemy_hub = Hub(Vector2(3* WIDTH / 4 + 20, HEIGHT/2))

    pumpkins = []
    for i in range(-4, 5):
        for j in range(-10, 11):
            pumpkins.append(Pumpkin(Vector2(WIDTH/2 + i * 24, HEIGHT/2 + j * 24)))


    target = Vector2(WIDTH/4, HEIGHT/2)

    timer = 0
    score = 0
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
        player.collide_walls()
        pygame.draw.polygon(screen, (0, 255, 0), player.get_hitbox(), 1)

        if keys[pygame.K_SPACE] and player.held > 0 and player.reload == 0:
            if player.pos.x > WIDTH / 4:
                if player.pos.y < HEIGHT / 2:
                    target = Vector2(WIDTH / 4, HEIGHT / 4)
                else:
                    target = Vector2(WIDTH / 4, 3 * HEIGHT / 4)
            else:
                target = Vector2(player_hub.pos)

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
                if player.held == player.capacity or player.intake_reload >= .15:
                    break
                if p.v_up == 0 and (-1 * player.forward()).dot((p.pos - player.pos).normalize()) > .7 and p.pos.distance_to(player.pos - player.forward()) < 4 * p.r:
                    taken.append(p)
                    player.held+=1
                    player.intake_reload += .03
            for t in taken:
                pumpkins.remove(t)

        taken = []
        for p in pumpkins:
            p.update()

            if player_hub.pos.distance_to(p.pos) < 75 and p.height < 5:
                player_hub.held += 1
                taken.append(p)
                if shift(timer)[0] != "loser":
                    score += 1
        for t in taken:
            pumpkins.remove(t)

        if player_hub.held > 0 and random.randint(0, 6 - min(6, player_hub.held)) == 0:
            pumpkins.append(Pumpkin(player_hub.pos + Vector2(80, 0), Vector2(1, 0).rotate(random.uniform(-45, 45)) * random.uniform(3, 10)))
            player_hub.held -= 1


        screen.fill((0,0,0))
        screen.blit(bg_image, (0, 0))

        player_rotated = pygame.transform.rotate(player_image, player.theta)
        screen.blit(player_rotated, player_rotated.get_rect(center=player.pos))

        for p in pumpkins:
            pygame.draw.circle(screen, (254, 117, 24), p.pos, p.r)

        font = pygame.font.Font(None, 50)
        text_surface = font.render(str(player.held) + "/" + str(player.capacity) + " held", False, (255, 255, 255))
        screen.blit(text_surface, (10, HEIGHT - 50))
        font = pygame.font.Font(None, 50)
        text_surface = font.render("Score: " + str(score), False, (255, 255, 255))
        screen.blit(text_surface, (10, 0))
        font = pygame.font.Font(None, 50)
        text_surface = font.render("Shift: " + shift(timer)[0] + ", " + str(shift(timer)[1]), False, (255, 255, 255))
        screen.blit(text_surface, (WIDTH - 500, HEIGHT - 50))

        pygame.display.flip()
        clock.tick(60)
        timer += 1/60
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())