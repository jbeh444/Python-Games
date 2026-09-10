import math
import random
import pygame

# --- Configuration ---
WIDTH, HEIGHT = 1200, 750
FPS = 60

BG_COLOR = (20, 22, 28)
WATER_COLOR = (20, 80, 140)
RED_TEAM = (230, 50, 50)
BLUE_TEAM = (50, 130, 240)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 95, 105)
DARK_GRAY = (40, 45, 55)
YELLOW = (255, 210, 40)
ORANGE = (255, 110, 20)
PURPLE = (170, 60, 230)
CYAN = (40, 220, 230)

GROUND_Y = 620
WATER_LEVEL_Y = 580
BLOCK_SIZE = 22

# --- Particle System ---

class Particle:
    def __init__(self, x, y, color, size, lifetime, vx=None, vy=None):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.vx = vx if vx is not None else random.uniform(-2, 2)
        self.vy = vy if vy is not None else random.uniform(-2, 2)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, surface):
        if self.lifetime > 0 and self.size > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))


def create_explosion(x, y, particles_list, count=12, radius=20):
    colors = [ORANGE, YELLOW, RED_TEAM, DARK_GRAY, WHITE]
    for _ in range(count):
        speed = random.uniform(1, max(2, radius / 5))
        angle = random.uniform(0, 2 * math.pi)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice(colors)
        size = random.uniform(2, max(3, radius / 8))
        lifetime = random.randint(12, 25)
        particles_list.append(Particle(x, y, color, size, lifetime, vx, vy))


# --- Selection & Spawning Box ---

class ControlledBallDrop:
    def __init__(self, x, y, width, height, team):
        self.rect = pygame.Rect(x, y, width, height)
        self.team = team
        self.ball = None
        self.drop_timer = 0
        self.drop_delay = 50

        slot_w = (width - 20) // 4
        self.slots = []
        types = ['body', 'gun', 'saw', 'flame']
        colors = [WHITE, YELLOW, PURPLE, ORANGE]

        for i in range(4):
            sx = self.rect.left + 5 + i * (slot_w + 3)
            sy = self.rect.bottom - 22
            rect = pygame.Rect(sx, sy, slot_w, 18)
            self.slots.append((rect, types[i], colors[i]))

        self.spawn_ball()

    def spawn_ball(self):
        bx = self.rect.left + random.randint(20, self.rect.width - 20)
        by = self.rect.top + 10
        self.ball = {'x': bx, 'y': by, 'vy': 2.5}

    def update(self):
        if not self.ball:
            self.drop_timer += 1
            if self.drop_timer >= self.drop_delay:
                self.drop_timer = 0
                self.spawn_ball()
            return None

        self.ball['y'] += self.ball['vy']
        ball_rect = pygame.Rect(self.ball['x'] - 5, self.ball['y'] - 5, 10, 10)

        for slot_rect, slot_type, _ in self.slots:
            if slot_rect.colliderect(ball_rect):
                self.ball = None
                return slot_type

        if self.ball and self.ball['y'] >= self.rect.bottom - 5:
            self.ball = None

        return None

    def draw(self, surface, font):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        pygame.draw.rect(surface, DARK_GRAY, self.rect)
        pygame.draw.rect(surface, color, self.rect, 2)

        for slot_rect, slot_type, s_color in self.slots:
            pygame.draw.rect(surface, s_color, slot_rect)
            pygame.draw.rect(surface, BLACK, slot_rect, 1)
            lbl = font.render(slot_type[0].upper(), True, BLACK)
            surface.blit(lbl, lbl.get_rect(center=slot_rect.center))

        if self.ball:
            pygame.draw.circle(surface, color, (int(self.ball['x']), int(self.ball['y'])), 5)


# --- Base Architecture with Shapes ---

