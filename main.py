import pygame
import urllib.request
import csv
import io
import os
import random
import asyncio

SHEET_NAME = "Active_Study" # or Vocab_Repo
base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vShES0s-zu-auumpN03xYynPNi58fcb3fmPoX0Kx0S39Y-1Owgoi8JaGvT9iYBI7NnW0V58hOapNzqQ/pub?output=csv"
url = f"{base_url}&sheet={SHEET_NAME}"
response = urllib.request.urlopen(url)
content  = response.read().decode("utf-8")
reader   = csv.reader(io.StringIO(content))
next(reader)  # skip header row

vocab = []
for row in reader:
    if len(row) >= 4:
        vocab.append({
            "english": row[0],
            "japanese": row[1],
            "romaji":  row[3],
        })

pygame.display.set_caption("Gravity")
os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'  # positions window on screen

pygame.init()

BASE_DIR = os.path.dirname(__file__)
TERMS_PER_LEVEL         = 7
BASE_SPEED              = 30
SPEED_INCREMENT         = 20
MAX_ASTEROIDS_ON_SCREEN = 3
SCREEN_WIDTH  = 736
SCREEN_HEIGHT = 1000
os.environ['SDL_VIDEO_CENTERED'] = '1' # centers window on screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock  = pygame.time.Clock()
font       = pygame.font.Font(os.path.join(BASE_DIR, "NotoSansJP-Regular.ttf"), 18)
small_font = pygame.font.Font(os.path.join(BASE_DIR, "NotoSansJP-Regular.ttf"), 20)  # common on Mac for Japanese font
input_font  = pygame.font.Font(os.path.join(BASE_DIR, "NotoSansJP-Regular.ttf"), 18)

# images
bg_img = pygame.image.load(os.path.join(BASE_DIR, "Images/ppulbatu_background.jpg")).convert()
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

asteroid_imgs = [
    pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, "Images/txt_stars_1.jpg")).convert_alpha(), (200, 200)),
    pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, "Images/txt_stars_2.jpg")).convert_alpha(), (200, 200)),
    pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, "Images/txt_stars_3.jpg")).convert_alpha(), (200, 200)),
]

#asteroid_img = pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, "Images/star_asteroid.jpeg")).convert_alpha(), (80, 80))

icon_img = pygame.image.load(os.path.join(BASE_DIR, "Images/txt_logo_v3.png")).convert_alpha()
icon_img = pygame.transform.scale(icon_img, (180, 90))


# defining the score
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
for card in vocab:
    if mode == "front":
        cards.append({"shown": card["english"], "answer": card["japanese"]})
    elif mode == "back":
        cards.append({"shown": card["japanese"], "answer": card["english"]})
    elif mode == "romaji":
        cards.append({"shown": card["english"], "answer": card["romaji"]})
    elif mode == "random":
        if random.random() < 0.5:
            cards.append({"shown": card["english"], "answer": card["japanese"]})
        else:
            cards.append({"shown": card["japanese"], "answer": card["english"]})

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
        "x":      random.randint(100, SCREEN_WIDTH - 100),
        "y":      -50.0,
        "speed":  BASE_SPEED + SPEED_INCREMENT * (level - 1),
        "red":    red,
        "img":    pygame.transform.rotate(random.choice(asteroid_imgs), random.randint(0, 360)), #random.choice(asteroid_imgs)
    })

# ── Game loop ─────────────────────────────────────────────────────────────────
pygame.key.start_text_input() # helps support Japanese typing
pygame.key.set_text_input_rect(pygame.Rect(0, 740, SCREEN_WIDTH, 40))  # helps support Japanese typing

run = True

async def main_loop():
    global run, state, input_text, level, cleared, spawn_timer, deck  # need globals since they're modified

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

            if not deck and not retry and not asteroids:
                random.shuffle(cards)
                deck = cards.copy()

        # ── Draw ──────────────────────────────────────────────────────────
        screen.blit(bg_img, (0, 0)) # background image add

        for ast in asteroids:
            img_rect = ast["img"].get_rect(center=(int(ast["x"]), int(ast["y"])))
            screen.blit(ast["img"], img_rect)
            t = small_font.render(ast["shown"], True, (0, 0, 0))
            screen.blit(t, (int(ast["x"]) - t.get_width() // 2, int(ast["y"]) - t.get_height() // 2))

        pygame.draw.rect(screen, (30, 30, 60), (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 100)) # for input bar color
        screen.blit(input_font.render(f"Answer: {input_text}|", True, (255, 255, 255)), # for text input bar font
            (20, SCREEN_HEIGHT - 30))
        screen.blit(icon_img, (10, 10))
        score_text = font.render(f"Score: {score.points}", True, (255, 255, 255))
        screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 40,
                         40))

        if state == "dead":
            screen.blit(font.render("GAME OVER", True, (220, 80, 80)), (450, 380))

        pygame.display.update()
        await asyncio.sleep(0)  # this line must be at the end of the loop for pygbag

asyncio.run(main_loop())
pygame.quit()