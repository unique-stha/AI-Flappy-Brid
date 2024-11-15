import pygame
import neat
import time
import os
import random
import json  # For saving high scores to a file

pygame.font.init()  # Initialize fonts

WIN_WIDTH = 500
WIN_HEIGHT = 800

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)
BUTTON_FONT = pygame.font.SysFont("comicsans", 35)

# File to save high scores
SCORE_FILE = "high_scores.json"

# Function to load high scores from the file
def load_high_scores():
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, 'r') as file:
            return json.load(file)
    return [0, 0, 0, 0, 0]

# Function to save high scores to the file
def save_high_scores(scores):
    with open(SCORE_FILE, 'w') as file:
        json.dump(scores, file)

# Function to update the top 5 scores
def update_high_scores(score):
    high_scores = load_high_scores()
    high_scores.append(score)
    high_scores = sorted(high_scores, reverse=True)[:5]  # Keep only top 5 scores
    save_high_scores(high_scores)
    return high_scores


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2
        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        return False


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, bird, pipes, base, score, game_over, high_scores):
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    bird.draw(win)
    base.draw(win)

    # Display score
    score_label = STAT_FONT.render(f"Score: {score}", 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 20, 10))

    # If game is over, show the game over screen and high scores
    if game_over:
        game_over_label = STAT_FONT.render("Game Over!", 1, (255, 0, 0))
        win.blit(game_over_label, (WIN_WIDTH // 2 - game_over_label.get_width() // 2, 400))

        restart_button = pygame.Rect(WIN_WIDTH // 2 - 70, 500, 140, 50)
        pygame.draw.rect(win, (255, 255, 255), restart_button)
        restart_label = BUTTON_FONT.render("Restart", 1, (0, 0, 0))
        win.blit(restart_label, (WIN_WIDTH // 2 - restart_label.get_width() // 2, 500))

        # Display top 5 high scores
        high_scores_label = STAT_FONT.render("Top 5 Scores", 1, (255, 255, 255))
        win.blit(high_scores_label, (WIN_WIDTH // 2 - high_scores_label.get_width() // 2, 100))

        for i, hs in enumerate(high_scores):
            score_text = STAT_FONT.render(f"{i + 1}. {hs}", 1, (255, 255, 255))
            win.blit(score_text, (WIN_WIDTH // 2 - score_text.get_width() // 2, 150 + i * 40))

    pygame.display.update()


def main():
    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    game_over = False
    high_scores = load_high_scores()

    run = True
    while run:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                bird.jump()

            # Handle restart if game over and button clicked
            if game_over and event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if WIN_WIDTH // 2 - 70 <= mouse_pos[0] <= WIN_WIDTH // 2 + 70 and 400 <= mouse_pos[1] <= 550:
                    main()  # Restart the game

        if not game_over:
            # Move bird
            bird.move()

            # Move pipes and check for collisions
            add_pipe = False
            rem = []
            for pipe in pipes:
                if pipe.collide(bird):
                    game_over = True
                    high_scores = update_high_scores(score)  # Update top scores

                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem.append(pipe)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
                    score += 1

                pipe.move()

            if bird.y + bird.img.get_height() >= 730:  # Bird hits the base
                game_over = True
                high_scores = update_high_scores(score)  # Update top scores

            for r in rem:
                pipes.remove(r)

            if add_pipe:
                pipes.append(Pipe(600))

            base.move()

        draw_window(win, bird, pipes, base, score, game_over, high_scores)

    pygame.quit()


if __name__ == "__main__":
    main()