class BaseBlock:
    def __init__(self, gx, gy, block_type='standard', shape='square', offset_y=0):
        self.gx = gx
        self.gy = gy
        self.block_type = block_type
        self.shape = shape
        self.is_core = (block_type == 'core')
        self.is_gun = (block_type == 'turret')
        self.is_silo = (block_type == 'silo')

        self.max_hp = 300 if self.is_core else (200 if block_type == 'outer' else 120)
        self.hp = self.max_hp
        self.rect = pygame.Rect(gx * BLOCK_SIZE, gy * BLOCK_SIZE + offset_y, BLOCK_SIZE, BLOCK_SIZE)
        self.shoot_cooldown = random.randint(0, 30)
        self.angle = 0

    def draw(self, surface, team_color):
        color = YELLOW if self.is_core else (GRAY if (self.is_gun or self.is_silo) else team_color)

        if self.shape == 'square':
            pygame.draw.rect(surface, color, self.rect)
            pygame.draw.rect(surface, BLACK, self.rect, 1)

        elif self.shape == 'slope_left':
            pts = [self.rect.bottomleft, self.rect.bottomright, self.rect.topright]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, BLACK, pts, 1)

        elif self.shape == 'slope_right':
            pts = [self.rect.bottomleft, self.rect.bottomright, self.rect.topleft]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, BLACK, pts, 1)

        elif self.shape == 'dome':
            pygame.draw.arc(surface, CYAN, self.rect, 0, math.pi, 3)
            pygame.draw.circle(surface, color, self.rect.center, 6)

        elif self.shape == 'antenna':
            pygame.draw.line(surface, GRAY, (self.rect.centerx, self.rect.bottom), (self.rect.centerx, self.rect.top - 6), 3)
            pygame.draw.circle(surface, RED_TEAM, (self.rect.centerx, self.rect.top - 6), 3)

        if self.is_core:
            pygame.draw.circle(surface, RED_TEAM, self.rect.center, 8)
            pygame.draw.circle(surface, WHITE, self.rect.center, 4)
        elif self.is_gun:
            end_x = self.rect.centerx + math.cos(self.angle) * 14
            end_y = self.rect.centery + math.sin(self.angle) * 14
            pygame.draw.line(surface, BLACK, self.rect.center, (end_x, end_y), 4)


