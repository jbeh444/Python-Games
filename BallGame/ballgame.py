import math
import random
import pygame

# --- Configuration ---
WIDTH, HEIGHT = 1200, 750
FPS = 60

BG_COLOR = (20, 22, 28)
RED_TEAM = (230, 50, 50)
BLUE_TEAM = (50, 130, 240)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 95, 105)
DARK_GRAY = (40, 45, 55)
YELLOW = (255, 210, 40)
ORANGE = (255, 110, 20)
PURPLE = (170, 60, 230)

GROUND_Y = 620
BLOCK_SIZE = 22

# --- Particle & Effect System ---

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


def create_explosion(x, y, particles_list, count=15, radius=30):
    colors = [ORANGE, YELLOW, RED_TEAM, DARK_GRAY, WHITE]
    for _ in range(count):
        speed = random.uniform(1, radius / 8)
        angle = random.uniform(0, 2 * math.pi)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice(colors)
        size = random.uniform(3, radius / 6)
        lifetime = random.randint(15, 35)
        particles_list.append(Particle(x, y, color, size, lifetime, vx, vy))


# --- Selection & Spawning ---

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


# --- Base Structures ---

class BaseBlock:
    def __init__(self, gx, gy, block_type='standard'):
        self.gx = gx
        self.gy = gy
        self.block_type = block_type
        self.is_core = (block_type == 'core')
        self.is_gun = (block_type == 'turret')
        self.is_silo = (block_type == 'silo')

        self.max_hp = 500 if self.is_core else (250 if block_type == 'outer' else 150)
        self.hp = self.max_hp
        self.rect = pygame.Rect(gx * BLOCK_SIZE, gy * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        self.shoot_cooldown = random.randint(0, 30)
        self.angle = 0

    def draw(self, surface, team_color):
        color = YELLOW if self.is_core else (GRAY if (self.is_gun or self.is_silo) else team_color)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 1)

        if self.is_core:
            pygame.draw.circle(surface, RED_TEAM, self.rect.center, 7)
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
        self.build_structure()

    def build_structure(self):
        for x in range(8):
            for y in range(8):
                gy = (GROUND_Y // BLOCK_SIZE) - 1 - y
                gx = self.start_gx + x
                is_core = (x == 1 if self.team == 'red' else x == 6) and y == 0
                is_silo = (x == 3 if self.team == 'red' else x == 4) and y == 7
                is_gun = (y == 7 and x in [1, 6])

                b_type = 'core' if is_core else ('silo' if is_silo else ('turret' if is_gun else 'inner'))
                self.blocks.append(BaseBlock(gx, gy, b_type))

    def update_systems(self, enemy_mechs, projectiles, missiles):
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
        if self.missile_cooldown >= 180:
            silo_block = next((b for b in self.blocks if b.is_silo), None)
            if silo_block:
                self.missile_cooldown = 0
                missiles.append(HomingMissile(silo_block.rect.centerx, silo_block.rect.top, self.team))

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        for block in self.blocks:
            block.draw(surface, color)

    def damage_at(self, rect, amount, particles):
        for block in list(self.blocks):
            if block.rect.colliderect(rect):
                block.hp -= amount
                if block.hp <= 0:
                    if block.is_core:
                        self.has_core = False
                    create_explosion(block.rect.centerx, block.rect.centery, particles, count=12, radius=35)
                    self.blocks.remove(block)
                return True
        return False


# --- Projectiles & Homing Explosive Missiles ---

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
        self.speed = 7.0
        self.angle = -math.pi / 2
        self.blast_radius = 75
        self.damage = 120
        self.rect = pygame.Rect(x - 6, y - 6, 12, 12)

    def update(self, enemy_mechs, enemy_base, particles):
        # 1. Trail Particles
        particles.append(Particle(self.x, self.y, ORANGE, 5, 10, vx=random.uniform(-1, 1), vy=random.uniform(-1, 1)))

        # 2. Find Nearest Homing Target
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
            target_y = GROUND_Y - 50

        # 3. Steer Angle toward target
        desired_angle = math.atan2(target_y - self.y, target_x - self.x)
        angle_diff = (desired_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += max(-0.08, min(0.08, angle_diff))

        # Move forward
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.rect.center = (int(self.x), int(self.y))

    def explode(self, enemy_mechs, enemy_base, particles):
        create_explosion(self.x, self.y, particles, count=45, radius=self.blast_radius)

        # AOE Damage to Mechs
        for m in enemy_mechs:
            if m.deployed:
                for my_rect, _, _, my_rel in m.get_hitboxes():
                    if math.hypot(my_rect.centerx - self.x, my_rect.centery - self.y) <= self.blast_radius:
                        m.damage_part(my_rel, self.damage, particles)

        # AOE Damage to Base Blocks
        for b in list(enemy_base.blocks):
            if math.hypot(b.rect.centerx - self.x, b.rect.centery - self.y) <= self.blast_radius:
                b.hp -= self.damage
                if b.hp <= 0:
                    if b.is_core:
                        enemy_base.has_core = False
                    enemy_base.blocks.remove(b)

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        end_x = self.x - math.cos(self.angle) * 12
        end_y = self.y - math.sin(self.angle) * 12
        pygame.draw.line(surface, color, (self.x, self.y), (end_x, end_y), 5)
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), 4)


# --- Mech Unit ---

