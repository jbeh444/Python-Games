import math
import random
import pygame

# --- Configuration ---
WIDTH, HEIGHT = 1200, 750
FPS = 60

# Colors
BG_COLOR = (25, 28, 36)
RED_TEAM = (220, 60, 60)
BLUE_TEAM = (60, 120, 240)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 95, 105)
DARK_GRAY = (40, 45, 55)
YELLOW = (255, 200, 50)
ORANGE = (255, 110, 20)
PURPLE = (160, 60, 220)

GROUND_Y = 620
BLOCK_SIZE = 22

# --- Classes ---

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 7
        angle = random.uniform(0, 2 * math.pi)
        speed = 6
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed

    def update(self, bounds):
        self.x += self.dx
        self.y += self.dy

        if self.x - self.radius <= bounds.left or self.x + self.radius >= bounds.right:
            self.dx *= -1
            self.x = max(bounds.left + self.radius, min(bounds.right - self.radius, self.x))
        if self.y - self.radius <= bounds.top or self.y + self.radius >= bounds.bottom:
            self.dy *= -1
            self.y = max(bounds.top + self.radius, min(bounds.bottom - self.radius, self.y))

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius)


class SlotRandomizer:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.ball = Ball(self.rect.centerx, self.rect.centery)
        self.cooldown = 0

        slot_w = (width - 25) // 4
        self.slots = []
        types = ['body', 'gun', 'saw', 'flame']
        colors = [WHITE, YELLOW, PURPLE, ORANGE]

        for i in range(4):
            sx = self.rect.left + 5 + i * (slot_w + 5)
            sy = self.rect.bottom - 25
            rect = pygame.Rect(sx, sy, slot_w, 20)
            self.slots.append((rect, types[i], colors[i]))

    def update(self):
        self.ball.update(self.rect)

        if self.cooldown > 0:
            self.cooldown -= 1
            return None, None

        ball_rect = pygame.Rect(self.ball.x - self.ball.radius, self.ball.y - self.ball.radius,
                                self.ball.radius * 2, self.ball.radius * 2)

        team = 'red' if self.ball.x < self.rect.centerx else 'blue'

        for slot_rect, slot_type, _ in self.slots:
            if slot_rect.colliderect(ball_rect):
                self.cooldown = 18
                self.ball.dy *= -1
                return team, slot_type

        return None, None

    def draw(self, surface, font):
        pygame.draw.rect(surface, DARK_GRAY, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)

        for slot_rect, slot_type, color in self.slots:
            pygame.draw.rect(surface, color, slot_rect)
            pygame.draw.rect(surface, BLACK, slot_rect, 1)
            lbl = font.render(slot_type[0].upper(), True, BLACK)
            surface.blit(lbl, lbl.get_rect(center=slot_rect.center))

        self.ball.draw(surface)


class BaseBlock:
    def __init__(self, gx, gy, is_core=False):
        self.gx = gx
        self.gy = gy
        self.is_core = is_core
        self.hp = 120 if is_core else 25
        self.rect = pygame.Rect(gx * BLOCK_SIZE, gy * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)

    def draw(self, surface, team_color):
        color = YELLOW if self.is_core else team_color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 1)

        if self.is_core:
            pygame.draw.circle(surface, RED_TEAM, self.rect.center, 6)


