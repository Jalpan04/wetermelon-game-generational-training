import pygame
import random
import math
import sys
from pygame import gfxdraw

pygame.init()

# Game Constants
UNIT = 12
GAME_WIDTH, GAME_HEIGHT = int(20.4 * UNIT), int(31.9 * UNIT)
UI_HEIGHT = 95
WIDTH, HEIGHT = GAME_WIDTH, GAME_HEIGHT + UI_HEIGHT
FPS = 60
GRAVITY = 0.3
FRICTION = 0.95
WHITE = (255, 255, 255)
DARK = (44, 62, 80)
UI_BG = (52, 73, 94)
RED = (231, 76, 60)
DROP_DELAY = 15
GAME_OVER_LINE = UI_HEIGHT + 60

fruit_types = [
    {"color": (74, 144, 226), "radius": UNIT * 1.00, "value": 1, "accent": (53, 122, 189), "glow": (174, 214, 255)},
    {"color": (255, 107, 107), "radius": UNIT * 1.25, "value": 2, "accent": (229, 90, 90), "glow": (255, 207, 207)},
    {"color": (192, 57, 43), "radius": UNIT * 1.50, "value": 4, "accent": (146, 43, 33), "glow": (255, 157, 143)},
    {"color": (255, 140, 66), "radius": UNIT * 1.75, "value": 8, "accent": (245, 124, 0), "glow": (255, 240, 166)},
    {"color": (255, 217, 61), "radius": UNIT * 2.00, "value": 12, "accent": (251, 192, 45), "glow": (255, 255, 161)},
    {"color": (170, 0, 255), "radius": UNIT * 2.30, "value": 20, "accent": (98, 0, 234), "glow": (220, 150, 255)},
    {"color": (255, 165, 0), "radius": UNIT * 2.60, "value": 30, "accent": (230, 81, 0), "glow": (255, 215, 150)},
    {"color": (0, 184, 148), "radius": UNIT * 3.00, "value": 40, "accent": (0, 105, 92), "glow": (150, 255, 228)},
    {"color": (253, 203, 110), "radius": UNIT * 3.50, "value": 60, "accent": (245, 127, 23), "glow": (255, 253, 210)},
    {"color": (108, 92, 231), "radius": UNIT * 4.00, "value": 100, "accent": (81, 45, 168), "glow": (208, 192, 255)},
    {"color": (46, 204, 113), "radius": UNIT * 4.50, "value": 200, "accent": (30, 132, 73), "glow": (196, 255, 213)},
]

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fruity - Drop Anytime")
title_font = pygame.font.SysFont("Arial", 32, bold=True)
score_font = pygame.font.SysFont("Arial", 20, bold=True)
next_font = pygame.font.SysFont("Arial", 16, bold=True)
game_over_font = pygame.font.SysFont("Arial", 48, bold=True)
restart_font = pygame.font.SysFont("Arial", 24, bold=True)
clock = pygame.time.Clock()

fruits = []
sparkles = []
score = 0
drop_timer = 0
game_over = False
dropped_fruits = []

def draw_dotted_line(surface, color, start_pos, end_pos, dash_length=10, gap_length=5):
    x1, y1 = start_pos
    x2, y2 = end_pos
    total_length = math.hypot(x2 - x1, y2 - y1)
    dx = (x2 - x1) / total_length
    dy = (y2 - y1) / total_length
    dist = 0
    while dist < total_length:
        start_x = int(x1 + dx * dist)
        start_y = int(y1 + dy * dist)
        end_x = int(x1 + dx * min(dist + dash_length, total_length))
        end_y = int(y1 + dy * min(dist + dash_length, total_length))
        pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y))
        dist += dash_length + gap_length

class Fruit:
    def __init__(self, x, y, ftype):
        self.x = x
        self.y = y + UI_HEIGHT
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = 0
        self.type = ftype
        self.base_radius = fruit_types[ftype]["radius"]
        self.color = fruit_types[ftype]["color"]
        self.accent = fruit_types[ftype]["accent"]
        self.glow = fruit_types[ftype]["glow"]
        self.value = fruit_types[ftype]["value"]
        self.scale = 1.0
        self.anim_timer = 0
        self.glow_pulse = 0
        self.drop_timer = 60

    def update(self):
        self.vy += GRAVITY
        self.vx *= FRICTION
        self.vy *= FRICTION

        if abs(self.vx) < 0.05: self.vx = 0
        if abs(self.vy) < 0.05: self.vy = 0

        self.x += self.vx
        self.y += self.vy

        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = 0
        elif self.x + self.radius > GAME_WIDTH:
            self.x = GAME_WIDTH - self.radius
            self.vx = 0

        if self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius
            self.vy = 0

        if self.anim_timer > 0:
            self.anim_timer -= 1
            self.scale = 1.0 + 0.3 * math.sin((self.anim_timer / 10) * math.pi)
        else:
            self.scale = 1.0

        self.glow_pulse += 0.1
        if self.drop_timer > 0:
            self.drop_timer -= 1

    @property
    def radius(self):
        return self.base_radius * self.scale

    def draw(self, surface):
        r = int(self.radius)
        x, y = int(self.x), int(self.y)
        glow_alpha = int(30 + 20 * math.sin(self.glow_pulse))
        glow_surface = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.glow, glow_alpha), (r * 1.5, r * 1.5), r * 1.2)
        surface.blit(glow_surface, (x - r * 1.5, y - r * 1.5), special_flags=pygame.BLEND_ALPHA_SDL2)

        for i in range(3):
            alpha = 255 - i * 60
            radius_offset = i * 0.15
            circle_color = tuple(max(0, c - i * 30) for c in self.accent)
            gfxdraw.filled_circle(surface, x, y, int(r * (1 - radius_offset)), (*circle_color, alpha))

        gfxdraw.filled_circle(surface, x, y, r, self.accent)
        gfxdraw.filled_circle(surface, x - int(r * 0.2), y - int(r * 0.2), int(r * 0.9), self.color)
        highlight_r = int(r * 0.4)
        highlight_color = tuple(min(255, c + 60) for c in self.color)
        gfxdraw.filled_circle(surface, x - int(r * 0.3), y - int(r * 0.3), highlight_r, highlight_color)
        gfxdraw.aacircle(surface, x, y, r, WHITE)

class Sparkle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = random.uniform(1, 3)
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-4, -1)
        self.alpha = 255
        self.color = color
        self.rotation = random.uniform(0, 360)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.alpha -= 8
        self.rotation += 5

    def draw(self, surface):
        if self.alpha > 0:
            points = []
            for i in range(8):
                angle = (i * 45 + self.rotation) * math.pi / 180
                r = self.radius * 2 if i % 2 == 0 else self.radius
                px = self.x + math.cos(angle) * r
                py = self.y + math.sin(angle) * r
                points.append((px, py))

            sparkle_surface = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
            color_with_alpha = (*self.color[:3], max(0, self.alpha))
            pygame.draw.polygon(sparkle_surface, color_with_alpha,
                                [(p[0] - self.x + self.radius * 3, p[1] - self.y + self.radius * 3) for p in points])
            surface.blit(sparkle_surface, (self.x - self.radius * 3, self.y - self.radius * 3))

