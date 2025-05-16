import pygame
import sys
import numpy as np

# Check for PyAudio installation as per request
try:
    import pyaudio
except ImportError:
    print("Warning: PyAudio is not installed. Audio will still be handled by Pygame's mixer.")

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)  # Mono, 44.1kHz, 16-bit

# Generate Atari-style beep and boop sounds (square waves)
def generate_square_wave(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sign(np.sin(2 * np.pi * frequency * t))  # Square wave
    wave = (wave * 32767 / 2).astype(np.int16)  # Scale to 16-bit PCM
    return wave

# Create beep (higher pitch, ~800 Hz) and boop (lower pitch, ~400 Hz)
beep_wave = generate_square_wave(800, 0.1)  # 100ms beep
boop_wave = generate_square_wave(400, 0.15)  # 150ms boop
beep_sound = pygame.mixer.Sound(beep_wave)
boop_sound = pygame.mixer.Sound(boop_wave)

# Window dimensions
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout")

# Colors (RGB tuples)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Paddle setup
PADDLE_WIDTH, PADDLE_HEIGHT = 60, 10
paddle = pygame.Rect(WIDTH // 2 - PADDLE_WIDTH // 2, HEIGHT - 20, PADDLE_WIDTH, PADDLE_HEIGHT)

# Ball setup
BALL_SIZE = 10
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2, BALL_SIZE, BALL_SIZE)
ball_dx, ball_dy = 3, 3  # Ball velocity
ball_attached = True  # Ball starts on paddle

# Bricks setup
BRICK_WIDTH, BRICK_HEIGHT = 50, 20
BRICK_ROWS, BRICK_COLS = 5, 10
bricks = [pygame.Rect(50 * x + 10, 20 * y + 10, BRICK_WIDTH, BRICK_HEIGHT) 
          for x in range(BRICK_COLS) for y in range(BRICK_ROWS)]

# Score and font
score = 0
font = pygame.font.Font(None, 36)

# Game states
game_state = 'start'  # Possible states: 'start', 'playing', 'over', 'prompt'

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Main game loop
while True:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state == 'start':
                    game_state = 'playing'
                elif game_state == 'playing' and ball_attached:
                    ball_dy = -3
                    ball_attached = False
            elif game_state == 'prompt':
                if event.key == pygame.K_y:
                    # Restart game
                    ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2, BALL_SIZE, BALL_SIZE)
                    paddle = pygame.Rect(WIDTH // 2 - PADDLE_WIDTH // 2, HEIGHT - 20, PADDLE_WIDTH, PADDLE_HEIGHT)
                    bricks = [pygame.Rect(50 * x + 10, 20 * y + 10, BRICK_WIDTH, BRICK_HEIGHT) 
                              for x in range(BRICK_COLS) for y in range(BRICK_ROWS)]
                    score = 0
                    game_state = 'start'
                    ball_attached = True
                elif event.key == pygame.K_n:
                    sys.exit()

    # Game logic for 'playing' state
    if game_state == 'playing':
        # Move paddle with mouse
        mouse_x = pygame.mouse.get_pos()[0]
        paddle.x = mouse_x - PADDLE_WIDTH // 2
        if paddle.left < 0:
            paddle.left = 0
        if paddle.right > WIDTH:
            paddle.right = WIDTH

        # Move ball
        if not ball_attached:
            ball.x += ball_dx
            ball.y += ball_dy

            # Wall collisions
            if ball.left < 0 or ball.right > WIDTH:
                ball_dx = -ball_dx
            if ball.top < 0:
                ball_dy = -ball_dy
            if ball.bottom > HEIGHT:
                game_state = 'prompt'

            # Paddle collision
            if ball.colliderect(paddle):
                ball_dy = -ball_dy
                beep_sound.play()  # Play beep sound

            # Brick collisions
            for brick in bricks[:]:
                if ball.colliderect(brick):
                    bricks.remove(brick)
                    ball_dy = -ball_dy
                    score += 1
                    boop_sound.play()  # Play boop sound

        else:
            # Keep ball attached to paddle
            ball.x = paddle.x + PADDLE_WIDTH // 2 - BALL_SIZE // 2

    # Drawing
    screen.fill(BLACK)
    if game_state == 'start':
        start_text = font.render("Press SPACE to Start", True, WHITE)
        screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2))
    elif game_state == 'playing':
        pygame.draw.rect(screen, WHITE, paddle)
        for brick in bricks:
            pygame.draw.rect(screen, RED, brick)
        pygame.draw.ellipse(screen, WHITE, ball)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
    elif game_state == 'over':
        over_text = font.render(f"Game Over! Score: {score}", True, WHITE)
        restart_text = font.render("Press SPACE to Restart", True, WHITE)
        screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 20))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))
    elif game_state == 'prompt':
        over_text = font.render(f"Game Over! Score: {score}", True, WHITE)
        prompt_text = font.render("Play again? (Y/N)", True, WHITE)
        screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 20))
        screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 + 20))

    # Update display
    pygame.display.flip()

    # Cap frame rate at 60 FPS
    clock.tick(60)
