import math
import sys
import wave
import struct
import io
import random
import pygame
import pymunk

# --- Game & Audio Setup ---
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Smash Simulator - Melting Lava & Ragdolls")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

ROAD_Y = 520
LAVA_FLOOR_Y = 620

# --- Procedural Sound Synthesizer ---
def create_sound(duration=0.2, volume=0.5, pitch=60, noise_factor=0.6):
    sample_rate = 22050
    num_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = i / sample_rate
            decay = math.exp(-8 * t)
            sample = (math.sin(2 * math.pi * pitch * t) * (1 - noise_factor) + (2 * (i % 17) / 17.0 - 1) * noise_factor) * decay
            packed_val = struct.pack('h', int(sample * 32767 * volume))
            wf.writeframes(packed_val)
            
    buf.seek(0)
    return pygame.mixer.Sound(file=buf)

CRASH_SOUND = create_sound(0.25, 0.6, 60, 0.7)
EXPLOSION_SOUND = create_sound(0.5, 0.9, 40, 0.8)
POP_SOUND = create_sound(0.15, 0.8, 180, 0.2)
SUCTION_SOUND = create_sound(0.1, 0.3, 120, 0.1)
BURN_SOUND = create_sound(0.15, 0.4, 220, 0.9)

# --- Ragdoll Class ---
class Ragdoll:
    def __init__(self, space, x, y):
        self.space = space
        self.on_fire = False
        self.burn_timer = 0
        self.fire_particles = []

        filter_group = random.randint(10, 100000)
        shape_filter = pymunk.ShapeFilter(group=filter_group)

        self.parts = {}
        part_data = {
            'head': (16, 16, 0.8, (230, 180, 150)),
            'torso': (22, 38, 3.0, (40, 100, 200)),
            'l_arm': (10, 26, 0.6, (200, 50, 50)),
            'r_arm': (10, 26, 0.6, (200, 50, 50)),
            'l_leg': (12, 30, 0.8, (30, 30, 140)),
            'r_leg': (12, 30, 0.8, (30, 30, 140))
        }

        positions = {
            'head': (x, y - 32),
            'torso': (x, y),
            'l_arm': (x - 18, y - 5),
            'r_arm': (x + 18, y - 5),
            'l_leg': (x - 8, y + 32),
            'r_leg': (x + 8, y + 32)
        }

        for name, (w, h, mass, color) in part_data.items():
            pos = positions[name]
            if name == 'head':
                moment = pymunk.moment_for_circle(mass, 0, w/2)
                body = pymunk.Body(mass, moment)
                body.position = pos
                shape = pymunk.Circle(body, w/2)
            else:
                moment = pymunk.moment_for_box(mass, (w, h))
                body = pymunk.Body(mass, moment)
                body.position = pos
                shape = pymunk.Poly.create_box(body, (w, h))

            shape.friction = 0.8
            shape.elasticity = 0.2
            shape.filter = shape_filter
            self.space.add(body, shape)

            self.parts[name] = {
                'body': body,
                'shape': shape,
                'size': (w, h),
                'color': color
            }

        self.joints = []
        torso = self.parts['torso']['body']

        self._add_pivot(self.parts['head']['body'], torso, (x, y - 20))
        self._add_pivot(self.parts['l_arm']['body'], torso, (x - 12, y - 16))
        self._add_pivot(self.parts['r_arm']['body'], torso, (x + 12, y - 16))
        self._add_pivot(self.parts['l_leg']['body'], torso, (x - 8, y + 18))
        self._add_pivot(self.parts['r_leg']['body'], torso, (x + 8, y + 18))

    def _add_pivot(self, body_a, body_b, anchor_world):
        pivot = pymunk.PivotJoint(body_a, body_b, anchor_world)
        pivot.max_force = 150000
        rot = pymunk.RotaryLimitJoint(body_a, body_b, -0.8, 0.8)
        self.space.add(pivot, rot)
        self.joints.extend([pivot, rot])

    def apply_impact(self, point, impulse_strength, radius):
        for data in self.parts.values():
            b = data['body']
            dist = b.position.get_distance(point)
            if dist < radius + 60:
                dir_vec = (b.position - point).normalized()
                b.apply_impulse_at_local_point(dir_vec * (impulse_strength * 0.4))

    def apply_suction(self, point, force_strength):
        for data in self.parts.values():
            b = data['body']
            dir_vec = (point - b.position)
            dist = dir_vec.length
            if dist > 1:
                pull_force = dir_vec.normalized() * min(force_strength * 0.2, force_strength * 200 / max(dist, 40))
                b.apply_impulse_at_local_point(pull_force)

    def check_lava(self):
        if current_map == 2:
            torso_pos = self.parts['torso']['body'].position
            if 240 < torso_pos.x < 760 and torso_pos.y > 500:
                self.on_fire = True

    def update_fire(self):
        if not self.on_fire:
            return

        self.burn_timer += 1
        if self.burn_timer % 20 == 0:
            BURN_SOUND.play()

        for _ in range(2):
            b = random.choice(list(self.parts.values()))['body']
            self.fire_particles.append({
                'pos': [b.position.x + random.uniform(-10, 10), b.position.y + random.uniform(-10, 10)],
                'vel': [random.uniform(-0.8, 0.8), random.uniform(-2, -0.5)],
                'life': random.randint(10, 25),
                'size': random.randint(4, 10)
            })

        for p in list(self.fire_particles):
            p['pos'][0] += p['vel'][0]
            p['pos'][1] += p['vel'][1]
            p['life'] -= 1
            if p['life'] <= 0:
                self.fire_particles.remove(p)

    def draw(self, surface):
        self.check_lava()
        self.update_fire()

        for name, data in self.parts.items():
            b = data['body']
            col = data['color']
            if self.on_fire:
                col = (max(20, col[0] - 80), max(20, col[1] - 80), max(20, col[2] - 80))

            if name == 'head':
                pygame.draw.circle(surface, col, (int(b.position.x), int(b.position.y)), int(data['size'][0]/2))
                pygame.draw.circle(surface, (20, 20, 20), (int(b.position.x), int(b.position.y)), int(data['size'][0]/2), 2)
            else:
                shape = data['shape']
                verts = [b.local_to_world(v) for v in shape.get_vertices()]
                pygame.draw.polygon(surface, col, [(p.x, p.y) for p in verts])
                pygame.draw.polygon(surface, (20, 20, 20), [(p.x, p.y) for p in verts], 2)

        for p in self.fire_particles:
            col = random.choice([(255, 60, 0), (255, 160, 0), (255, 220, 0)])
            pygame.draw.circle(surface, col, (int(p['pos'][0]), int(p['pos'][1])), p['size'])

    def destroy(self):
        for j in self.joints:
            self.space.remove(j)
        for data in self.parts.values():
            self.space.remove(data['body'], data['shape'])

