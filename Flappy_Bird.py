"""
AI Driven Game Suite

Game: Flappy Bird

Description:
A Python implementation of Flappy Bird featuring both
manual gameplay and an optional predictive AI controller.

Technologies:
- Python
- Pygame
"""

import os
import random
import sys

import pygame

pygame.init()
WIDTH, HEIGHT = 400, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 28)

# Game configuration
GRAVITY = 0.5
FLAP_STRENGTH = -8
PIPE_GAP = 150
PIPE_WIDTH = 60
PIPE_SPEED = 3
PIPE_INTERVAL = 1500  # ms
GROUND_HEIGHT = 100

def load_image(name):
    """Load an image from the project directory."""
    path = os.path.join(os.path.dirname(__file__), name)
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"Warning: could not load {name}: {e}")
        return None

class Bird:
    def __init__(self):
        self.x = 80
        self.y = HEIGHT // 2
        self.vel = 0
        self.radius = 12
        self.alive = True

        # Load bird sprites
        self.img_up = load_image("bird_upflap.png")
        self.img_down = load_image("bird_downflap.png")

        if self.img_up and self.img_down:
            self.img_up = pygame.transform.smoothscale(self.img_up, (40, 30))
            self.img_down = pygame.transform.smoothscale(self.img_down, (40, 30))
            self.current_img = self.img_down
        else:
            self.current_img = None

        self._show_up_until = 0

    def flap(self):
        self.vel = FLAP_STRENGTH
        if self.img_up:
            self.current_img = self.img_up
            self._show_up_until = pygame.time.get_ticks() + 140

    def update(self):
        self.vel += GRAVITY
        self.y += self.vel

        if self.img_down and self.img_up:
            if self.vel > 0 or pygame.time.get_ticks() > self._show_up_until:
                self.current_img = self.img_down

        # ceiling / ground collision
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vel = 0
        if self.y + self.radius > HEIGHT - GROUND_HEIGHT:
            self.y = HEIGHT - GROUND_HEIGHT - self.radius
            self.alive = False

    def draw(self, surf):
        if self.current_img:
            angle = max(-45, min(45, -self.vel * 3))
            rotated = pygame.transform.rotate(self.current_img, angle)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(rotated, rect)
        else:
            pygame.draw.circle(surf, (255, 200, 0), (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
        if self.current_img:
            return self.current_img.get_rect(center=(int(self.x), int(self.y)))
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

class Pipe:
    def __init__(self, x):
        self.x = x
        self.width = PIPE_WIDTH
        self.gap_y = random.randint(80, HEIGHT - 80 - PIPE_GAP - GROUND_HEIGHT)
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self, surf):
        pygame.draw.rect(surf, (34, 139, 34), (self.x, 0, self.width, self.gap_y))
        pygame.draw.rect(surf, (34, 139, 34),
                         (self.x, self.gap_y + PIPE_GAP, self.width,
                          HEIGHT - (self.gap_y + PIPE_GAP) - GROUND_HEIGHT))

    def collides_with(self, rect):
        top_rect = pygame.Rect(self.x, 0, self.width, self.gap_y)
        bottom_rect = pygame.Rect(self.x, self.gap_y + PIPE_GAP, self.width,
                                  HEIGHT - (self.gap_y + PIPE_GAP) - GROUND_HEIGHT)
        return rect.colliderect(top_rect) or rect.colliderect(bottom_rect)

def draw_background(surf, bg_img):
    if bg_img:
        bg = pygame.transform.smoothscale(bg_img, (WIDTH, HEIGHT))
        surf.blit(bg, (0, 0))
    else:
        surf.fill((135, 206, 235))

def draw_ground(surf, base_img, base_x):
    if base_img:
        base_img_scaled = pygame.transform.smoothscale(base_img, (WIDTH, GROUND_HEIGHT))
        surf.blit(base_img_scaled, (base_x, HEIGHT - GROUND_HEIGHT))
        surf.blit(base_img_scaled, (base_x + WIDTH, HEIGHT - GROUND_HEIGHT))
    else:
        pygame.draw.rect(surf, (150, 111, 51), (0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))

def draw_text(surf, text, x, y, color=(0, 0, 0)):
    img = FONT.render(text, True, color)
    surf.blit(img, (x, y))

def main():
    bg_img = load_image("background.png")
    base_img = load_image("base.png")

    bird = Bird()
    pipes = []
    score = 0
    last_pipe_time = pygame.time.get_ticks() - PIPE_INTERVAL
    ai_enabled = False
    running = True
    game_over = False

    base_x = 0  # for scrolling ground

    while running:
        CLOCK.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE and bird.alive and not ai_enabled:
                    bird.flap()
                if event.key == pygame.K_a:
                    ai_enabled = not ai_enabled
                if event.key == pygame.K_r and game_over:
                    bird = Bird()
                    pipes = []
                    score = 0
                    last_pipe_time = pygame.time.get_ticks() - PIPE_INTERVAL
                    base_x = 0
                    game_over = False

        if bird.alive and not game_over:
            
            base_x -= PIPE_SPEED
            if base_x <= -WIDTH:
                base_x = 0

            
            now = pygame.time.get_ticks()
            if now - last_pipe_time > PIPE_INTERVAL:
                pipes.append(Pipe(WIDTH + 10))
                last_pipe_time = now

            # Predictive AI controller
            if ai_enabled:
                next_pipe = None
                for p in pipes:
                    if p.x + p.width >= bird.x - bird.radius:
                        next_pipe = p
                        break
                if next_pipe:
                    gap_center_y = next_pipe.gap_y + PIPE_GAP / 2
                    distance_x = next_pipe.x - bird.x
                    if (bird.y > gap_center_y + 6 and distance_x < 180) or \
                       (bird.y > gap_center_y + 20 and distance_x < 260):
                        bird.flap()

            bird.update()

            to_remove = []
            for p in pipes:
                p.update()
                if p.collides_with(bird.get_rect()):
                    bird.alive = False
                if not p.passed and p.x + p.width < bird.x:
                    p.passed = True
                    score += 1
                if p.x + p.width < -10:
                    to_remove.append(p)
            for r in to_remove:
                pipes.remove(r)

            if not bird.alive:
                game_over = True

        
        draw_background(WIN, bg_img)
        for p in pipes:
            p.draw(WIN)
        draw_ground(WIN, base_img, base_x)
        bird.draw(WIN)
        draw_text(WIN, f"Score: {score}", 10, 10)
        draw_text(WIN, f"AI: {'ON' if ai_enabled else 'OFF'} (A)", 10, 36)
        if game_over:
            draw_text(WIN, "GAME OVER - Press R to restart", WIDTH // 2 - 140, HEIGHT // 2 - 10, (200, 0, 0))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
