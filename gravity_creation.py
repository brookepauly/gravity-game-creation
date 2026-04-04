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

font = pygame.font.Font(None, size = 30)

astroid_img = pygame.image.load("astroid.png").convert_alpha
background_img = pygame.image.load("background.png")

astroid_img = pygame.transform.scale(astroid_img, astroid_img.get_width * 2, astroid_img.get_height * 2)

score_info = pd.DataFrame({
    'Points': [],
    'Correct': [],
    'Incorrect': [],
}) # Weight by mode of incorrect cards for displaying an incorrect answer 

# create meteor class

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

run = True
y = 0
delta_time = .1

clock = pygame.time.Clock()
while run:

    screen.blit(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

    screen.blit(astroid_img, (0, y))

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

