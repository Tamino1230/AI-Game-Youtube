import pygame
import random
import time
import math
import webbrowser  # Import webbrowser module

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Player settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
PLAYER_SPEED = 5
PLAYER_JUMP = 12.5  # Reduced jump height
GRAVITY = 1

# Barrel settings
BARREL_WIDTH = 20
BARREL_HEIGHT = 20
BARREL_SPEED = 3
BARREL_SPAWN_COUNT = 10000  # Number of barrels to spawn

# Ladder settings
LADDER_WIDTH = 40
LADDER_HEIGHT = 120

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Donkey Money")

# Load images
player_image = pygame.image.load('assets/player.png').convert_alpha()
barrel_image = pygame.image.load('assets/barrel.png').convert_alpha()
donkey_money_image = pygame.image.load('assets/donkey_money.png').convert_alpha()
platform_image = pygame.image.load('assets/platform.png').convert_alpha()
ladder_image = pygame.image.load('assets/ladder.png').convert_alpha()
goal_image = pygame.image.load('assets/goal.png').convert_alpha()
banana_peel_image = pygame.image.load('assets/banana_peel.png').convert_alpha()

# Load sounds
jump_sound = pygame.mixer.Sound('assets/jump.wav')
barrel_sound = pygame.mixer.Sound('assets/barrel.wav')
pygame.mixer.music.load('assets/background.wav')
pygame.mixer.music.play(-1)  # Play background music on loop
slip_sound = pygame.mixer.Sound('assets/slip.wav')  # Load slip sound

# Load explosion sound and GIF (only 2 frames)
explosion_sound = pygame.mixer.Sound('assets/explosion.wav')
explosion_gif = [pygame.image.load(f'assets/explosion/frame_{i}.png').convert_alpha() for i in range(2)]

# Use already loaded images for credits screen
random_images = [player_image, barrel_image, donkey_money_image, platform_image, ladder_image, goal_image, banana_peel_image]

# Platform settings
PLATFORM_HEIGHT = 20

# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.image = pygame.transform.scale(platform_image, (width, PLATFORM_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Ladder class
class Ladder(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(ladder_image, (LADDER_WIDTH, LADDER_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(player_image, (PLAYER_WIDTH, PLAYER_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH // 2
        self.rect.y = SCREEN_HEIGHT - PLAYER_HEIGHT
        self.speed_x = 0
        self.speed_y = 0
        self.on_ground = False
        self.on_ladder = False
        self.climbing = False  # New attribute to track climbing state
        self.slipping = False  # New attribute to track slipping state
        self.facing_right = True  # New attribute to track facing direction

    def update(self):
        if self.on_ladder:
            self.speed_y = 0  # Stop gravity effect when on ladder
            if self.climbing:
                self.rect.y -= PLAYER_SPEED  # Smooth climbing
        else:
            self.speed_y += GRAVITY
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.speed_y = 0
            self.on_ground = True

        # Check for collisions with platforms
        if not self.on_ladder:  # Ignore platform collisions while on ladder
            platform_collisions = pygame.sprite.spritecollide(self, platforms, False)
            if platform_collisions:
                if self.speed_y > 0:  # Falling down
                    self.rect.bottom = platform_collisions[0].rect.top
                    self.speed_y = 0
                    self.on_ground = True
                elif self.speed_y < 0:  # Jumping up
                    self.rect.top = platform_collisions[0].rect.bottom
                    self.speed_y = 0

        # Check for collisions with ladders
        ladder_collisions = pygame.sprite.spritecollide(self, ladders, False)
        if ladder_collisions:
            self.on_ladder = True
            self.speed_y = 0
            if self.rect.bottom > ladder_collisions[0].rect.bottom:
                self.rect.bottom = ladder_collisions[0].rect.bottom
            elif self.rect.top < ladder_collisions[0].rect.top:
                self.rect.top = ladder_collisions[0].rect.top
        else:
            self.on_ladder = False
            self.climbing = False  # Stop climbing if not on ladder

        # Check for collisions with barrels and banana peels
        if pygame.sprite.spritecollideany(self, barrels):
            if isinstance(pygame.sprite.spritecollideany(self, barrels), BananaPeel):
                self.slip()
            else:
                global lives, running
                lives -= 1
                if lives <= 0:
                    CREDITS_SCREEN = True
                else:
                    self.rect.x = SCREEN_WIDTH // 2
                    self.rect.y = SCREEN_HEIGHT - PLAYER_HEIGHT

        # Flip player image based on direction
        if self.speed_x > 0:
            self.facing_right = True
        elif self.speed_x < 0:
            self.facing_right = False

        self.image = pygame.transform.scale(player_image, (PLAYER_WIDTH, PLAYER_HEIGHT))
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

    def slip(self):
        self.slipping = True
        self.speed_x *= -1  # Reverse direction on banana peel collision
        slip_sound.play()

    def jump(self):
        if self.on_ground and not self.on_ladder:
            self.speed_y = -PLAYER_JUMP
            self.on_ground = False
            jump_sound.play()

# Barrel class
class Barrel(pygame.sprite.Sprite): 
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(barrel_image, (BARREL_WIDTH, BARREL_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed_x = BARREL_SPEED
        self.speed_y = 0
        self.exploded = False

    def update(self):
        if not self.exploded and random.random() < 0.00005:  # 0.5% chance to explode
            self.explode()
        else:
            self.rect.x += self.speed_x
            self.rect.y += self.speed_y
            self.speed_y += GRAVITY

            # Check for collisions with platforms
            platform_collisions = pygame.sprite.spritecollide(self, platforms, False)
            if platform_collisions:
                if self.speed_y > 0:
                    self.rect.bottom = platform_collisions[0].rect.top
                    self.speed_y = 0

            # Change direction at screen edges
            if self.rect.right > SCREEN_WIDTH or self.rect.left < 0:
                self.speed_x = -self.speed_x

            # Move to next platform if at the edge
            if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
                self.rect.y += PLATFORM_HEIGHT + 10
                self.speed_x = -self.speed_x

            # Reset barrel if it falls off the screen
            if self.rect.top > SCREEN_HEIGHT:
                self.rect.x = random.randint(0, SCREEN_WIDTH - BARREL_WIDTH)
                self.rect.y = 0
                self.speed_x = BARREL_SPEED
                self.speed_y = 0

    def explode(self):
        self.exploded = True
        explosion = Explosion(self.rect.center)
        all_sprites.add(explosion)
        explosion_sound.play()
        self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.frames = explosion_gif
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50  # Time in milliseconds between frames

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.current_frame]

# Donkey Money class
class DonkeyMoney(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(donkey_money_image, (100, 100))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.snack_attack = False
        self.snack_timer = 0

    def launch_barrel(self):
        if self.snack_attack:
            banana_peel = BananaPeel(self.rect.x, self.rect.y)
            all_sprites.add(banana_peel)
            barrels.add(banana_peel)
        else:
            barrel = Barrel(self.rect.x, self.rect.y)
            all_sprites.add(barrel)
            barrels.add(barrel)

    def update(self):
        if random.random() < 0.001:  # 0.1% chance to start snack attack
            self.snack_attack = True
            self.snack_timer = 300  # Snack attack lasts for 5 seconds
        if self.snack_attack:
            self.snack_timer -= 1
            if self.snack_timer <= 0:
                self.snack_attack = False

# Banana Peel class
class BananaPeel(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(banana_peel_image, (BARREL_WIDTH, BARREL_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed_x = BARREL_SPEED
        self.speed_y = 0

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        self.speed_y += GRAVITY

        # Check for collisions with platforms
        platform_collisions = pygame.sprite.spritecollide(self, platforms, False)
        if platform_collisions:
            if self.speed_y > 0:
                self.rect.bottom = platform_collisions[0].rect.top
                self.speed_y = 0

        # Change direction at screen edges
        if self.rect.right > SCREEN_WIDTH or self.rect.left < 0:
            self.speed_x = -self.speed_x

        # Move to next platform if at the edge
        if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
            self.rect.y += PLATFORM_HEIGHT + 10
            self.speed_x = -self.speed_x

        # Reset banana peel if it falls off the screen
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.x = random.randint(0, SCREEN_WIDTH - BARREL_WIDTH)
            self.rect.y = 0
            self.speed_x = BARREL_SPEED
            self.speed_y = 0

# Goal class
class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(goal_image, (150, 150))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class BouncingImage(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.original_image = image
        self.image = pygame.transform.scale(self.original_image, (40, 40))  # Scale image to be tiny
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, max(0, SCREEN_WIDTH - self.rect.width))
        self.rect.y = random.randint(0, max(0, SCREEN_HEIGHT - self.rect.height))
        self.speed_x = random.choice([-3, 3])
        self.speed_y = random.choice([-3, 3])

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
            self.speed_x = -self.speed_x
        if self.rect.bottom >= SCREEN_HEIGHT or self.rect.top <= 0:
            self.speed_y = -self.speed_y

# Create sprite groups
all_sprites = pygame.sprite.Group()
barrels = pygame.sprite.Group()
platforms = pygame.sprite.Group()
ladders = pygame.sprite.Group()
explosions = pygame.sprite.Group()
bouncing_images = pygame.sprite.Group()

# Create player
player = Player()
all_sprites.add(player)

# Create platforms
platforms_data = [
    (0, SCREEN_HEIGHT - 2, SCREEN_WIDTH - 100),  # Floor 1 with gap
    (0, SCREEN_HEIGHT - 150, SCREEN_WIDTH - 200),  # Floor 2 with gap
    (200, SCREEN_HEIGHT - 270, SCREEN_WIDTH - 200),  # Floor 3 with gap
    (0, SCREEN_HEIGHT - 390, SCREEN_WIDTH - 50),  # Floor 4 (Rescue Zone) with gap
    (200, SCREEN_HEIGHT - 510, SCREEN_WIDTH - 0)  # Safe Zone
]
for x, y, width in platforms_data:
    platform = Platform(x, y, width)
    all_sprites.add(platform)
    platforms.add(platform)

# Create ladders
ladders_data = [
    (100, SCREEN_HEIGHT - 150),  # Ladder A
    (500, SCREEN_HEIGHT - 270),  # Ladder B
    (250, SCREEN_HEIGHT - 390),  # Ladder C
    (SCREEN_WIDTH // 2 - LADDER_WIDTH // 2 + 250, SCREEN_HEIGHT - 510)  # Ladder in Safe Zone
]
for x, y in ladders_data:
    ladder = Ladder(x, y)
    all_sprites.add(ladder)
    ladders.add(ladder)

# Create goal
goal = Goal(260, -32.5)
all_sprites.add(goal)

# Create Donkey Money
donkey_money = DonkeyMoney(180, 5)
all_sprites.add(donkey_money)

# Create bouncing images for credits screen
for img in random_images:
    bouncing_image = BouncingImage(img)
    bouncing_images.add(bouncing_image)

# Story mode settings
STORY_MODE = True
story_texts = [
    "Once upon a time, in a land where barrels ruled the skies...",
    "A brave player decided to climb the ladders of destiny...",
    "To rescue the golden banana from the evil Donkey Money...",
    "But beware! The barrels of doom are relentless...",
    "Will you reach the top and claim the golden banana?",
    "Or will the barrels send you tumbling down?",
    "The fate of the banana rests in your hands!"
]
current_story_index = 0
story_timer = 0
STORY_INTERVAL = 80  # Reduced time in frames to show each story text

# Retro Glitch Mode settings
RETRO_GLITCH_MODE = False
BIG_GLITCH_MODE = False
GLITCH_INTERVAL = 500  # Time in milliseconds between glitches
BIG_GLITCH_DURATION = 3000  # Duration of BIG GLITCH in milliseconds
last_glitch_time = 0
big_glitch_start_time = 0

# Reduce the chances of activating glitch modes
RETRO_GLITCH_CHANCE = 0.001  # 0.1% chance to activate glitch mode
BIG_GLITCH_CHANCE = 0.0002  # 0.02% chance to activate BIG GLITCH mode

def apply_retro_glitch_effect():
    for y in range(0, SCREEN_HEIGHT, 10):
        pygame.draw.line(screen, random.choice([RED, GREEN, BLUE]), (0, y), (SCREEN_WIDTH, y), 1)

# New visual glitch effect functions
def apply_color_shift_effect():
    for y in range(0, SCREEN_HEIGHT, 5):
        color = random.choice([RED, GREEN, BLUE, WHITE])
        pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y), 1)

def apply_pixelate_effect():
    pixel_size = 10
    for x in range(0, SCREEN_WIDTH, pixel_size):
        for y in range(0, SCREEN_HEIGHT, pixel_size):
            rect = pygame.Rect(x, y, pixel_size, pixel_size)
            color = screen.get_at((x, y))
            pygame.draw.rect(screen, color, rect)

def apply_invert_colors_effect():
    for x in range(SCREEN_WIDTH):
        for y in range(SCREEN_HEIGHT):
            color = screen.get_at((x, y))
            inverted_color = (255 - color.r, 255 - color.g, 255 - color.b)
            screen.set_at((x, y), inverted_color)

def apply_blocky_effect():
    block_size = 20
    for x in range(0, SCREEN_WIDTH, block_size):
        for y in range(0, SCREEN_HEIGHT, block_size):
            rect = pygame.Rect(x, y, block_size, block_size)
            color = screen.get_at((x, y))
            pygame.draw.rect(screen, color, rect)

def apply_scanline_effect():
    for y in range(0, SCREEN_HEIGHT, 2):
        pygame.draw.line(screen, BLACK, (0, y), (SCREEN_WIDTH, y), 1)

def apply_wave_effect():
    for y in range(0, SCREEN_HEIGHT, 10):
        offset = int(10 * math.sin(pygame.time.get_ticks() / 100 + y / 10))
        pygame.draw.line(screen, WHITE, (0, y + offset), (SCREEN_WIDTH, y + offset), 1)

def apply_random_glitch_effect():
    effects = [
        apply_retro_glitch_effect,
        apply_color_shift_effect,
        apply_pixelate_effect,
        apply_invert_colors_effect,
        apply_blocky_effect,
        apply_scanline_effect,
        apply_wave_effect
    ]
    random.choice(effects)()

# Credits settings
CREDITS_SCREEN = False
CREDITS = [
    "Game developed by: Some Ai dude",
    "Graphics by: Some randoms dudes in the internet",
    "Music by: Idk bro",
    "Special thanks to: chatgpt",
    "Thank you for playing (this horrible game)!",
    "",
    "Thankss for watching this Video! I apriciate it!",
    "Please like and subscribe to my channel!",
    "~ Tamino1230",
    "",
    "",
    "Playtester:",
    "Stuubii (youtube.com/@stuubii)",
    "",
    "",
    "",
    "This game was made in 4 hours with ChatGPT",
    "Hope you enjoyed it!",
    "Byebye have fun now with uhm ykyk"
]

credit_y = SCREEN_HEIGHT

# Main game loop
running = True
clock = pygame.time.Clock()
barrel_timer = 0
score = 0
lives = 3
barrels_spawned = 0

# Font for HUD
font = pygame.font.Font(None, 36)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if not STORY_MODE and not CREDITS_SCREEN:  # Prevent player movement during story mode and credits screen
                if event.key in [pygame.K_a, pygame.K_LEFT]:
                    player.speed_x = -PLAYER_SPEED
                elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                    player.speed_x = PLAYER_SPEED
                elif event.key == pygame.K_SPACE:
                    if player.on_ladder:
                        player.climbing = True  # Start climbing when space is held
                    else:
                        player.jump()
                elif event.key in [pygame.K_w, pygame.K_UP] and player.on_ladder:
                    player.rect.y -= PLAYER_SPEED
                elif event.key in [pygame.K_s, pygame.K_DOWN] and player.on_ladder:
                    player.rect.y += PLAYER_SPEED
            if event.key == pygame.K_RETURN and STORY_MODE:
                current_story_index += 1
                if current_story_index >= len(story_texts):
                    STORY_MODE = False
        elif event.type == pygame.KEYUP:
            if not STORY_MODE and not CREDITS_SCREEN:  # Prevent player movement during story mode and credits screen
                if event.key in [pygame.K_a, pygame.K_d, pygame.K_LEFT, pygame.K_RIGHT]:
                    player.speed_x = 0
                elif event.key == pygame.K_SPACE:
                    player.climbing = False  # Stop climbing when space is released
                elif event.key in [pygame.K_w, pygame.K_s, pygame.K_UP, pygame.K_DOWN]:
                    player.speed_y = 0

    if STORY_MODE:
        screen.fill(WHITE)
        story_text = font.render(story_texts[current_story_index], True, BLACK)
        screen.blit(story_text, (50, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        
        story_timer += 1
        if story_timer > STORY_INTERVAL:
            story_timer = 0
            current_story_index += 1
            if current_story_index >= len(story_texts):
                STORY_MODE = False

    elif CREDITS_SCREEN:
        screen.fill(BLACK)
        for i, line in enumerate(CREDITS):
            credit_text = font.render(line, True, WHITE)
            screen.blit(credit_text, (SCREEN_WIDTH // 2 - credit_text.get_width() // 2, credit_y + i * 40))
        credit_y -= 1
        if credit_y + len(CREDITS) * 40 < 0:
            for _ in range(10):  # Open the link 10 times
                webbrowser.open("https://www.youtube.com/watch?v=xvFZjo5PgG0")
            running = False

        # Update and draw bouncing images
        bouncing_images.update()
        bouncing_images.draw(screen)

        pygame.display.flip()

    else:
        # Update sprites
        all_sprites.update()
        donkey_money.update()

        # Launch barrels periodically
        barrel_timer += 1
        if barrel_timer > 120 and barrels_spawned < BARREL_SPAWN_COUNT:  # Launch a barrel every 2 seconds
            donkey_money.launch_barrel()
            barrel_timer = 0
            barrels_spawned += 1

        # Check for collisions with barrels
        if pygame.sprite.spritecollideany(player, barrels):
            if isinstance(pygame.sprite.spritecollideany(player, barrels), BananaPeel):
                player.slip()
            else:
                lives -= 1
                if lives <= 0:
                    CREDITS_SCREEN = True
                else:
                    player.rect.x = SCREEN_WIDTH // 2
                    player.rect.y = SCREEN_HEIGHT - PLAYER_HEIGHT

        # Check for reaching the goal
        if pygame.sprite.collide_rect(player, goal):
            score += 100
            CREDITS_SCREEN = True

        # Draw everything
        if not STORY_MODE and not CREDITS_SCREEN:  # Only draw the game when story mode and credits screen are not active
            screen.fill(WHITE)
            all_sprites.draw(screen)
            explosions.draw(screen)

            # Draw HUD
            hud = font.render(f'Lives: {lives}  Level: 1', True, BLACK)
            screen.blit(hud, (10, 10))

            # Apply visual glitch effects
            current_time = pygame.time.get_ticks()
            if not RETRO_GLITCH_MODE and random.random() < RETRO_GLITCH_CHANCE:
                RETRO_GLITCH_MODE = True
                last_glitch_time = current_time
            if not BIG_GLITCH_MODE and random.random() < BIG_GLITCH_CHANCE:
                BIG_GLITCH_MODE = True
                big_glitch_start_time = current_time

            if RETRO_GLITCH_MODE:
                apply_random_glitch_effect()
                if current_time - last_glitch_time > GLITCH_INTERVAL:
                    RETRO_GLITCH_MODE = False

            if BIG_GLITCH_MODE:
                apply_color_shift_effect()
                apply_pixelate_effect()
                apply_invert_colors_effect()
                apply_blocky_effect()
                apply_scanline_effect()
                apply_wave_effect()
                if current_time - big_glitch_start_time > BIG_GLITCH_DURATION:
                    BIG_GLITCH_MODE = False

        pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()
