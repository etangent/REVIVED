from cmath import rect
import pygame
import random
import math
import asyncio
from pygame.math import Vector2

WIDTH, HEIGHT = 1400, 900
robot_hitbox = 30

class Robot:
    def __init__(self, pos, theta=0, w=0, capacity = 70):
        self.pos = pos
        self.v = Vector2(0, 0)
        self.theta = theta
        self.w = w
        self.held = 8
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

    # obstacles should be (pos, radius)
    def align(self, desiredPos, desiredTheta, obstacles=[], maxSpeed=10000):
        to_goal = desiredPos - self.pos
        dist_to_goal = to_goal.length()
        
        if dist_to_goal > 1:
            attract = to_goal.normalize() * (min(dist_to_goal * 0.1, 3.0) - 0.2 * self.v.project((to_goal)).length())
        else:
            attract = Vector2(0, 0)

        repel = Vector2(0, 0)
        swerve = Vector2(0, 0)

        for o_pos, o_radius in obstacles:
            to_obs = self.pos - o_pos
            dist = to_obs.length()
            
            speed_buffer = self.v.length() * 20 
            safe_dist = o_radius + 45 + speed_buffer
            
            if 0 < dist < safe_dist:
                repel_magnitude = (1.0 / dist - 1.0 / safe_dist) * 400.0
                repel += to_obs.normalize() * repel_magnitude
                
                tangent = Vector2(-to_obs.y, to_obs.x).normalize()
                
                if self.v.dot(tangent) < 0:
                    tangent = -tangent
                if to_obs.normalize().dot(self.v.normalize()) > 0:
                    tangent = Vector2(0, 0)

                swerve += tangent * repel_magnitude * 1.5

        accel = attract + repel + swerve
        if accel.length() > 0:
            accel = accel.normalize() * min(accel.length(), 2.5)

        if self.v.length() > maxSpeed:
            accel = Vector2(0, 0)
        self.v += accel

        error = (desiredTheta - self.theta + 180) % 360 - 180
        alpha = 1.5 * error - 0.1 * self.w
        self.w += min(max(alpha, -2), 2)

        

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
    else:
        return ("done", 0)

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    clock = pygame.time.Clock()

    player_image = pygame.image.load("assets/player.png").convert_alpha()
    player_image = pygame.transform.scale(player_image, (60, 60))
    enemy_image = pygame.image.load("assets/player.png").convert_alpha()
    enemy_image = pygame.transform.scale(enemy_image, (60, 60))


    bg_image = pygame.image.load("assets/field.png").convert_alpha()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))

    player = Robot(Vector2(200, 100))
    enemy = Robot(Vector2(WIDTH - 200, HEIGHT - 100))

    player_hub = Hub(Vector2(WIDTH / 4 - 20, HEIGHT/2))
    enemy_hub = Hub(Vector2(3* WIDTH / 4 + 20, HEIGHT/2))

    pumpkins = []
    for i in range(-4, 5):
        for j in range(-10, 11):
            pumpkins.append(Pumpkin(Vector2(WIDTH/2 + i * 24, HEIGHT/2 + j * 24)))


    target = Vector2(WIDTH/4, HEIGHT/2)

    timer = 0
    player_score = 0
    enemy_score = 0
    running = True
    player_auto_status = None
    enemy_auto_status = None
    while running and timer < 160:
        if abs(timer - 20) < .25:
            if player_score > enemy_score:
                player_auto_status = "winner"
                enemy_auto_status = "loser"
            else:
                player_auto_status = "loser"
                enemy_auto_status = "winner"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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
                if shift(timer)[0] != enemy_auto_status:
                    player_score += 1
            if enemy_hub.pos.distance_to(p.pos) < 75 and p.height < 5:
                enemy_hub.held += 1
                taken.append(p)
                if shift(timer)[0] != player_auto_status:
                    enemy_score += 1
        for t in taken:
            pumpkins.remove(t)

        closest = Vector2(0, 0)
        if player_hub.held > 0 and random.randint(0, 6 - min(6, player_hub.held)) == 0:
            pumpkins.append(Pumpkin(player_hub.pos + Vector2(80, 0), Vector2(1, 0).rotate(random.uniform(-45, 45)) * random.uniform(3, 10)))
            player_hub.held -= 1
        if enemy_hub.held > 0 and random.randint(0, 6 - min(6, enemy_hub.held)) == 0:
            pumpkins.append(Pumpkin(enemy_hub.pos - Vector2(80, 0), Vector2(-1, 0).rotate(random.uniform(-45, 45)) * random.uniform(3, 10)))
            enemy_hub.held -= 1
        if shift(timer + 2)[0] != player_auto_status and (enemy.held == enemy.capacity or (enemy.held > 0 and enemy.pos.x > enemy_hub.pos.x + 100)):
            enemy.align(enemy_hub.pos + Vector2(200, 0), enemy.theta, [(player_hub.pos, 75), (enemy_hub.pos, 75)])
            if enemy.reload == 0 and enemy.pos.x > enemy_hub.pos.x + 100:
                target = Vector2(enemy_hub.pos)
                v_up = random.randint(25, 35)
                tof = 2 * v_up
                v = (target - enemy.pos).normalize() * target.distance_to(enemy.pos) / tof
                v += .05 * enemy.v
                pumpkins.append(Pumpkin(enemy.pos.copy(), v, v_up))
                enemy.reload = .1
                enemy.held -= 1
        elif enemy.held < enemy.capacity and pumpkins:
            if enemy.v.length() > 0.5:
                move_dir = enemy.v.normalize()
            else:
                move_dir = -enemy.forward()
            closest = min(pumpkins, key=lambda x: x.pos.distance_to(enemy.pos) + 100000 * x.height + .3 * move_dir.dot((x.pos - enemy.pos).normalize() if x.pos != enemy.pos else Vector2(0,0)))

            diffVector = closest.pos - enemy.pos
            dist = diffVector.length()

            if dist > 0:
                target_theta = -math.degrees(math.atan2(diffVector.y, diffVector.x))
            else:
                target_theta = enemy.theta

            enemy.align(closest.pos, target_theta, [(player_hub.pos, 75), (enemy_hub.pos, 75)])            
        else:
            enemy.align(player.pos, enemy.theta + 1, [(player_hub.pos, 75), (enemy_hub.pos, 75)])

        enemy.update()
        enemy.collide_walls()
        taken = []
        for p in pumpkins:
            if enemy.held == enemy.capacity or enemy.intake_reload >= .15:
                break
            if p.v_up == 0 and (-1 * enemy.forward()).dot((p.pos - enemy.pos).normalize()) > .7 and p.pos.distance_to(enemy.pos - enemy.forward()) < 4 * p.r:
                taken.append(p)
                enemy.held+=1
                enemy.intake_reload += .03
        for t in taken:
            pumpkins.remove(t)


        screen.fill((0,0,0))
        screen.blit(bg_image, (0, 0))

        player_rotated = pygame.transform.rotate(player_image, player.theta)
        screen.blit(player_rotated, player_rotated.get_rect(center=player.pos))
        enemy_rotated = pygame.transform.rotate(enemy_image, enemy.theta)
        screen.blit(enemy_rotated, enemy_rotated.get_rect(center=enemy.pos))

        for p in pumpkins:
            pygame.draw.circle(screen, (254, 117, 24), p.pos, p.r)

        font = pygame.font.Font(None, 50)
        text_surface = font.render(str(player.held) + "/" + str(player.capacity) + " held", False, (255, 255, 255))
        screen.blit(text_surface, (10, HEIGHT - 50))
        text_surface = font.render("Your Score: " + str(player_score), False, (255, 255, 255))
        screen.blit(text_surface, (10, 0))
        text_surface = font.render("Enemy Score: " + str(enemy_score), False, (255, 255, 255))
        screen.blit(text_surface, (WIDTH - 300, 0))
        curr_shift = shift(timer)[0]
        if curr_shift == "winner" or curr_shift == "loser":
            if player_auto_status == curr_shift:
                curr_shift = "player"
            if enemy_auto_status == curr_shift:
                curr_shift = "enemy"
        text_surface = font.render("Shift: " + curr_shift + ", " + str(shift(timer)[1]), False, (255, 255, 255))
        screen.blit(text_surface, (WIDTH - 400, HEIGHT - 50))

        if closest:
            pygame.draw.circle(screen, (0, 0, 255), closest.pos, 10)

        pygame.display.flip()
        clock.tick(60)
        timer += 1/60
        await asyncio.sleep(0)

    screen.fill((0, 0, 0))
    winner = "player"
    if enemy_score > player_score:
        winner = "enemy"
    font = pygame.font.Font(None, 100)
    text_surface = font.render(winner + " wins!", False, (255, 255, 255))
    screen.blit(text_surface, (WIDTH/2 - 200, HEIGHT / 2))
    text_surface = font.render("Your Score: " + str(player_score), False, (255, 255, 255))
    screen.blit(text_surface, (10, 0))
    text_surface = font.render("Enemy Score: " + str(enemy_score), False, (255, 255, 255))  
    screen.blit(text_surface, (WIDTH - 600, 0))
    pygame.display.flip()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()      
            clock.tick(60)
            await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())