# --- Deformable Vehicle Base Class with Lava Melting ---
class SolidCar:
    def __init__(self, space, x, y, car_type="sedan"):
        self.space = space
        self.car_type = car_type
        self.on_fire = False
        self.burn_timer = 0
        self.fire_particles = []
        self.is_dissolved = False

        mass_map = {"sedan": 12.0, "van": 15.0, "supercar": 10.0, "monster": 28.0}
        box_map = {"sedan": (160, 60), "van": (180, 80), "supercar": (170, 50), "monster": (200, 130)}
        
        mass = mass_map.get(car_type, 12.0)
        box_size = box_map.get(car_type, (160, 60))
        moment = pymunk.moment_for_box(mass, box_size)
        
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.space.add(self.body)

        car_filter = pymunk.ShapeFilter(group=1)

        if car_type == "van":
            self.part_specs = {
                'chassis': [150, 16, 0, 20, (50, 50, 50), 400],
                'van_body': [130, 48, -10, -10, (30, 90, 180), 300],
                'van_hood': [35, 20, 52, 5, (30, 90, 180), 200],
                'van_roof': [120, 8, -10, -36, (20, 70, 150), 180],
                'trunk_door': [12, 40, -71, -10, (20, 70, 150), 150],
                'front_bumper': [12, 18, 73, 18, (120, 120, 120), 150],
                'rear_bumper': [12, 18, -73, 18, (120, 120, 120), 150],
                'windshield': [18, 22, 42, -12, (150, 220, 255), 80],
                'side_window': [40, 16, 0, -18, (150, 220, 255), 80],
                'rear_window': [25, 16, -42, -18, (150, 220, 255), 80]
            }
            wheel_offsets = [-48, 48]
            wheel_radius = 16
            wheel_y = 36
        elif car_type == "supercar":
            self.part_specs = {
                'chassis': [140, 12, 0, 14, (40, 40, 40), 300],
                'hood': [50, 12, 35, 6, (240, 200, 20), 180],
                'cabin': [45, 16, -10, -6, (30, 30, 30), 150],
                'spoiler': [20, 8, -60, -16, (20, 20, 20), 100],
                'front_bumper': [10, 12, 62, 10, (200, 160, 10), 120],
                'rear_bumper': [10, 12, -62, 10, (200, 160, 10), 120],
                'windshield': [22, 14, 15, -6, (180, 240, 255), 70]
            }
            wheel_offsets = [-42, 42]
            wheel_radius = 14
            wheel_y = 22
        elif car_type == "monster":
            self.part_specs = {
                'heavy_chassis': [140, 20, 0, 18, (30, 30, 35), 700],
                'lift_suspension': [120, 16, 0, 32, (180, 40, 40), 500],
                'truck_cabin': [70, 36, -15, -20, (50, 180, 50), 500],
                'truck_hood': [45, 22, 40, -13, (50, 180, 50), 400],
                'truck_bed': [40, 18, -65, -11, (40, 150, 40), 400],
                'engine_blower': [20, 14, 35, -30, (220, 220, 220), 250],
                'exhaust_pipes': [10, 30, -35, -40, (180, 180, 180), 300],
                'roll_cage': [80, 8, -15, -42, (220, 220, 220), 400],
                'monster_bumper': [18, 22, 70, 15, (200, 180, 40), 350],
                'monster_windshield': [20, 18, 12, -22, (160, 230, 255), 100]
            }
            wheel_offsets = [-58, 58]
            wheel_radius = 34
            wheel_y = 48
        else:  # Sedan
            self.part_specs = {
                'chassis': [120, 14, 0, 15, (60, 60, 60), 300],
                'cabin': [50, 24, -10, -5, (200, 30, 30), 200],
                'hood': [35, 12, 38, 8, (200, 30, 30), 150],
                'trunk': [30, 12, -48, 8, (200, 30, 30), 150],
                'front_bumper': [10, 16, 62, 14, (100, 100, 100), 100],
                'rear_bumper': [10, 16, -62, 14, (100, 100, 100), 100],
                'windshield': [18, 18, 18, -5, (150, 220, 255), 60]
            }
            wheel_offsets = [-38, 38]
            wheel_radius = 16
            wheel_y = 32

        self.shapes = {}
        self.detached_debris = []

        for name, spec in self.part_specs.items():
            w, h, ox, oy, color, hp = spec
            local_verts = [
                pymunk.Vec2d(-w/2 + ox, -h/2 + oy),
                pymunk.Vec2d(w/2 + ox, -h/2 + oy),
                pymunk.Vec2d(w/2 + ox, h/2 + oy),
                pymunk.Vec2d(-w/2 + ox, h/2 + oy)
            ]
            
            shape = pymunk.Poly(self.body, local_verts)
            shape.friction = 0.8
            shape.elasticity = 0.1
            shape.filter = car_filter
            self.space.add(shape)
            
            self.shapes[name] = {
                'shape': shape,
                'local_verts': local_verts,
                'size': (w, h),
                'color': color,
                'health': hp,
                'max_health': hp
            }

        self.wheels = []
        for offset_x in wheel_offsets:
            w_mass = 3.0 if car_type == "monster" else 1.2
            w_body = pymunk.Body(w_mass, pymunk.moment_for_circle(w_mass, 0, wheel_radius))
            w_body.position = (x + offset_x, y + wheel_y)
            w_shape = pymunk.Circle(w_body, wheel_radius)
            w_shape.friction = 1.2 if car_type == "monster" else 1.0
            w_shape.filter = car_filter
            
            pivot = pymunk.PivotJoint(self.body, w_body, (offset_x, wheel_y - 12), (0, 0))
            self.space.add(w_body, w_shape, pivot)
            
            self.wheels.append({
                'body': w_body,
                'shape': w_shape,
                'pivot': pivot,
                'radius': wheel_radius,
                'popped': False,
                'melted': False
            })

    def drive(self, direction):
        if self.is_dissolved: return
        for w in self.wheels:
            if w['melted']: continue
            torque = 450000 if self.car_type == "monster" else 180000
            if w['popped']: torque *= 0.2
            w['body'].torque = torque * direction

    def melt_in_lava(self):
        if self.is_dissolved:
            return

        self.on_fire = True
        
        # Melt and pop tires
        for w in self.wheels:
            if not w['melted']:
                if not w['popped']:
                    w['popped'] = True
                    w['radius'] = max(3.0, w['radius'] * 0.6)
                    self.space.remove(w['shape'])
                    w['shape'] = pymunk.Circle(w['body'], w['radius'])
                    w['shape'].friction = 0.3
                    self.space.add(w['shape'])
                    POP_SOUND.play()
                else:
                    # Gradually shrink and dissolve tires
                    w['radius'] -= 0.15
                    if w['radius'] <= 3.0:
                        w['melted'] = True
                        self.space.remove(w['body'], w['shape'], w['pivot'])
                    else:
                        self.space.remove(w['shape'])
                        w['shape'] = pymunk.Circle(w['body'], w['radius'])
                        w['shape'].friction = 0.1
                        self.space.add(w['shape'])

        # Melt car body parts
        if len(self.shapes) > 0:
            target_part = random.choice(list(self.shapes.keys()))
            center = self.body.local_to_world(pymunk.Vec2d(0, 0))
            self.deform_part(target_part, center, pymunk.Vec2d(random.uniform(-50, 50), random.uniform(-50, 50)), damage=18)
        else:
            # Completely dissolve chassis
            if not self.is_dissolved:
                self.space.remove(self.body)
                self.is_dissolved = True

        # Dissolve detached debris in lava
        for deb in list(self.detached_debris):
            if 240 < deb['body'].position.x < 760 and deb['body'].position.y > 500:
                deb['melt_timer'] = deb.get('melt_timer', 60) - 1
                if deb['melt_timer'] <= 0:
                    self.space.remove(deb['body'], deb['shape'])
                    self.detached_debris.remove(deb)

    def update_fire(self):
        if not self.on_fire or self.is_dissolved:
            return

        self.burn_timer += 1
        if self.burn_timer % 15 == 0:
            BURN_SOUND.play()

        for _ in range(3):
            rx = random.randint(-60, 60)
            ry = random.randint(-20, 20)
            p_pos = self.body.local_to_world(pymunk.Vec2d(rx, ry))
            self.fire_particles.append({
                'pos': [p_pos.x, p_pos.y],
                'vel': [random.uniform(-1, 1), random.uniform(-3, -1)],
                'life': random.randint(15, 30),
                'size': random.randint(6, 14)
            })

        for p in list(self.fire_particles):
            p['pos'][0] += p['vel'][0]
            p['pos'][1] += p['vel'][1]
            p['life'] -= 1
            if p['life'] <= 0:
                self.fire_particles.remove(p)

    def deform_part(self, name, impact_world_pt, force_vec, damage=20):
        if name not in self.shapes:
            return

        info = self.shapes[name]
        info['health'] -= damage

        local_impact = self.body.world_to_local(impact_world_pt)
        local_force = force_vec.rotated(-self.body.angle) * 0.004

        new_verts = []
        for v in info['local_verts']:
            dist = v.get_distance(local_impact)
            if dist < 80:
                factor = max(0.0, 1.0 - (dist / 80.0))
                v_new = v + local_force * factor
                new_verts.append(v_new)
            else:
                new_verts.append(v)

        info['local_verts'] = new_verts
        self.space.remove(info['shape'])
        
        new_shape = pymunk.Poly(self.body, info['local_verts'])
        new_shape.friction = 0.8
        new_shape.elasticity = 0.1
        new_shape.filter = pymunk.ShapeFilter(group=1)
        self.space.add(new_shape)
        info['shape'] = new_shape

        if info['health'] <= 0:
            self.detach_part(name)

    def detach_part(self, name):
        if name in self.shapes:
            info = self.shapes.pop(name)
            self.space.remove(info['shape'])

            if not self.is_dissolved:
                verts_local = info['local_verts']
                center_local = sum(verts_local, pymunk.Vec2d(0, 0)) / len(verts_local)
                world_pos = self.body.local_to_world(center_local)
                
                centered_verts = [v - center_local for v in verts_local]

                d_mass = 1.2
                moment = pymunk.moment_for_poly(d_mass, centered_verts)
                d_body = pymunk.Body(d_mass, moment)
                d_body.position = world_pos
                d_body.angle = self.body.angle
                
                d_shape = pymunk.Poly(d_body, centered_verts)
                d_shape.friction = 0.9
                self.space.add(d_body, d_shape)

                d_body.velocity = self.body.velocity + pymunk.Vec2d(random.uniform(-100, 100), -150)
                self.detached_debris.append({
                    'body': d_body,
                    'shape': d_shape,
                    'local_verts': centered_verts,
                    'color': info['color'],
                    'melt_timer': 60
                })
                CRASH_SOUND.play()

    def apply_suction(self, point, force_strength):
        if not self.is_dissolved:
            dir_vec = (point - self.body.position)
            dist = dir_vec.length
            if dist > 1:
                dir_norm = dir_vec.normalized()
                pull_force = dir_norm * min(force_strength, force_strength * 500 / max(dist, 50))
                self.body.apply_impulse_at_world_point(pull_force, self.body.position)

        for deb in self.detached_debris:
            d_body = deb['body']
            d_dir = (point - d_body.position)
            if d_dir.length > 1:
                d_body.apply_impulse_at_world_point(d_dir.normalized() * (force_strength * 0.5), d_body.position)

        SUCTION_SOUND.play()

    def apply_impact(self, point, impulse_strength, radius):
        if not self.is_dissolved:
            dir_vec = (self.body.position - point).normalized()
            if self.body.position.get_distance(point) < radius + 100:
                self.body.apply_impulse_at_local_point(dir_vec * impulse_strength)

            hit_parts = []
            for name, data in list(self.shapes.items()):
                verts = data['local_verts']
                center_local = sum(verts, pymunk.Vec2d(0, 0)) / len(verts)
                part_world_pos = self.body.local_to_world(center_local)
                if part_world_pos.get_distance(point) < radius:
                    hit_parts.append(name)

            for name in hit_parts:
                dmg = int(impulse_strength / 25)
                self.deform_part(name, point, dir_vec * impulse_strength, damage=dmg)

            if hit_parts and impulse_strength >= 2500:
                EXPLOSION_SOUND.play()

    def check_debris_and_wheels(self):
        for deb in self.detached_debris:
            deb_pos = deb['body'].position
            for w in self.wheels:
                if not w['popped'] and not w['melted']:
                    if deb_pos.get_distance(w['body'].position) < w['radius'] + 10:
                        w['popped'] = True
                        w['radius'] = int(w['radius'] * 0.6)
                        self.space.remove(w['shape'])
                        w['shape'] = pymunk.Circle(w['body'], w['radius'])
                        w['shape'].friction = 0.3
                        self.space.add(w['shape'])
                        POP_SOUND.play()

    def draw(self, surface):
        self.update_fire()

        if not self.is_dissolved:
            for name, data in self.shapes.items():
                world_verts = [self.body.local_to_world(v) for v in data['local_verts']]
                col = data['color']
                if self.on_fire:
                    col = (max(20, col[0] - 60), max(20, col[1] - 60), max(20, col[2] - 60))
                pygame.draw.polygon(surface, col, [(p.x, p.y) for p in world_verts])
                pygame.draw.polygon(surface, (20, 20, 20), [(p.x, p.y) for p in world_verts], 2)

            if ('monster_bumper' in self.shapes or 'front_bumper' in self.shapes):
                front_pt = self.body.local_to_world(pymunk.Vec2d(75 if self.car_type == "monster" else 65, 0))
                pygame.draw.circle(surface, (255, 255, 180), (int(front_pt.x), int(front_pt.y)), 6)

        for deb in self.detached_debris:
            b = deb['body']
            world_verts = [b.local_to_world(v) for v in deb['local_verts']]
            col = deb['color']
            if 240 < b.position.x < 760 and b.position.y > 500:
                col = (200, 80, 20)  # Red heat effect on debris melting in lava
            pygame.draw.polygon(surface, col, [(p.x, p.y) for p in world_verts])
            pygame.draw.polygon(surface, (20, 20, 20), [(p.x, p.y) for p in world_verts], 2)

        for w in self.wheels:
            if w['melted']: continue
            wb = w['body']
            pos = (int(wb.position.x), int(wb.position.y))
            rad = max(2, int(w['radius']))
            
            if w['popped']:
                pygame.draw.circle(surface, (40, 40, 40), pos, rad)
            else:
                pygame.draw.circle(surface, (15, 15, 15), pos, rad)
                pygame.draw.circle(surface, (210, 210, 210), pos, max(4, rad // 2))
                pygame.draw.circle(surface, (40, 40, 40), pos, max(2, rad // 4))

                tread_count = 10 if self.car_type == "monster" else 6
                for t in range(tread_count):
                    angle = wb.angle + (t * (2 * math.pi / tread_count))
                    spoke_end = (pos[0] + rad * math.cos(angle), pos[1] + rad * math.sin(angle))
                    pygame.draw.line(surface, (255, 255, 255) if self.car_type != "monster" else (80, 80, 80), pos, spoke_end, 3)

        for p in self.fire_particles:
            col = random.choice([(255, 60, 0), (255, 160, 0), (255, 220, 0)])
            pygame.draw.circle(surface, col, (int(p['pos'][0]), int(p['pos'][1])), p['size'])

# --- Auto-Retracting Spiked Wall Crusher Class ---
class SpikedCrusher:
    def __init__(self, space):
        self.space = space
        self.left_home = -200.0
        self.right_home = WIDTH + 200.0
        self.left_x = self.left_home
        self.right_x = self.right_home
        self.wall_thickness = 500
        self.state = "IDLE"
        self.crush_hold_timer = 0
        
        self.left_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.right_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        
        self.left_shape = pymunk.Poly.create_box(self.left_body, (self.wall_thickness, HEIGHT * 2))
        self.right_shape = pymunk.Poly.create_box(self.right_body, (self.wall_thickness, HEIGHT * 2))
        self.left_shape.friction = 1.0
        self.right_shape.friction = 1.0
        
        self.space.add(self.left_body, self.left_shape, self.right_body, self.right_shape)
        self.reset()

    def reset(self):
        self.state = "IDLE"
        self.crush_hold_timer = 0
        self.left_x = self.left_home
        self.right_x = self.right_home
        self.left_body.position = (self.left_x - self.wall_thickness / 2, HEIGHT / 2)
        self.right_body.position = (self.right_x + self.wall_thickness / 2, HEIGHT / 2)

    def trigger(self):
        if self.state == "IDLE":
            self.state = "CLOSING"

    def update(self, car, ragdolls):
        if self.state == "IDLE":
            return

        crush_speed = 3.5
        retract_speed = 4.5
        min_gap = 210

        if self.state == "CLOSING":
            if (self.right_x - self.left_x) > min_gap:
                self.left_x += crush_speed
                self.right_x -= crush_speed
            else:
                self.state = "CRUSHING"
                self.crush_hold_timer = 40

        elif self.state == "CRUSHING":
            self.crush_hold_timer -= 1
            if self.crush_hold_timer <= 0:
                self.state = "RETRACTING"

        elif self.state == "RETRACTING":
            if self.left_x > self.left_home or self.right_x < self.right_home:
                self.left_x = max(self.left_home, self.left_x - retract_speed)
                self.right_x = min(self.right_home, self.right_x + retract_speed)
            else:
                self.state = "IDLE"

        self.left_body.position = (self.left_x - self.wall_thickness / 2, HEIGHT / 2)
        self.right_body.position = (self.right_x + self.wall_thickness / 2, HEIGHT / 2)

        if self.state in ["CLOSING", "CRUSHING"]:
            left_crush_pt = pymunk.Vec2d(self.left_x, car.body.position.y if not car.is_dissolved else HEIGHT/2)
            right_crush_pt = pymunk.Vec2d(self.right_x, car.body.position.y if not car.is_dissolved else HEIGHT/2)
            
            for name in list(car.shapes.keys()):
                car.deform_part(name, left_crush_pt, pymunk.Vec2d(500, 0), damage=15)
                car.deform_part(name, right_crush_pt, pymunk.Vec2d(-500, 0), damage=15)

            for rd in ragdolls:
                rd.apply_impact(left_crush_pt, 800, 100)
                rd.apply_impact(right_crush_pt, 800, 100)

    def draw(self, surface):
        pygame.draw.rect(surface, (80, 80, 80), (self.left_x - self.wall_thickness, 0, self.wall_thickness, HEIGHT))
        pygame.draw.rect(surface, (120, 120, 120), (self.left_x - 30, 0, 30, HEIGHT))
        for y in range(40, HEIGHT, 35):
            pts = [(self.left_x, y), (self.left_x + 24, y + 15), (self.left_x, y + 30)]
            pygame.draw.polygon(surface, (200, 30, 30), pts)
            pygame.draw.polygon(surface, (30, 30, 30), pts, 2)

        pygame.draw.rect(surface, (80, 80, 80), (self.right_x, 0, self.wall_thickness, HEIGHT))
        pygame.draw.rect(surface, (120, 120, 120), (self.right_x, 0, 30, HEIGHT))
        for y in range(40, HEIGHT, 35):
            pts = [(self.right_x, y), (self.right_x - 24, y + 15), (self.right_x, y - 30)]
            pygame.draw.polygon(surface, (200, 30, 30), pts)
            pygame.draw.polygon(surface, (30, 30, 30), pts, 2)

# --- World Setup ---
space = pymunk.Space()
space.gravity = (0, 900)

active_static_shapes = []
ragdolls = []

def setup_map_physics(map_idx):
    global active_static_shapes
    for shape in active_static_shapes:
        space.remove(shape)
    active_static_shapes.clear()

    w_left = pymunk.Segment(space.static_body, (-100, -500), (-100, HEIGHT + 500), 20)
    w_right = pymunk.Segment(space.static_body, (WIDTH + 100, -500), (WIDTH + 100, HEIGHT + 500), 20)
    w_top = pymunk.Segment(space.static_body, (-500, -200), (WIDTH + 500, -200), 20)
    space.add(w_left, w_right, w_top)
    active_static_shapes.extend([w_left, w_right, w_top])

    if map_idx == 2:  # Lava Map
        p1 = pymunk.Segment(space.static_body, (-100, ROAD_Y), (250, ROAD_Y), 10)
        p2 = pymunk.Segment(space.static_body, (750, ROAD_Y), (WIDTH + 100, ROAD_Y), 10)
        p3 = pymunk.Segment(space.static_body, (240, LAVA_FLOOR_Y), (760, LAVA_FLOOR_Y), 10)
        p1.friction = p2.friction = p3.friction = 0.9
        space.add(p1, p2, p3)
        active_static_shapes.extend([p1, p2, p3])
    else:
        road_shape = pymunk.Segment(space.static_body, (-200, ROAD_Y), (WIDTH + 200, ROAD_Y), 10)
        road_shape.friction = 0.9
        space.add(road_shape)
        active_static_shapes.append(road_shape)

setup_map_physics(0)

current_car_type = "sedan"
car = SolidCar(space, 400, 300, current_car_type)
crusher = SpikedCrusher(space)

weapons = [
    {"name": "Crowbar", "force": 400, "radius": 50},
    {"name": "Pistol", "force": 1000, "radius": 40},
    {"name": "Warhammer", "force": 2000, "radius": 85},
    {"name": "C4 Bomb", "force": 5000, "radius": 160},
    {"name": "Suction Gun", "force": 300, "radius": 200},
    {"name": "Ragdoll Spawner", "force": 0, "radius": 0}
]
current_weapon_idx = 0
current_map = 0
menu_open = False
attack_animation_frame = 0

font = pygame.font.SysFont(None, 20)
btn_font = pygame.font.SysFont(None, 24, bold=True)
menu_font = pygame.font.SysFont(None, 30, bold=True)

def spawn_car(car_type):
    global car, current_car_type
    current_car_type = car_type
    
    if not car.is_dissolved:
        for s in list(car.shapes.values()): space.remove(s['shape'])
        space.remove(car.body)
    
    for d in car.detached_debris: space.remove(d['body'], d['shape'])
    for w in car.wheels:
        if not w['melted']:
            space.remove(w['body'], w['shape'], w['pivot'])
    
    start_x = 150 if current_map == 2 else 400
    car = SolidCar(space, start_x, 300, car_type)
    crusher.reset()

def clear_ragdolls():
    global ragdolls
    for rd in ragdolls:
        rd.destroy()
    ragdolls.clear()

def check_lava_interaction():
    if current_map == 2:
        # Check car body in lava
        if not car.is_dissolved:
            car_pos = car.body.position
            if 240 < car_pos.x < 760 and car_pos.y > 480:
                car.melt_in_lava()
        else:
            car.melt_in_lava()

def draw_lava_map(surface):
    surface.fill((25, 12, 16))
    pygame.draw.rect(surface, (55, 45, 50), (0, ROAD_Y, 250, HEIGHT - ROAD_Y))
    pygame.draw.rect(surface, (55, 45, 50), (750, ROAD_Y, 250, HEIGHT - ROAD_Y))
    pygame.draw.rect(surface, (40, 20, 20), (240, LAVA_FLOOR_Y, 520, HEIGHT - LAVA_FLOOR_Y))
    
    lava_surf = pygame.Surface((520, LAVA_FLOOR_Y - ROAD_Y), pygame.SRCALPHA)
    lava_surf.fill((240, 70, 10, 180))
    surface.blit(lava_surf, (240, ROAD_Y))

    for _ in range(10):
        bx = random.randint(250, 730)
        by = random.randint(ROAD_Y + 10, LAVA_FLOOR_Y - 5)
        pygame.draw.circle(surface, (255, 210, 40), (bx, by), random.randint(3, 10))

def draw_weapon_cursor(surface, pos, weapon_idx, attack_frame, is_active):
    x, y = pos
    if weapon_idx == 0:
        angle = -30 - (attack_frame * 15)
        rad = math.radians(angle)
        end_x = x + 35 * math.cos(rad)
        end_y = y + 35 * math.sin(rad)
        pygame.draw.line(surface, (180, 30, 30), (x, y), (end_x, end_y), 6)
        pygame.draw.line(surface, (200, 200, 200), (end_x, end_y), (end_x + 8, end_y - 8), 4)

    elif weapon_idx == 1:
        pygame.draw.rect(surface, (50, 50, 50), (x - 10, y - 5, 25, 10))
        pygame.draw.rect(surface, (30, 30, 30), (x - 8, y, 8, 15))
        if attack_frame > 0:
            pygame.draw.circle(surface, (255, 200, 50), (x + 20, y - 1), 12)

    elif weapon_idx == 2:
        rot = attack_frame * 20
        rad = math.radians(-45 + rot)
        hx = x + 40 * math.cos(rad)
        hy = y + 40 * math.sin(rad)
        pygame.draw.line(surface, (120, 80, 40), (x, y), (hx, hy), 8)
        pygame.draw.rect(surface, (150, 150, 150), (hx - 12, hy - 12, 24, 24))

    elif weapon_idx == 3:
        pygame.draw.rect(surface, (180, 140, 60), (x - 15, y - 10, 30, 20))
        pygame.draw.circle(surface, (255, 0, 0), (x, y - 12), 4)

    elif weapon_idx == 4:
        pygame.draw.polygon(surface, (40, 140, 220), [(x-15, y-10), (x+15, y-20), (x+15, y+20), (x-15, y+10)])
        pygame.draw.circle(surface, (0, 200, 255), (x-15, y), 8)
        if is_active:
            for r in range(20, 120, 25):
                alpha_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(alpha_surf, (0, 220, 255, 100), (r, r), r, 3)
                surface.blit(alpha_surf, (x - r, y - r))

    elif weapon_idx == 5:
        pygame.draw.circle(surface, (230, 180, 150), (x, y - 15), 6)
        pygame.draw.line(surface, (40, 100, 200), (x, y - 9), (x, y + 5), 4)
        pygame.draw.line(surface, (200, 50, 50), (x - 10, y - 5), (x + 10, y - 5), 3)
        pygame.draw.line(surface, (30, 30, 140), (x, y + 5), (x - 6, y + 16), 3)
        pygame.draw.line(surface, (30, 30, 140), (x, y + 5), (x + 6, y + 16), 3)

    pygame.draw.circle(surface, (255, 255, 255), (x, y), 5, 1)

def draw_ui(surface):
    bar_rect = pygame.Rect(10, 10, 560, 50)
    pygame.draw.rect(surface, (30, 30, 40), bar_rect, border_radius=8)
    pygame.draw.rect(surface, (100, 100, 120), bar_rect, 2, border_radius=8)

    for i, w in enumerate(weapons):
        btn_x = 14 + i * 91
        w_rect = pygame.Rect(btn_x, 15, 87, 40)
        
        selected = (i == current_weapon_idx)
        bg_col = (70, 130, 180) if selected else (50, 50, 60)
        border_col = (255, 215, 0) if selected else (80, 80, 90)
        
        pygame.draw.rect(surface, bg_col, w_rect, border_radius=6)
        pygame.draw.rect(surface, border_col, w_rect, 2, border_radius=6)
        
        txt = font.render(f"[{i+1}]{w['name'][:7]}", True, (255, 255, 255))
        surface.blit(txt, (btn_x + 4, 26))

    car_btn_rect = pygame.Rect(580, 10, 110, 50)
    pygame.draw.rect(surface, (180, 100, 30), car_btn_rect, border_radius=8)
    pygame.draw.rect(surface, (255, 200, 120), car_btn_rect, 2, border_radius=8)
    c_txt1 = font.render("GARAGE", True, (255, 255, 255))
    c_txt2 = font.render("[C] Select", True, (230, 230, 230))
    surface.blit(c_txt1, (588, 18))
    surface.blit(c_txt2, (588, 36))

    map_names = {0: "Arena", 1: "Spike Crusher", 2: "Lava Pool"}
    map_btn_rect = pygame.Rect(700, 10, 140, 50)
    pygame.draw.rect(surface, (40, 120, 60), map_btn_rect, border_radius=8)
    pygame.draw.rect(surface, (200, 255, 200), map_btn_rect, 2, border_radius=8)
    m_txt1 = font.render("MAP: " + map_names[current_map], True, (255, 255, 255))
    m_txt2 = font.render("[M] Switch", True, (200, 200, 200))
    surface.blit(m_txt1, (708, 18))
    surface.blit(m_txt2, (708, 36))

    rst_btn_rect = pygame.Rect(850, 10, 135, 50)
    pygame.draw.rect(surface, (160, 40, 40), rst_btn_rect, border_radius=8)
    pygame.draw.rect(surface, (255, 150, 150), rst_btn_rect, 2, border_radius=8)
    r_txt = btn_font.render("RESET [R]", True, (255, 255, 255))
    surface.blit(r_txt, (862, 25))

    if current_map == 1:
        crush_btn_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT - 55, 240, 45)
        b_col = (220, 30, 30) if crusher.state == "IDLE" else (100, 100, 100)
        pygame.draw.rect(surface, b_col, crush_btn_rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), crush_btn_rect, 3, border_radius=10)
        c_label = "ACTIVATE CRUSHER" if crusher.state == "IDLE" else f"CRUSHER: {crusher.state}"
        c_txt = font.render(c_label, True, (255, 255, 255))
        surface.blit(c_txt, (WIDTH // 2 - 80, HEIGHT - 40))

def draw_car_select_menu(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 260, HEIGHT // 2 - 210, 520, 420)
    pygame.draw.rect(surface, (40, 40, 50), panel, border_radius=12)
    pygame.draw.rect(surface, (255, 215, 0), panel, 3, border_radius=12)

    title = menu_font.render("SELECT VEHICLE GARAGE", True, (255, 215, 0))
    surface.blit(title, (WIDTH // 2 - 140, HEIGHT // 2 - 190))

    cars_data = [
        ("1. Red Sports Sedan", "Original starting car. Lightweight & agile.", (255, 255, 255), "sedan"),
        ("2. Detailed Blue Van", "Heavy cargo van with rear trunk door & windows.", (30, 180, 255), "van"),
        ("3. Yellow Supercar", "Aerodynamic, ultra-fast supercar with spoiler.", (240, 220, 30), "supercar"),
        ("4. Detailed Monster Truck", "Engine blower, roll cage, exhaust stacks & massive tires.", (80, 220, 60), "monster")
    ]

    for idx, (c_title, c_desc, c_col, c_key) in enumerate(cars_data):
        y_pos = HEIGHT // 2 - 140 + idx * 75
        c_rect = pygame.Rect(WIDTH // 2 - 230, y_pos, 460, 65)
        bg = (60, 80, 110) if current_car_type == c_key else (60, 60, 70)
        pygame.draw.rect(surface, bg, c_rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), c_rect, 2, border_radius=8)

        st1 = btn_font.render(c_title, True, c_col)
        st2 = font.render(c_desc, True, (200, 200, 200))
        surface.blit(st1, (WIDTH // 2 - 215, y_pos + 10))
        surface.blit(st2, (WIDTH // 2 - 215, y_pos + 35))

    close_txt = font.render("Press [1-4], Click an option, or Press [C]/[ESC] to close", True, (180, 180, 180))
    surface.blit(close_txt, (WIDTH // 2 - 180, HEIGHT // 2 + 170))

# --- Main Game Loop ---
running = True
is_mouse_down = False

while running:
    if current_map == 0:
        screen.fill((135, 206, 235))
        pygame.draw.rect(screen, (50, 50, 50), (0, ROAD_Y, WIDTH, HEIGHT - ROAD_Y))
    elif current_map == 1:
        screen.fill((40, 35, 45))
        pygame.draw.rect(screen, (50, 50, 50), (0, ROAD_Y, WIDTH, HEIGHT - ROAD_Y))
    else:
        draw_lava_map(screen)

    mx, my = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if menu_open:
                if event.key == pygame.K_1: spawn_car("sedan"); menu_open = False
                elif event.key == pygame.K_2: spawn_car("van"); menu_open = False
                elif event.key == pygame.K_3: spawn_car("supercar"); menu_open = False
                elif event.key == pygame.K_4: spawn_car("monster"); menu_open = False
                elif event.key in [pygame.K_c, pygame.K_ESCAPE]: menu_open = False
            else:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]:
                    current_weapon_idx = event.key - pygame.K_1
                elif event.key == pygame.K_c:
                    menu_open = True
                elif event.key == pygame.K_m:
                    current_map = (current_map + 1) % 3
                    setup_map_physics(current_map)
                    clear_ragdolls()
                    spawn_car(current_car_type)
                elif event.key == pygame.K_r:
                    clear_ragdolls()
                    spawn_car(current_car_type)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            is_mouse_down = True
            
            if menu_open:
                if (WIDTH // 2 - 230 <= mx <= WIDTH // 2 + 230):
                    for idx, c_key in enumerate(["sedan", "van", "supercar", "monster"]):
                        y_pos = HEIGHT // 2 - 140 + idx * 75
                        if y_pos <= my <= y_pos + 65:
                            spawn_car(c_key)
                            menu_open = False
            else:
                if my <= 60:
                    if 10 <= mx <= 570:
                        idx = (mx - 14) // 91
                        if 0 <= idx < len(weapons):
                            current_weapon_idx = idx
                    elif 580 <= mx <= 690:
                        menu_open = True
                    elif 700 <= mx <= 840:
                        current_map = (current_map + 1) % 3
                        setup_map_physics(current_map)
                        clear_ragdolls()
                        spawn_car(current_car_type)
                    elif 850 <= mx <= 985:
                        clear_ragdolls()
                        spawn_car(current_car_type)

                elif current_map == 1 and (WIDTH // 2 - 120 <= mx <= WIDTH // 2 + 120) and (HEIGHT - 55 <= my <= HEIGHT - 10):
                    crusher.trigger()

                else:
                    w_info = weapons[current_weapon_idx]
                    if current_weapon_idx == 5:
                        ragdolls.append(Ragdoll(space, mx, my))
                    elif current_weapon_idx != 4:
                        pt = pymunk.Vec2d(mx, my)
                        car.apply_impact(pt, w_info["force"], w_info["radius"])
                        for rd in ragdolls:
                            rd.apply_impact(pt, w_info["force"], w_info["radius"])
                        attack_animation_frame = 4

        elif event.type == pygame.MOUSEBUTTONUP:
            is_mouse_down = False

    if not menu_open:
        if is_mouse_down and current_weapon_idx == 4 and my > 65:
            pt = pymunk.Vec2d(mx, my)
            car.apply_suction(pt, weapons[4]["force"])
            for rd in ragdolls:
                rd.apply_suction(pt, weapons[4]["force"])

        if attack_animation_frame > 0:
            attack_animation_frame -= 1

        keys = pygame.key.get_pressed()
        if keys[pygame.K_d]: car.drive(1)
        elif keys[pygame.K_a]: car.drive(-1)

        space.step(1 / 60.0)
        car.check_debris_and_wheels()
        check_lava_interaction()

        if current_map == 1:
            crusher.update(car, ragdolls)

    # Render Phase
    if current_map == 1:
        crusher.draw(screen)

    car.draw(screen)
    for rd in ragdolls:
        rd.draw(screen)

    draw_ui(screen)

    if menu_open:
        draw_car_select_menu(screen)

    draw_weapon_cursor(screen, (mx, my), current_weapon_idx, attack_animation_frame, is_mouse_down and current_weapon_idx == 4 and not menu_open)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()