class BreakableBase:
    def __init__(self, start_gx, team):
        self.team = team
        self.blocks = []
        self.has_core = True

        # Outer Fortress Structure (8 wide x 8 tall)
        # Front wall facing center, roof, and isolated back chamber
        for x in range(8):
            for y in range(8):
                gy = (GROUND_Y // BLOCK_SIZE) - 1 - y
                gx = start_gx + x

                is_front_wall = (x == 7 if team == 'red' else x == 0)
                is_back_wall = (x == 0 if team == 'red' else x == 7)
                is_roof = (y == 7)
                is_inner_bunker = (x == 1 if team == 'red' else x == 6)

                # Core is strictly in the back-bottom corner behind the inner bunker wall
                is_core = (x == 0 if team == 'red' else x == 7) and y == 0

                if is_core or is_front_wall or is_roof or is_back_wall or is_inner_bunker:
                    self.blocks.append(BaseBlock(gx, gy, is_core))

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM
        for block in self.blocks:
            block.draw(surface, color)

    def damage_at(self, rect, amount):
        # Front-facing blocks absorb hits before interior core can be touched
        sorted_blocks = sorted(self.blocks, key=lambda b: b.gx, reverse=(self.team == 'red'))

        for block in sorted_blocks:
            if block.rect.colliderect(rect):
                block.hp -= amount
                if block.hp <= 0:
                    if block.is_core:
                        self.has_core = False
                    self.blocks.remove(block)
                return True
        return False


class Mech:
    def __init__(self, team, zone_rect):
        self.team = team
        self.zone = zone_rect
        self.parts = []  # List of [relative_x, relative_y, type, hp]
        self.deployed = False
        self.x = zone_rect.centerx
        self.y = GROUND_Y - BLOCK_SIZE
        self.dir = 1 if team == 'red' else -1

        # Core body part
        self.parts.append([0, 0, 'body', 40])

    def add_part(self, part_type):
        if self.deployed:
            return

        existing_coords = {(p[0], p[1]) for p in self.parts}
        candidates = []

        for px, py, _, _ in self.parts:
            for dx, dy in [(0, -1), (1, 0), (-1, 0), (0, 1)]:
                nx, ny = px + dx, py + dy
                if (nx, ny) not in existing_coords and ny <= 0:
                    candidates.append((nx, ny))

        if candidates:
            chosen = random.choice(candidates)
            hp = 60 if part_type == 'body' else 35
            self.parts.append([chosen[0], chosen[1], part_type, hp])

        if len(self.parts) >= 6:
            self.deployed = True

    def get_hitboxes(self):
        hitboxes = []
        for px, py, ptype, hp in self.parts:
            bx = int(self.x) + px * BLOCK_SIZE
            by = int(self.y) + py * BLOCK_SIZE
            rect = pygame.Rect(bx, by, BLOCK_SIZE, BLOCK_SIZE)
            hitboxes.append((rect, ptype, hp, (px, py)))
        return hitboxes

    def damage_part(self, rel_coord, damage):
        for part in list(self.parts):
            if (part[0], part[1]) == rel_coord:
                part[3] -= damage
                if part[3] <= 0:
                    self.parts.remove(part)
                break

    def update(self, enemy_base, enemy_mechs):
        if not self.deployed or not self.parts:
            return

        my_hitboxes = self.get_hitboxes()

        # Check collision with opposing deployed mechs
        fighting = False
        for enemy in enemy_mechs:
            if not enemy.deployed or not enemy.parts:
                continue

            enemy_hitboxes = enemy.get_hitboxes()
            for my_rect, my_type, _, my_rel in my_hitboxes:
                for enemy_rect, enemy_type, _, enemy_rel in enemy_hitboxes:
                    if my_rect.colliderect(enemy_rect):
                        fighting = True
                        # Fight each other
                        dmg = 2.0 if my_type in ['saw', 'flame'] else 1.0
                        enemy.damage_part(enemy_rel, dmg)

        # Move forward if path is clear of enemy mechs
        if not fighting:
            self.x += 2.0 * self.dir

            # Damage base blocks on contact
            for my_rect, ptype, _, _ in my_hitboxes:
                damage = 15 if ptype in ['saw', 'flame'] else 8
                enemy_base.damage_at(my_rect, damage)

    def draw(self, surface):
        color = RED_TEAM if self.team == 'red' else BLUE_TEAM

        for px, py, ptype, _ in self.parts:
            bx = int(self.x) + px * BLOCK_SIZE
            by = int(self.y) + py * BLOCK_SIZE
            rect = pygame.Rect(bx, by, BLOCK_SIZE, BLOCK_SIZE)

            if ptype == 'body':
                pygame.draw.rect(surface, color, rect)
            elif ptype == 'gun':
                pygame.draw.rect(surface, GRAY, rect)
                barrel = pygame.Rect(rect.centerx, rect.centery - 2, 12 * self.dir, 4)
                pygame.draw.rect(surface, YELLOW, barrel)
            elif ptype == 'saw':
                pygame.draw.rect(surface, DARK_GRAY, rect)
                pygame.draw.circle(surface, WHITE, rect.center, BLOCK_SIZE // 2, 2)
            elif ptype == 'flame':
                pygame.draw.rect(surface, ORANGE, rect)
                if self.deployed and random.random() > 0.4:
                    pygame.draw.circle(surface, YELLOW, (bx + (BLOCK_SIZE if self.dir == 1 else 0), by + 10), 6)

            pygame.draw.rect(surface, BLACK, rect, 1)

        if not self.deployed:
            pygame.draw.rect(surface, (60, 65, 75), self.zone, 1)


# --- Main Loop ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mech Fighting & Protected Base Battle")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 20)
    large_font = pygame.font.SysFont(None, 60)

    red_base = BreakableBase(start_gx=1, team='red')
    blue_base = BreakableBase(start_gx=(WIDTH // BLOCK_SIZE) - 9, team='blue')

    randomizer = SlotRandomizer(WIDTH // 2 - 120, 30, 240, 110)

    red_zone = pygame.Rect(200, GROUND_Y - 120, 100, 120)
    blue_zone = pygame.Rect(WIDTH - 300, GROUND_Y - 120, 100, 120)

    red_mechs = [Mech('red', red_zone)]
    blue_mechs = [Mech('blue', blue_zone)]

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
            team, slot_type = randomizer.update()
            if team and slot_type:
                active_mechs = red_mechs if team == 'red' else blue_mechs
                if active_mechs[-1].deployed:
                    zone = red_zone if team == 'red' else blue_zone
                    active_mechs.append(Mech(team, zone))

                active_mechs[-1].add_part(slot_type)

            # Update Mechs
            for m in list(red_mechs):
                m.update(blue_base, blue_mechs)
                if not m.parts:
                    red_mechs.remove(m)

            for m in list(blue_mechs):
                m.update(red_base, red_mechs)
                if not m.parts:
                    blue_mechs.remove(m)

            # Ensure at least one assembling mech exists per side
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

        # Drawing
        screen.fill(BG_COLOR)

        pygame.draw.line(screen, GRAY, (0, GROUND_Y), (WIDTH, GROUND_Y), 4)

        red_base.draw(screen)
        blue_base.draw(screen)

        for m in red_mechs + blue_mechs:
            m.draw(screen)

        randomizer.draw(screen, font)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            txt = large_font.render(f"{winner} TEAM WINS!", True, WHITE)
            rst = font.render("Press 'R' to Play Next Round", True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 30))
            screen.blit(rst, (WIDTH // 2 - rst.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()