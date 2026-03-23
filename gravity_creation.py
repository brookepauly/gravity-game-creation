import pygame 
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file
file_url = os.getenv('FILE_URL')

vocab = pd.read_csv(file_url)

pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

score_info = pd.DataFrame({
    'Points': [],
    'Correct': [],
    'Incorrect': []
})

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    screen.fill((255, 255, 255))

pygame.quit()

