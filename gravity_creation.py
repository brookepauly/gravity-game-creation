import pygame
import pandas as pd
from dotenv import load_dotenv
import os
import random

load_dotenv()
file_url = os.getenv('FILE_URL')
vocab = pd.read_csv(file_url)

pygame.display.set_caption("Gravity")
os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'  # positions window on screen

pygame.init()

TERMS_PER_LEVEL         = 7
BASE_SPEED              = 30
SPEED_INCREMENT         = 20
MAX_ASTEROIDS_ON_SCREEN = 3
SCREEN_WIDTH  = 1100
SCREEN_HEIGHT = 700
os.environ['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock  = pygame.time.Clock()
font       = pygame.font.SysFont("hiragino sans gb", 30)
small_font = pygame.font.SysFont("hiragino sans gb", 12)  # common on Mac for Japanese font

astroid_img = pygame.image.load("/Users/brookepauly/Downloads/gravity-creation/Images/asteroid.png").convert_alpha()
astroid_img = pygame.transform.scale(astroid_img, (120, 180))

class Score:
    def __init__(self):
        self.points    = 0
        self.correct   = 0
        self.incorrect = 0

score = Score()

# ── Menu ──────────────────────────────────────────────────────────────────────

mode    = None
buttons = [
    {"label": "Front",  "rect": pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 115, 200, 50)},
    {"label": "Back",   "rect": pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 55,  200, 50)},
    {"label": "Romaji", "rect": pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 5,   200, 50)},
    {"label": "Random", "rect": pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 65,  200, 50)},
]

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
                    mode = btn["label"].lower()
    pygame.display.update()

# ── Build card deck based on mode ─────────────────────────────────────────────

cards = []
for _, row in vocab.iterrows():
    if mode == "front":
        cards.append({"shown": str(row.iloc[0]), "answer": str(row.iloc[1])})
    elif mode == "back":
        cards.append({"shown": str(row.iloc[1]), "answer": str(row.iloc[0])})
    elif mode == "romaji":
        cards.append({"shown": str(row.iloc[0]), "answer": str(row.iloc[2])})  # show english, type romaji
    elif mode == "random": # random between japanese and english (no romaji)
        if random.random() < 0.5:
            cards.append({"shown": str(row.iloc[0]), "answer": str(row.iloc[1])})
        else:
            cards.append({"shown": str(row.iloc[1]), "answer": str(row.iloc[0])})

random.shuffle(cards)

# ── Game state ────────────────────────────────────────────────────────────────

deck        = cards.copy()
retry       = []
asteroids   = []
input_text  = ""
level       = 1
cleared     = 0
spawn_timer = 0
state       = "playing"

def spawn():
    if len(asteroids) >= MAX_ASTEROIDS_ON_SCREEN or (not deck and not retry):
        return
    if retry and (not deck or random.random() < 0.4):
        card = retry.pop(0)
        red  = True
    else:
        card = deck.pop(0)
        red  = False
    asteroids.append({ # asteroid logic
        "shown":  card["shown"],
        "answer": card["answer"],
        "x":      random.randint(100, 900),
        "y":      -50.0,
        "speed":  BASE_SPEED + SPEED_INCREMENT * (level - 1),
        "red":    red,
    })

# ── Game loop ─────────────────────────────────────────────────────────────────
pygame.key.start_text_input()
pygame.key.set_text_input_rect(pygame.Rect(0, 740, SCREEN_WIDTH, 60))  # helps support Japanese typing

run = True
while run:
    delta_time = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.TEXTINPUT and state == "playing": 
            input_text += event.text
        if event.type == pygame.KEYDOWN and state == "playing":
            if event.key == pygame.K_RETURN:
                guess = input_text.strip().lower()
                input_text = ""
                if guess and asteroids:
                    target = max(asteroids, key=lambda a: a["y"])
                    if guess == target["answer"].strip().lower():
                        score.points  += 10 * level
                        score.correct += 1
                        asteroids.remove(target)
                        cleared += 1
                        if cleared >= TERMS_PER_LEVEL:
                            level  += 1
                            cleared = 0
                    else:
                        score.incorrect += 1
                        if target["red"]:
                            state = "dead"
                        else:
                            retry.append({"shown": target["shown"], "answer": target["answer"]})
                            asteroids.remove(target)
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]

    if state == "playing":
        spawn_timer += delta_time
        if spawn_timer >= 2.0:
            spawn_timer = 0
            spawn()

        for ast in asteroids[:]:
            ast["y"] += ast["speed"] * delta_time
            if ast["y"] > SCREEN_HEIGHT - 80:
                if ast["red"]:
                    state = "dead"
                else:
                    retry.append({"shown": ast["shown"], "answer": ast["answer"]})
                asteroids.remove(ast)

        #if not deck and not retry and not asteroids:
        #    state = ""

    # ── Draw ──────────────────────────────────────────────────────────────────

    screen.fill((255, 182, 193))

    for ast in asteroids:
        img_rect = astroid_img.get_rect(center = (int(ast["x"]), int(ast["y"])))
        screen.blit(astroid_img, img_rect)
        t = small_font.render(ast["shown"], True, (0, 0, 0))
        screen.blit(t, (int(ast["x"]) - t.get_width() // 2, int(ast["y"]) - t.get_height() // 2 + 28))

    pygame.draw.rect(screen, (30, 30, 60), (0, 640, SCREEN_WIDTH, 60))
    screen.blit(font.render(f"Answer: {input_text}|", True, (255, 255, 255)), (20, 655)) # input text 
    screen.blit(font.render(f"Score: {score.points}  Level: {level}", True, (255, 255, 255)), (10, 10)) # score rendering

    if state == "dead":
        screen.blit(font.render("GAME OVER", True, (220, 80, 80)), (450, 380))
    if state == "win":
        screen.blit(font.render(f"YOU WIN!  Score: {score.points}", True, (80, 220, 120)), (400, 380)) # Shouldn't have win state

    pygame.display.update()

pygame.quit()