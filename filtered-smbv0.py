import pygame
import sys
import numpy as np
import pyaudio
import threading
import random

# Initialize Pygame
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 400
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 0)  # Fixed size, no resizable flag
pygame.display.set_caption("Super Mario Bros. 1 Inspired")
clock = pygame.time.Clock()

# Constants
TILE_SIZE = 16  # Smaller tiles for 600x400 window
GRAVITY = 0.5
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
GRAY = (169, 169, 169)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
BLUE = (0, 0, 255)

# Sound setup with PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=True)

def generate_square_wave(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sign(np.sin(2 * np.pi * frequency * t))
    return wave

def play_sound(frequency, duration):
    wave = generate_square_wave(frequency, duration)
    stream.write(wave.astype(np.float32).tobytes())

def play_sound_thread(frequency, duration):
    threading.Thread(target=play_sound, args=(frequency, duration)).start()

# Procedural level generation
def generate_level(world, level):
    LEVEL_WIDTH = 200
    LEVEL_HEIGHT = 15
    level_data = [[0 for _ in range(LEVEL_WIDTH)] for _ in range(LEVEL_HEIGHT)]
    # Ground
    for x in range(LEVEL_WIDTH):
        level_data[14][x] = 1
        level_data[13][x] = 1
    # Platforms and blocks
    for x in range(10, LEVEL_WIDTH - 10, 20):
        height = random.randint(8, 11)
        for w in range(random.randint(3, 6)):
            if x + w < LEVEL_WIDTH:
                level_data[height][x + w] = 2  # Bricks
        if random.random() > 0.5 and x + 2 < LEVEL_WIDTH:
            level_data[height - 1][x + 2] = 3  # Question block
    # Pipes
    if world > 1:
        for x in range(30, LEVEL_WIDTH - 20, 40):
            for y in range(11, 14):
                level_data[y][x] = 4
    # Flagpole
    flagpole_x = (LEVEL_WIDTH - 5) * TILE_SIZE
    for y in range(5, 14):
        level_data[y][LEVEL_WIDTH - 5] = 5
    # Enemies
    enemies = [Goomba(200 + i * 100, WINDOW_HEIGHT - 2 * TILE_SIZE - 32) for i in range(3)]
    powerups = []
    return level_data, enemies, powerups, flagpole_x, LEVEL_WIDTH, LEVEL_HEIGHT

# Game state
current_world = 1
current_level = 1
score = 0
lives = 3
font = pygame.font.Font(None, 24)
camera_x = 0

# Mario class
class Mario:
    def __init__(self):
        self.reset()
        self.width = 16
        self.height = 16
        self.state = "small"

    def update(self, level_data, flagpole_x, LEVEL_WIDTH, LEVEL_HEIGHT):
        global camera_x, score, lives, current_world, current_level
        # Apply gravity
        self.vy += GRAVITY
        # Y movement
        new_y = self.y + self.vy
        if self.vy > 0:  # Falling
            left_tile = int(self.x // TILE_SIZE)
            right_tile = int((self.x + self.width - 1) // TILE_SIZE)
            for tx in range(left_tile, min(right_tile + 1, LEVEL_WIDTH)):
                ty = int((new_y + self.height) // TILE_SIZE)
                if ty >= LEVEL_HEIGHT or ty < 0:
                    continue
                tile = level_data[ty][tx]
                if tile in [1, 2, 3, 4]:
                    self.y = ty * TILE_SIZE - self.height
                    self.vy = 0
                    self.on_ground = True
                    break
            else:
                self.y = new_y
                self.on_ground = False
        elif self.vy < 0:  # Jumping
            left_tile = int(self.x // TILE_SIZE)
            right_tile = int((self.x + self.width - 1) // TILE_SIZE)
            for tx in range(left_tile, min(right_tile + 1, LEVEL_WIDTH)):
                ty = int(new_y // TILE_SIZE)
                if ty < 0 or ty >= LEVEL_HEIGHT:
                    continue
                tile = level_data[ty][tx]
                if tile in [1, 2, 3, 4]:
                    self.y = (ty + 1) * TILE_SIZE
                    self.vy = 0
                    if tile == 3:
                        level_data[ty][tx] = 2
                        play_sound_thread(659, 0.1)
                        score += 100
                        if random.random() > 0.7:
                            powerups.append(PowerUp(tx * TILE_SIZE, ty * TILE_SIZE))
                    break
            else:
                self.y = new_y
        # X movement
        new_x = self.x + self.vx
        if self.vx != 0:
            top_tile = int(self.y // TILE_SIZE)
            bottom_tile = int((self.y + self.height - 1) // TILE_SIZE)
            direction = 1 if self.vx > 0 else -1
            edge_x = new_x + self.width if self.vx > 0 else new_x
            tx_check = int(edge_x // TILE_SIZE)
            for ty in range(top_tile, min(bottom_tile + 1, LEVEL_HEIGHT)):
                if tx_check < 0 or tx_check >= LEVEL_WIDTH or ty < 0:
                    continue
                tile = level_data[ty][tx_check]
                if tile in [1, 2, 3, 4]:
                    self.x = (tx_check - direction) * TILE_SIZE + (0 if direction > 0 else TILE_SIZE - self.width)
                    break
            else:
                self.x = new_x
        # Camera
        if self.x > camera_x + WINDOW_WIDTH / 2:
            camera_x = self.x - WINDOW_WIDTH / 2
        if camera_x < 0:
            camera_x = 0
        # Death or win
        if self.y > WINDOW_HEIGHT:
            lives -= 1
            self.reset()
            if lives <= 0:
                return "game_over"
        if flagpole_x and self.x + self.width > flagpole_x:
            play_sound_thread(784, 0.5)
            current_level += 1
            if current_level > 4:
                current_level = 1
                current_world += 1
                if current_world > 8:
                    return "game_won"
            self.reset()
            return "next_level"
        return None

    def reset(self):
        self.x = 50
        self.y = WINDOW_HEIGHT - 2 * TILE_SIZE - 16
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        global camera_x
        camera_x = 0

    def draw(self):
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, RED if self.state == "small" else BLUE, (screen_x, self.y, self.width, self.height))
        eye_x1, eye_x2 = screen_x + 4, screen_x + 12
        eye_y = self.y + 4
        pygame.draw.circle(screen, BLACK, (int(eye_x1), int(eye_y)), 2)
        pygame.draw.circle(screen, BLACK, (int(eye_x2), int(eye_y)), 2)

# Enemy class (Goomba)
class Goomba:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.vx = -2

    def update(self, level_data, LEVEL_WIDTH, LEVEL_HEIGHT):
        self.x += self.vx
        # Wall collision
        tx = int((self.x + (self.width if self.vx > 0 else 0)) // TILE_SIZE)
        ty_top = int(self.y // TILE_SIZE)
        ty_bottom = int((self.y + self.height - 1) // TILE_SIZE)
        for ty in range(ty_top, min(ty_bottom + 1, LEVEL_HEIGHT)):
            if tx < 0 or tx >= LEVEL_WIDTH:
                self.vx = -self.vx
                break
            if level_data[ty][tx] in [1, 2, 3, 4]:
                self.vx = -self.vx
                break
        # Gravity
        self.y += 2
        left_tile = int(self.x // TILE_SIZE)
        right_tile = int((self.x + self.width - 1) // TILE_SIZE)
        for tx in range(left_tile, min(right_tile + 1, LEVEL_WIDTH)):
            ty = int((self.y + self.height) // TILE_SIZE)
            if ty >= LEVEL_HEIGHT:
                continue
            if level_data[ty][tx] in [1, 2, 3, 4]:
                self.y = ty * TILE_SIZE - self.height
                break

    def draw(self):
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, BROWN, (screen_x, self.y, self.width, self.height))

# Power-up class (Mushroom)
class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.vy = -2

    def update(self, level_data, LEVEL_WIDTH, LEVEL_HEIGHT):
        self.y += self.vy
        if self.vy > 0:
            left_tile = int(self.x // TILE_SIZE)
            right_tile = int((self.x + self.width - 1) // TILE_SIZE)
            for tx in range(left_tile, min(right_tile + 1, LEVEL_WIDTH)):
                ty = int((self.y + self.height) // TILE_SIZE)
                if ty >= LEVEL_HEIGHT:
                    continue
                if level_data[ty][tx] in [1, 2, 3, 4]:
                    self.y = ty * TILE_SIZE - self.height
                    self.vy = 0
                    break
            else:
                self.vy += GRAVITY

    def draw(self):
        screen_x = self.x - camera_x
        pygame.draw.rect(screen, GREEN, (screen_x, self.y, self.width, self.height))

# Initialize entities
mario = Mario()
level_data, enemies, powerups, flagpole_x, LEVEL_WIDTH, LEVEL_HEIGHT = generate_level(current_world, current_level)

# Main game loop
running = True
while running:
    current_key = f"{current_world}-{current_level}"

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                mario.vx = -5
            elif event.key == pygame.K_RIGHT:
                mario.vx = 5
            elif event.key == pygame.K_SPACE and mario.on_ground:
                mario.vy = -12
                mario.on_ground = False
                play_sound_thread(440, 0.1)
        elif event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                mario.vx = 0

    # Update
    result = mario.update(level_data, flagpole_x, LEVEL_WIDTH, LEVEL_HEIGHT)
    if result == "game_over":
        screen.fill(BLACK)
        text = font.render("Game Over", True, WHITE)
        screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, WINDOW_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait
