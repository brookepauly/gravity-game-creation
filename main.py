import pygame
import urllib.request
import csv
import os
import io
import random

SHEET_NAME = "Vocab_Repo" # or Vocab_Repo
base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBYNEU5xj3BnWzR8fJQe8qHkAnxsBeptyJgbPFBP4LdDOdaZCkWCrTi0kDTAav42ksbAlp7HvwAVKc/pub?output=csv"
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
            "hiragana":  row[2],
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
font       = pygame.font.Font(os.path.join(BASE_DIR, "Fonts/NotoSansJP-Regular.ttf"), 22)
small_font = pygame.font.Font(os.path.join(BASE_DIR, "Fonts/NotoSansJP-Regular.ttf"), 20)  # common on Mac for Japanese font
input_font  = pygame.font.Font(os.path.join(BASE_DIR, "Fonts/NotoSansJP-Regular.ttf"), 18)
feedback_font = pygame.font.Font(os.path.join(BASE_DIR, "Fonts/NotoSansJP-Regular.ttf"), 16)  # adjust size/style
end_font = pygame.font.Font(os.path.join(BASE_DIR, "Fonts/Bytesized-Regular.ttf"), 80)

# images
bg_img = pygame.image.load(os.path.join(BASE_DIR, "Images/ppulbatu_background.jpg")).convert()
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

asteroid_imgs = [
    pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, "Images/txt_stars_1.jpg")).convert_alpha(), (250, 250)),
    pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, "Images/txt_stars_2.jpg")).convert_alpha(), (250, 250)),
    pygame.transform.scale(pygame.image.load(os.path.join(BASE_DIR, "Images/txt_stars_3.jpg")).convert_alpha(), (250, 250)),
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
    {"label": "Hiragana", "rect": pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 5,   200, 50)},
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
    elif mode == "hiragana":
        cards.append({"shown": card["english"], "answer": card["hiragana"]})
    elif mode == "random":
        if random.random() < 0.5:
            cards.append({"shown": card["english"], "answer": card["hiragana"]})
        else:
            cards.append({"shown": card["hiragana"], "answer": card["english"]})

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
feedback    = ""   
feedback_timer = 0.0   

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
        "img":    pygame.transform.rotate(random.choice(asteroid_imgs), random.randint(0, 260)),
    })

# ── Game loop ─────────────────────────────────────────────────────────────────
pygame.key.start_text_input() # helps support Japanese typing
input_box = pygame.Rect(0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 100)
pygame.key.set_text_input_rect((input_box))  # 0, 740, SCREEN_WIDTH, 40

death_timer = None
run = True
active = False

while run:
    delta_time = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.TEXTINPUT and state == "playing" and active:
            input_text += event.text
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_box.collidepoint(event.pos):
                active = True   # Clicked inside → focus
            else:
                active = False  # Clicked outside → unfocus
        if event.type == pygame.KEYDOWN and state == "playing" and active:
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
                        feedback       = f"{target['shown']} {target['answer']}"
                        feedback_timer = 1.0
                        if target["red"]:
                            state = "dead"
                            death_timer = pygame.time.get_ticks()  # start the clock
                        else:
                            retry.append({"shown": target["shown"], "answer": target["answer"]})
                            asteroids.remove(target)
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]

    if state == "playing":
        spawn_timer += delta_time
        if feedback_timer > 0:
            feedback_timer -= delta_time
            if feedback_timer <= 0:
                feedback = ""
        if spawn_timer >= 2.0:
            spawn_timer = 0
            spawn()

        for ast in asteroids[:]:
            ast["y"] += ast["speed"] * delta_time
            if ast["y"] > SCREEN_HEIGHT - 80:
                if ast["red"]:
                    state = "dead"
                    death_timer = pygame.time.get_ticks()  # start the clock
                else:
                    retry.append({"shown": ast["shown"], "answer": ast["answer"]})
                asteroids.remove(ast)

        if not deck and not retry and not asteroids:
            random.shuffle(cards)
            deck = cards.copy()

        # --- DEAD STATE TIMER ---
    if state == "dead" and death_timer is not None:
        if pygame.time.get_ticks() - death_timer >= 2000:  # 2 seconds
            run = False   # exit main loop

    # ── Draw ──────────────────────────────────────────────────────────
    screen.blit(bg_img, (0, 0)) # background image add

    for ast in asteroids:
        color = (224, 33, 138) if ast['red'] else (0, 0, 0)
        img_rect = ast["img"].get_rect(center=(int(ast["x"]), int(ast["y"])))
        screen.blit(ast["img"], img_rect)
        t = small_font.render(ast["shown"], True, color)
        screen.blit(t, (int(ast["x"]) - t.get_width() // 2, int(ast["y"]) - t.get_height() // 2))

    pygame.draw.rect(screen, (30, 30, 60), (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 100)) # for input bar color
    screen.blit(input_font.render(f"Answer: {input_text}|", True, (255, 255, 255)), # for text input bar font
        (20, SCREEN_HEIGHT - 30))
    screen.blit(icon_img, (10, 10))
    score_text = font.render(f"Score: {score.points}", True, (255, 255, 255))
    screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 40,
                        40))
    if feedback:
        fb_surf = feedback_font.render(feedback, True, (179,235,242)) # light yellow: 255,255,197, light pink: 255, 192, 203, pastel blue: 179,235,242, other blue: 196,216,226
        screen.blit(fb_surf, (30, 40 + icon_img.get_height() - 9))

    if state == "dead":
        dead_surf = end_font.render("GAME OVER", True, (179,235,242))
        screen.blit(dead_surf, (SCREEN_WIDTH // 2 - dead_surf.get_width() // 2, SCREEN_HEIGHT // 2))

    pygame.display.update()