class Mech:
    def __init__(self, team, zone_rect):
        self.team = team
        self.zone = zone_rect
        self.parts = []
        self.deployed = False
        self.x = zone_rect.centerx
        self.y = GROUND_Y - BLOCK_SIZE
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
                    create_explosion(bx, by, particles, count=10, radius=20)
                    self.parts.remove(part)
                break

    def update(self, enemy_base, enemy_mechs, projectiles, particles):
        if not self.deployed or not self.parts:
            return

        # Fire Guns
        for part in self.parts:
            if part[2] == 'gun':
                part[4] += 1
                if part[4] >= 30:
                    part[4] = 0
                    gx = int(self.x) + part[0] * BLOCK_SIZE + BLOCK_SIZE // 2
                    gy = int(self.y) + part[1] * BLOCK_SIZE + BLOCK_SIZE // 2
                    angle = math.atan2(GROUND_Y - 50 - gy, (enemy_base.start_gx * BLOCK_SIZE) - gx)
                    projectiles.append(AimedProjectile(gx, gy, angle, self.team, damage=15))

        # Check Incoming Bullets
        for p in list(projectiles):
            if p.team != self.team:
                for my_rect, _, _, my_rel in self.get_hitboxes():
                    if my_rect.colliderect(p.rect):
                        self.damage_part(my_rel, p.damage, particles)
                        if p in projectiles:
                            projectiles.remove(p)

        # Movement / Melee
        fighting = False
        for enemy in enemy_mechs:
            if enemy.deployed and enemy.parts:
                for my_rect, my_type, _, my_rel in self.get_hitboxes():
                    for enemy_rect, enemy_type, _, enemy_rel in enemy.get_hitboxes():
                        if my_rect.colliderect(enemy_rect):
                            fighting = True
                            enemy.damage_part(enemy_rel, 2.0, particles)

        if not fighting:
            self.x += 1.5 * self.dir
            for my_rect, ptype, _, _ in self.get_hitboxes():
                enemy_base.damage_at(my_rect, 2.0, particles)

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM

        for px, py, ptype, _, _ in self.parts:
            bx = int(self.x) + px * BLOCK_SIZE
            by = int(self.y) + py * BLOCK_SIZE
            rect = pygame.Rect(bx, by, BLOCK_SIZE, BLOCK_SIZE)

            pygame.draw.rect(surface, color if ptype == 'body' else GRAY, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)


# --- Main Loop ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Homing Missile Warfare")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 20)
    large_font = pygame.font.SysFont(None, 60)

    red_base = BreakableBase(start_gx=1, team='red')
    blue_base = BreakableBase(start_gx=(WIDTH // BLOCK_SIZE) - 9, team='blue')

    red_rand = ControlledBallDrop(80, 20, 150, 90, 'red')
    blue_rand = ControlledBallDrop(WIDTH - 230, 20, 150, 90, 'blue')

    red_zone = pygame.Rect(200, GROUND_Y - 120, 100, 120)
    blue_zone = pygame.Rect(WIDTH - 300, GROUND_Y - 120, 100, 120)

    red_mechs = [Mech('red', red_zone)]
    blue_mechs = [Mech('blue', blue_zone)]

    projectiles = []
    missiles = []
    particles = []

    game_over = False
    winner = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                main()
                return

        if not game_over:
            # Assembly Controls
            r_part = red_rand.update()
            if r_part:
                if red_mechs[-1].deployed:
                    red_mechs.append(Mech('red', red_zone))
                red_mechs[-1].add_part(r_part)

            b_part = blue_rand.update()
            if b_part:
                if blue_mechs[-1].deployed:
                    blue_mechs.append(Mech('blue', blue_zone))
                blue_mechs[-1].add_part(b_part)

            # Systems Update
            red_base.update_systems(blue_mechs, projectiles, missiles)
            blue_base.update_systems(red_mechs, projectiles, missiles)

            # Update Missiles with Homing & Massive AOE Blast
            for m in list(missiles):
                targets_mechs = blue_mechs if m.team == 'red' else red_mechs
                target_base = blue_base if m.team == 'red' else red_base

                m.update(targets_mechs, target_base, particles)

                # Impact Conditions
                collided = False
                for mech in targets_mechs:
                    if mech.deployed:
                        for rect, _, _, _ in mech.get_hitboxes():
                            if rect.colliderect(m.rect):
                                collided = True
                                break

                if collided or target_base.damage_at(m.rect, 10, particles) or m.y >= GROUND_Y:
                    m.explode(targets_mechs, target_base, particles)
                    if m in missiles:
                        missiles.remove(m)

            # Update Projectiles
            for p in list(projectiles):
                p.update()
                if p.x < 0 or p.x > WIDTH or p.y < 0 or p.y > HEIGHT:
                    projectiles.remove(p)

            # Update Mechs
            for m in list(red_mechs):
                m.update(blue_base, blue_mechs, projectiles, particles)
                if not m.parts:
                    red_mechs.remove(m)

            for m in list(blue_mechs):
                m.update(red_base, red_mechs, projectiles, particles)
                if not m.parts:
                    blue_mechs.remove(m)

            # Particle Systems
            for p in list(particles):
                p.update()
                if p.lifetime <= 0:
                    particles.remove(p)

            # Ensure Next Mech Spawning
            if not red_mechs or red_mechs[-1].deployed:
                red_mechs.append(Mech('red', red_zone))
            if not blue_mechs or blue_mechs[-1].deployed:
                blue_mechs.append(Mech('blue', blue_zone))

            # Core Destruction Check
            if not blue_base.has_core:
                game_over = True
                winner = "RED"
            elif not red_base.has_core:
                game_over = True
                winner = "BLUE"

        # Rendering
        screen.fill(BG_COLOR)
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
            rst = font.render("Press 'R' to Restart", True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 30))
            screen.blit(rst, (WIDTH // 2 - rst.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()