class BreakableBase:
    def __init__(self, start_gx, team):
        self.team = team
        self.start_gx = start_gx
        self.blocks = []
        self.has_core = True
        self.missile_cooldown = 0
        self.build_shaped_structure()

    def build_shaped_structure(self):
        for x in range(8):
            for y in range(8):
                gy = (GROUND_Y // BLOCK_SIZE) - 1 - y
                gx = self.start_gx + x

                is_core = (x == 2 if self.team == 'red' else x == 5) and y == 1
                is_silo = (x == 4 if self.team == 'red' else x == 3) and y == 6
                is_gun = (y == 5 and x in [1, 6])

                shape = 'square'
                b_type = 'inner'

                if is_core:
                    b_type = 'core'
                elif is_silo:
                    b_type = 'silo'
                elif is_gun:
                    b_type = 'turret'
                elif y == 7 and x in [0, 7]:
                    shape = 'antenna'
                    b_type = 'decorative'
                elif y == 6 and x in [2, 5]:
                    shape = 'dome'
                    b_type = 'decorative'
                elif y == 4 and x == (7 if self.team == 'red' else 0):
                    shape = 'slope_left' if self.team == 'red' else 'slope_right'
                    b_type = 'outer'
                elif y == 0 and x in [0, 7]:
                    shape = 'slope_right' if self.team == 'red' else 'slope_left'
                    b_type = 'outer'

                self.blocks.append(BaseBlock(gx, gy, b_type, shape))

    def update_systems(self, enemy_mechs, projectiles, missiles):
        for b in self.blocks:
            if b.is_gun:
                target_mech = next((m for m in enemy_mechs if m.deployed and m.parts), None)
                if target_mech:
                    b.angle = math.atan2(target_mech.y - b.rect.centery, target_mech.x - b.rect.centerx)
                    b.shoot_cooldown += 1
                    if b.shoot_cooldown >= 45:
                        b.shoot_cooldown = 0
                        projectiles.append(AimedProjectile(b.rect.centerx, b.rect.centery, b.angle, self.team, damage=12))

        self.missile_cooldown += 1
        if self.missile_cooldown >= 210:
            silo_block = next((b for b in self.blocks if b.is_silo), None)
            if silo_block:
                self.missile_cooldown = 0
                missiles.append(HomingMissile(silo_block.rect.centerx, silo_block.rect.top, self.team))

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        for block in self.blocks:
            block.draw(surface, color)

    def damage_at(self, rect, amount, particles):
        hit = False
        for block in list(self.blocks):
            if block.rect.colliderect(rect):
                hit = True
                block.hp -= amount
                create_explosion(block.rect.centerx, block.rect.centery, particles, count=4, radius=12)
                if block.hp <= 0:
                    if block.is_core:
                        self.has_core = False
                    create_explosion(block.rect.centerx, block.rect.centery, particles, count=15, radius=30)
                    self.blocks.remove(block)
        return hit


# --- Warship (Boat Battle Mode) ---

class Warship:
    def __init__(self, start_gx, team):
        self.team = team
        self.start_gx = start_gx
        self.blocks = []
        self.has_core = True
        self.is_sinking = False
        self.sink_offset = 0
        self.missile_cooldown = 0
        self.build_ship()

    def build_ship(self):
        # 12 Wide x 5 High Warship design
        ship_layout = [
            "  A  T T  A ",
            " S  CCCC  S ",
            "DDDDDXDDDDDD",
            " HHHHHHHHHH ",
            "  HHHHHHHH  "
        ]

        for y, row in enumerate(ship_layout):
            for x, char in enumerate(row):
                if char == ' ':
                    continue
                gx = self.start_gx + x
                gy = (WATER_LEVEL_Y // BLOCK_SIZE) - 3 + y

                b_type = 'inner'
                shape = 'square'

                if char == 'X':
                    b_type = 'core'
                elif char == 'T':
                    b_type = 'turret'
                elif char == 'S':
                    b_type = 'silo'
                elif char == 'A':
                    shape = 'antenna'
                    b_type = 'decorative'
                elif char == 'D':
                    b_type = 'outer'

                self.blocks.append(BaseBlock(gx, gy, b_type, shape))

    def update_systems(self, enemy_mechs, projectiles, missiles, particles):
        if self.is_sinking:
            self.sink_offset += 0.8
            for b in self.blocks:
                b.rect.y += 0.8
            if random.random() < 0.3:
                rx = self.start_gx * BLOCK_SIZE + random.randint(0, 250)
                ry = WATER_LEVEL_Y + random.randint(0, 40)
                particles.append(Particle(rx, ry, CYAN, random.randint(3, 8), 20, vy=-1))

            if self.sink_offset > 120:
                self.blocks.clear()
            return

        for b in self.blocks:
            if b.is_gun:
                target_mech = next((m for m in enemy_mechs if m.deployed and m.parts), None)
                if target_mech:
                    b.angle = math.atan2(target_mech.y - b.rect.centery, target_mech.x - b.rect.centerx)
                    b.shoot_cooldown += 1
                    if b.shoot_cooldown >= 40:
                        b.shoot_cooldown = 0
                        projectiles.append(AimedProjectile(b.rect.centerx, b.rect.centery, b.angle, self.team, damage=14))

        self.missile_cooldown += 1
        if self.missile_cooldown >= 200:
            silo_block = next((b for b in self.blocks if b.is_silo), None)
            if silo_block:
                self.missile_cooldown = 0
                missiles.append(HomingMissile(silo_block.rect.centerx, silo_block.rect.top, self.team))

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        for block in self.blocks:
            block.draw(surface, color)

    def damage_at(self, rect, amount, particles):
        hit = False
        for block in list(self.blocks):
            if block.rect.colliderect(rect):
                hit = True
                block.hp -= amount
                create_explosion(block.rect.centerx, block.rect.centery, particles, count=4, radius=12)
                if block.hp <= 0:
                    if block.is_core:
                        self.has_core = False
                        self.is_sinking = True
                    create_explosion(block.rect.centerx, block.rect.centery, particles, count=18, radius=35)
                    self.blocks.remove(block)
        return hit


# --- Projectiles & Missiles ---

class AimedProjectile:
    def __init__(self, x, y, angle, team, damage=10):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * 8
        self.vy = math.sin(angle) * 8
        self.team = team
        self.damage = damage
        self.rect = pygame.Rect(x - 3, y - 3, 6, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 4)


class HomingMissile:
    def __init__(self, x, y, team):
        self.x = x
        self.y = y
        self.team = team
        self.speed = 6.0
        self.angle = -math.pi / 2
        self.blast_radius = 38
        self.damage = 45
        self.rect = pygame.Rect(x - 5, y - 5, 10, 10)

    def update(self, enemy_mechs, enemy_base, particles):
        particles.append(Particle(self.x, self.y, ORANGE, 4, 8, vx=random.uniform(-1, 1), vy=random.uniform(-1, 1)))

        target_x, target_y = None, None
        closest_dist = 9999

        for m in enemy_mechs:
            if m.deployed and m.parts:
                dist = math.hypot(m.x - self.x, m.y - self.y)
                if dist < closest_dist:
                    closest_dist = dist
                    target_x, target_y = m.x, m.y

        if not target_x:
            target_x = enemy_base.start_gx * BLOCK_SIZE + 80
            target_y = WATER_LEVEL_Y - 40

        desired_angle = math.atan2(target_y - self.y, target_x - self.x)
        angle_diff = (desired_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += max(-0.06, min(0.06, angle_diff))

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.rect.center = (int(self.x), int(self.y))

    def explode(self, enemy_mechs, enemy_base, particles):
        create_explosion(self.x, self.y, particles, count=25, radius=self.blast_radius)

        for m in enemy_mechs:
            if m.deployed:
                for my_rect, _, _, my_rel in m.get_hitboxes():
                    if math.hypot(my_rect.centerx - self.x, my_rect.centery - self.y) <= self.blast_radius:
                        m.damage_part(my_rel, self.damage, particles)

        for b in list(enemy_base.blocks):
            if math.hypot(b.rect.centerx - self.x, b.rect.centery - self.y) <= self.blast_radius:
                b.hp -= self.damage
                if b.hp <= 0:
                    if b.is_core:
                        enemy_base.has_core = False
                        if hasattr(enemy_base, 'is_sinking'):
                            enemy_base.is_sinking = True
                    enemy_base.blocks.remove(b)

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        end_x = self.x - math.cos(self.angle) * 10
        end_y = self.y - math.sin(self.angle) * 10
        pygame.draw.line(surface, color, (self.x, self.y), (end_x, end_y), 4)
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), 3)


# --- Mech Unit ---

class Mech:
    def __init__(self, team, zone_rect, floor_y=GROUND_Y):
        self.team = team
        self.zone = zone_rect
        self.parts = []
        self.deployed = False
        self.floor_y = floor_y
        self.x = zone_rect.centerx
        self.y = floor_y - BLOCK_SIZE
        self.dir = 1 if team == 'red' else -1
        self.parts.append([0, 0, 'body', 100, 0])

    def add_part(self, part_type):
        if self.deployed:
            return

        existing_coords = {(p[0], p[1]) for p in self.parts}
        candidates = []

        for px, py, _, _, _ in self.parts:
            for dx, dy in [(0, -1), (1, 0), (-1, 0), (0, 1)]:
                nx, ny = px + dx, py + dy
                if (nx, ny) not in existing_coords and ny <= 0:
                    candidates.append((nx, ny))

        if candidates:
            chosen = random.choice(candidates)
            hp = 120 if part_type == 'body' else 70
            self.parts.append([chosen[0], chosen[1], part_type, hp, 0])

        if len(self.parts) >= 6:
            self.deployed = True

    def get_hitboxes(self):
        hitboxes = []
        for px, py, ptype, hp, _ in self.parts:
            bx = int(self.x) + px * BLOCK_SIZE
            by = int(self.y) + py * BLOCK_SIZE
            hitboxes.append((pygame.Rect(bx, by, BLOCK_SIZE, BLOCK_SIZE), ptype, hp, (px, py)))
        return hitboxes

    def damage_part(self, rel_coord, damage, particles):
        for part in list(self.parts):
            if (part[0], part[1]) == rel_coord:
                part[3] -= damage
                if part[3] <= 0:
                    bx = int(self.x) + part[0] * BLOCK_SIZE
                    by = int(self.y) + part[1] * BLOCK_SIZE
                    create_explosion(bx, by, particles, count=8, radius=18)
                    self.parts.remove(part)
                break

    def update(self, enemy_base, enemy_mechs, projectiles, particles):
        if not self.deployed or not self.parts:
            return

        for part in self.parts:
            if part[2] == 'gun':
                part[4] += 1
                if part[4] >= 30:
                    part[4] = 0
                    gx = int(self.x) + part[0] * BLOCK_SIZE + BLOCK_SIZE // 2
                    gy = int(self.y) + part[1] * BLOCK_SIZE + BLOCK_SIZE // 2
                    angle = math.atan2(self.floor_y - 50 - gy, (enemy_base.start_gx * BLOCK_SIZE) - gx)
                    projectiles.append(AimedProjectile(gx, gy, angle, self.team, damage=14))

        for p in list(projectiles):
            if p.team != self.team:
                for my_rect, _, _, my_rel in self.get_hitboxes():
                    if my_rect.colliderect(p.rect):
                        self.damage_part(my_rel, p.damage, particles)
                        if p in projectiles:
                            projectiles.remove(p)

        fighting = False
        for enemy in enemy_mechs:
            if enemy.deployed and enemy.parts:
                for my_rect, my_type, _, my_rel in self.get_hitboxes():
                    for enemy_rect, enemy_type, _, enemy_rel in enemy.get_hitboxes():
                        if my_rect.colliderect(enemy_rect):
                            fighting = True
                            enemy.damage_part(enemy_rel, 2.0, particles)

        touching_base = False
        for my_rect, ptype, _, _ in self.get_hitboxes():
            if enemy_base.damage_at(my_rect, 2.0, particles):
                touching_base = True

        if not fighting and not touching_base:
            self.x += 1.5 * self.dir

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        for px, py, ptype, _, _ in self.parts:
            bx = int(self.x) + px * BLOCK_SIZE
            by = int(self.y) + py * BLOCK_SIZE
            rect = pygame.Rect(bx, by, BLOCK_SIZE, BLOCK_SIZE)

            pygame.draw.rect(surface, color if ptype == 'body' else GRAY, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)


# --- Game Engine Loop ---

def run_game(mode="NORMAL"):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Mech Warfare - Mode: {mode}")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 20)
    large_font = pygame.font.SysFont(None, 60)

    floor_y = WATER_LEVEL_Y - 22 if mode == "BOAT" else GROUND_Y

    if mode == "BOAT":
        red_base = Warship(start_gx=1, team='red')
        blue_base = Warship(start_gx=(WIDTH // BLOCK_SIZE) - 13, team='blue')
    else:
        red_base = BreakableBase(start_gx=1, team='red')
        blue_base = BreakableBase(start_gx=(WIDTH // BLOCK_SIZE) - 9, team='blue')

    red_rand = ControlledBallDrop(80, 20, 150, 90, 'red')
    blue_rand = ControlledBallDrop(WIDTH - 230, 20, 150, 90, 'blue')

    red_zone = pygame.Rect(200, floor_y - 120, 100, 120)
    blue_zone = pygame.Rect(WIDTH - 300, floor_y - 120, 100, 120)

    red_mechs = [Mech('red', red_zone, floor_y)]
    blue_mechs = [Mech('blue', blue_zone, floor_y)]

    projectiles = []
    missiles = []
    particles = []

    game_over = False
    winner = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                return True  # Restart current game mode

        if not game_over:
            r_part = red_rand.update()
            if r_part:
                if red_mechs[-1].deployed:
                    red_mechs.append(Mech('red', red_zone, floor_y))
                red_mechs[-1].add_part(r_part)

            b_part = blue_rand.update()
            if b_part:
                if blue_mechs[-1].deployed:
                    blue_mechs.append(Mech('blue', blue_zone, floor_y))
                blue_mechs[-1].add_part(b_part)

            if mode == "BOAT":
                red_base.update_systems(blue_mechs, projectiles, missiles, particles)
                blue_base.update_systems(red_mechs, projectiles, missiles, particles)
            else:
                red_base.update_systems(blue_mechs, projectiles, missiles)
                blue_base.update_systems(red_mechs, projectiles, missiles)

            for m in list(missiles):
                targets_mechs = blue_mechs if m.team == 'red' else red_mechs
                target_base = blue_base if m.team == 'red' else red_base

                m.update(targets_mechs, target_base, particles)

                collided = False
                for mech in targets_mechs:
                    if mech.deployed:
                        for rect, _, _, _ in mech.get_hitboxes():
                            if rect.colliderect(m.rect):
                                collided = True
                                break

                if collided or target_base.damage_at(m.rect, 10, particles) or m.y >= floor_y:
                    m.explode(targets_mechs, target_base, particles)
                    if m in missiles:
                        missiles.remove(m)

            for p in list(projectiles):
                p.update()
                if p.x < 0 or p.x > WIDTH or p.y < 0 or p.y > HEIGHT:
                    projectiles.remove(p)

            for m in list(red_mechs):
                m.update(blue_base, blue_mechs, projectiles, particles)
                if not m.parts:
                    red_mechs.remove(m)

            for m in list(blue_mechs):
                m.update(red_base, red_mechs, projectiles, particles)
                if not m.parts:
                    blue_mechs.remove(m)

            for p in list(particles):
                p.update()
                if p.lifetime <= 0:
                    particles.remove(p)

            if not red_mechs or red_mechs[-1].deployed:
                red_mechs.append(Mech('red', red_zone, floor_y))
            if not blue_mechs or blue_mechs[-1].deployed:
                blue_mechs.append(Mech('blue', blue_zone, floor_y))

            if not blue_base.has_core:
                game_over = True
                winner = "RED"
            elif not red_base.has_core:
                game_over = True
                winner = "BLUE"

        # Frame Render
        screen.fill(BG_COLOR)

        if mode == "BOAT":
            pygame.draw.rect(screen, WATER_COLOR, (0, WATER_LEVEL_Y, WIDTH, HEIGHT - WATER_LEVEL_Y))
            pygame.draw.line(screen, CYAN, (0, WATER_LEVEL_Y), (WIDTH, WATER_LEVEL_Y), 3)
        else:
            pygame.draw.line(screen, GRAY, (0, GROUND_Y), (WIDTH, GROUND_Y), 4)

        red_base.draw(screen)
        blue_base.draw(screen)

        for m in red_mechs + blue_mechs:
            m.draw(screen)

        for p in projectiles:
            p.draw(screen)

        for m in missiles:
            m.draw(screen)

        for p in particles:
            p.draw(screen)

        red_rand.draw(screen, font)
        blue_rand.draw(screen, font)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            txt = large_font.render(f"{winner} TEAM WINS!", True, WHITE)
            rst = font.render("Press 'R' to Restart Current Game Mode", True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 30))
            screen.blit(rst, (WIDTH // 2 - rst.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()
        clock.tick(FPS)

    return False


# --- Start Menu ---

def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mech Warfare - Main Menu")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 70)
    btn_font = pygame.font.SysFont(None, 40)

    btn_normal = pygame.Rect(WIDTH // 2 - 150, 280, 300, 65)
    btn_boat = pygame.Rect(WIDTH // 2 - 150, 380, 300, 65)

    while True:
        screen.fill(BG_COLOR)

        title_lbl = title_font.render("MECH WARFARE", True, YELLOW)
        screen.blit(title_lbl, (WIDTH // 2 - title_lbl.get_width() // 2, 130))

        m_pos = pygame.mouse.get_pos()

        # Normal Battle Button
        norm_color = RED_TEAM if btn_normal.collidepoint(m_pos) else DARK_GRAY
        pygame.draw.rect(screen, norm_color, btn_normal, border_radius=8)
        pygame.draw.rect(screen, WHITE, btn_normal, 2, border_radius=8)
        lbl1 = btn_font.render("Normal Battle", True, WHITE)
        screen.blit(lbl1, lbl1.get_rect(center=btn_normal.center))

        # Boat Battle Button
        boat_color = BLUE_TEAM if btn_boat.collidepoint(m_pos) else DARK_GRAY
        pygame.draw.rect(screen, boat_color, btn_boat, border_radius=8)
        pygame.draw.rect(screen, WHITE, btn_boat, 2, border_radius=8)
        lbl2 = btn_font.render("Boat Battle", True, WHITE)
        screen.blit(lbl2, lbl2.get_rect(center=btn_boat.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_normal.collidepoint(event.pos):
                    while run_game("NORMAL"):
                        pass
                elif btn_boat.collidepoint(event.pos):
                    while run_game("BOAT"):
                        pass

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main_menu()