def draw_gradient_background():
    pygame.draw.rect(screen, UI_BG, (0, 0, WIDTH, UI_HEIGHT))
    for y in range(UI_HEIGHT):
        ratio = y / UI_HEIGHT
        r = int(52 + (62 - 52) * ratio)
        g = int(73 + (83 - 73) * ratio)
        b = int(94 + (104 - 94) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    for y in range(UI_HEIGHT, UI_HEIGHT + GAME_HEIGHT // 2):
        ratio = (y - UI_HEIGHT) / (GAME_HEIGHT // 2)
        r = int(135 + (70 - 135) * ratio)
        g = int(206 + (130 - 206) * ratio)
        b = int(235 + (180 - 235) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    for y in range(UI_HEIGHT + GAME_HEIGHT // 2, HEIGHT):
        ratio = (y - UI_HEIGHT - GAME_HEIGHT // 2) / (GAME_HEIGHT // 2)
        r = int(152 + (120 - 152) * ratio)
        g = int(251 + (200 - 251) * ratio)
        b = int(152 + (120 - 152) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
    pygame.draw.line(screen, (30, 40, 50), (0, UI_HEIGHT), (WIDTH, UI_HEIGHT), 2)
    if not game_over:
        pygame.draw.line(screen, RED, (0, GAME_OVER_LINE), (WIDTH, GAME_OVER_LINE), 2)

def draw_ui():
    title_text = title_font.render("FRUITY", True, WHITE)
    title_shadow = title_font.render("FRUITY", True, (20, 30, 40))
    screen.blit(title_shadow, title_text.get_rect(center=(WIDTH // 2 + 2, 27)))
    screen.blit(title_text, title_text.get_rect(center=(WIDTH // 2, 25)))

    score_text = score_font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_font.render(f"Score: {score}", True, (20, 30, 40)), (21, 56))
    screen.blit(score_text, (20, 55))

    next_text = next_font.render("Next:", True, WHITE)
    screen.blit(next_font.render("Next:", True, (20, 30, 40)), (WIDTH - 101, 51))
    screen.blit(next_text, (WIDTH - 100, 50))

    start_x = WIDTH - 120
    for i, ftype in enumerate(next_fruit_queue):
        fruit_color = fruit_types[ftype]["color"]
        fruit_radius = int(fruit_types[ftype]["radius"] * 0.4)
        x_pos = start_x + i * 40
        y_pos = 80
        pygame.draw.circle(screen, (20, 30, 40), (x_pos, y_pos), fruit_radius + 2)
        pygame.draw.circle(screen, fruit_types[ftype]["accent"], (x_pos, y_pos), fruit_radius)
        pygame.draw.circle(screen, fruit_color, (x_pos - int(fruit_radius * 0.2), y_pos - int(fruit_radius * 0.2)),
                           int(fruit_radius * 0.8))

def draw_game_over():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    screen.blit(game_over_font.render("GAME OVER", True, RED),
                game_over_font.render("GAME OVER", True, RED).get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
    screen.blit(score_font.render(f"Final Score: {score}", True, WHITE),
                score_font.render(f"Final Score: {score}", True, WHITE).get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    screen.blit(restart_font.render("Press R to Restart", True, WHITE),
                restart_font.render("Press R to Restart", True, WHITE).get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))

def spawn_sparkles(x, y, color, count=15):
    for _ in range(count):
        sparkles.append(Sparkle(x, y, color))

def check_game_over():
    global game_over
    for fruit in fruits:
        if fruit.drop_timer <= 0 and fruit.y - fruit.radius <= GAME_OVER_LINE:
            game_over = True
            return

def restart_game():
    global fruits, sparkles, score, drop_timer, game_over, next_fruit, next_fruit_queue, dropped_fruits
    fruits = []
    sparkles = []
    score = 0
    drop_timer = 0
    game_over = False
    dropped_fruits = []
    next_fruit = Fruit(GAME_WIDTH // 2, 30, random.randint(0, 2))
    next_fruit_queue = [random.randint(0, 2), random.randint(0, 2)]

def resolve_collisions():
    global score
    for _ in range(3):
        for i in range(len(fruits)):
            for j in range(i + 1, len(fruits)):
                f1, f2 = fruits[i], fruits[j]
                dx = f2.x - f1.x
                dy = f2.y - f1.y
                dist = math.hypot(dx, dy)
                min_dist = f1.radius + f2.radius
                if dist < min_dist:
                    if f1.type == f2.type and f1.type < len(fruit_types) - 1:
                        mid_x = (f1.x + f2.x) / 2
                        mid_y = (f1.y + f2.y) / 2
                        new_fruit = Fruit(mid_x, mid_y - UI_HEIGHT, f1.type + 1)
                        new_fruit.vy = -2
                        new_fruit.anim_timer = 15
                        spawn_sparkles(mid_x, mid_y, fruit_types[f1.type]["color"])
                        fruits.pop(j)
                        fruits.pop(i)
                        fruits.append(new_fruit)
                        score += new_fruit.value
                        return
                    nx, ny = dx / (dist or 1), dy / (dist or 1)
                    overlap = min_dist - dist
                    m1 = m2 = 1
                    total = m1 + m2
                    f1.x -= nx * overlap * (m2 / total)
                    f1.y -= ny * overlap * (m2 / total)
                    f2.x += nx * overlap * (m1 / total)
                    f2.y += ny * overlap * (m1 / total)
                    f1.vx *= 0.9
                    f1.vy *= 0.9
                    f2.vx *= 0.9
                    f2.vy *= 0.9

next_fruit = Fruit(GAME_WIDTH // 2, 30, random.randint(0, 2))
next_fruit_queue = [random.randint(0, 2), random.randint(0, 2)]

running = True
while running:
    clock.tick(FPS)
    draw_gradient_background()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                restart_game()
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mx, my = pygame.mouse.get_pos()
            if my > UI_HEIGHT and drop_timer <= 0:
                next_fruit.x = mx
                fruits.append(next_fruit)
                drop_timer = DROP_DELAY
                next_fruit = Fruit(GAME_WIDTH // 2, 30, next_fruit_queue[0])
                next_fruit_queue[0] = next_fruit_queue[1]
                next_fruit_queue[1] = random.randint(0, 2)

    if not game_over:
        if drop_timer > 0:
            drop_timer -= 1

        for fruit in fruits:
            fruit.update()
        for sparkle in sparkles:
            sparkle.update()
        sparkles[:] = [s for s in sparkles if s.alpha > 0]
        resolve_collisions()
        check_game_over()

        mx, my = pygame.mouse.get_pos()
        if my > UI_HEIGHT and drop_timer <= 0:
            next_fruit.x = mx

            # ✨ Dotted drop indicator
            draw_dotted_line(screen, next_fruit.color, (int(next_fruit.x), UI_HEIGHT + 30), (int(next_fruit.x), HEIGHT), 8, 6)

            next_fruit.draw(screen)

        for fruit in fruits:
            fruit.draw(screen)
        for sparkle in sparkles:
            sparkle.draw(screen)
        draw_ui()
    else:
        draw_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit()
