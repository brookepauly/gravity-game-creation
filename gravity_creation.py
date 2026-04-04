import pygame 
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file
file_url = os.getenv('FILE_URL')

vocab = pd.read_csv(file_url)

pygame.init()

# Initialize variables
TERMS_PER_LEVEL = 7          # asteroids to clear before levelling up
BASE_SPEED = 60              # pixels per second on level 1
SPEED_INCREMENT = 20         # extra px/s per level
MAX_ASTEROIDS_ON_SCREEN = 3  # simultaneous falling asteroids
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
clock = pygame.time.Clock()

# user selects front, back, or random side of cards to be shown on asteroid


font = pygame.font.Font(None, size = 30)

astroid_img = pygame.image.load("astroid.png").convert_alpha
astroid_img = pygame.transform.scale(astroid_img, astroid_img.get_width * 2, astroid_img.get_height * 2)

class Score:
    def __init__(self):
        self.points    = 0
        self.correct   = 0
        self.incorrect = 0

score = Score()

# create meteor class

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

run = True
y = 0
delta_time = .1

# create menu options
mode = None
buttons = [
    {"label": "Front",  "rect": pygame.Rect(400, 250, 200, 50)},
    {"label": "Back",   "rect": pygame.Rect(400, 320, 200, 50)},
    {"label": "Random", "rect": pygame.Rect(400, 390, 200, 50)},
]

# apply menu options through what the user selects
while mode is None:
    screen.fill((10, 10, 30))
    for btn in buttons:
        pygame.draw.rect(screen, (60, 60, 120), btn["rect"])
        t = font.render(btn["label"], True, (255, 255, 255))
        screen.blit(t, (btn["rect"].centerx - t.get_width() // 2,
                        btn["rect"].centery - t.get_height() // 2))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in buttons:
                if btn["rect"].collidepoint(event.pos):
                    mode = btn["label"].lower()  # "front", "back", or "random"
    pygame.display.update()


# main game
clock = pygame.time.Clock()
while run:

    screen.blit(astroid_img, (0, y))
    text = font.render(f'Score: {score.points}')

    y += 50 * delta_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    
    screen.fill((255, 255, 255))
    pygame.display.update()
    pygame.display.flip()

    delta_time = clock.tick(60) / 1000 #fps
    delta_time = max(0.001, min(0.1, delta_time))

pygame.quit()

