import json
import math
import random
from array import array
from collections import deque

import pygame

CELL = 30
COLS, ROWS = 24, 20
PAD = 28
TOP = 152
BOTTOM = 74
BOARD_X, BOARD_Y = PAD, TOP
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
WIDTH, HEIGHT = BOARD_W + PAD * 2, TOP + BOARD_H + BOTTOM
SPEEDS = [6, 10, 15, 25, 40, 60]
START_SPEED = 1
SAVE_FILE = "best_scores.json"

BG_TOP = (16, 22, 40)
BG_BOTTOM = (6, 8, 16)
PANEL = (13, 18, 30)
CELL_A = (17, 23, 37)
CELL_B = (15, 20, 33)
BORDER = (40, 52, 80)
CARD = (20, 27, 44)
SNAKE_HEAD_END = (74, 222, 128)
SNAKE_TAIL_END = (20, 120, 110)
HEAD = (245, 197, 24)
APPLE = (239, 68, 68)
TEXT = (236, 241, 248)
MUTED = (128, 140, 165)
YELLOW = (245, 197, 24)
GREEN = (74, 222, 128)
ORANGE = (245, 158, 11)

PLAN_NOTES = {
    "safe": ("planning: safe", GREEN),
    "tail": ("playing it safe: following tail", ORANGE),
    "risk": ("taking a risk: going for the apple", APPLE),
}

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)
KEYS = {
    pygame.K_UP: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_RIGHT: RIGHT,
}


def load_best():
    try:
        with open(SAVE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_best(best):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(best, f, indent=2)
    except OSError:
        pass


# a game played in more than one mode doesn't count towards any best score
def record_best(game, best):
    if len(game.modes) != 1:
        return
    key = next(iter(game.modes))
    if game.score > best.get(key, 0):
        best[key] = game.score
        save_best(best)


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        mid = (COLS // 2, ROWS // 2)
        self.snake = [mid, (mid[0] - 1, mid[1]), (mid[0] - 2, mid[1])]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.score = 0
        self.alive = True
        self.plan = []
        self.plan_note = "safe"
        self.waiting = 0
        self.modes = set()
        self.place_apple()

    def place_apple(self):
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in self.snake]
        self.apple = random.choice(free) if free else None

    def turn(self, new_direction):
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.next_direction = new_direction

    def step(self):
        if not self.alive:
            return
        self.direction = self.next_direction
        hx, hy = self.snake[0]
        new_head = (hx + self.direction[0], hy + self.direction[1])

        eating = new_head == self.apple
        body = self.snake if eating else self.snake[:-1]   # the tail moves away this turn
        out_of_board = not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS)
        if out_of_board or new_head in body:
            self.alive = False
            return

        self.snake.insert(0, new_head)
        self.waiting += 1
        if eating:
            self.score += 1
            self.waiting = 0
            self.place_apple()
            if self.apple is None:
                self.alive = False
        else:
            self.snake.pop()


def level1_move(game):
    hx, hy = game.snake[0]
    ax, ay = game.apple
    options = []
    for d in (UP, DOWN, LEFT, RIGHT):
        if (d[0] * -1, d[1] * -1) == game.direction:
            continue
        nx, ny = hx + d[0], hy + d[1]
        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            continue
        distance = abs(ax - nx) + abs(ay - ny)
        options.append((distance, d != game.direction, d))
    if not options:
        return game.direction
    options.sort()
    return options[0][2]


def neighbours(cell):
    x, y = cell
    for d in (UP, DOWN, LEFT, RIGHT):
        nx, ny = x + d[0], y + d[1]
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            yield (nx, ny), d


def find_path(start, goal, blocked):
    came_from = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            path = []
            while cell != start:
                path.append(cell)
                cell = came_from[cell]
            return path[::-1]
        for nxt, _ in neighbours(cell):
            if nxt not in came_from and nxt not in blocked:
                came_from[nxt] = cell
                queue.append(nxt)
    return None


def safe_moves(game):
    head = game.snake[0]
    body = set(game.snake[:-1])
    moves = []
    for nxt, d in neighbours(head):
        if nxt not in body and (d[0] * -1, d[1] * -1) != game.direction:
            moves.append(d)
    return moves


def level2_move(game):
    head = game.snake[0]
    blocked = set(game.snake[:-1])
    path = find_path(head, game.apple, blocked)
    game.plan = path or []
    if path:
        nx, ny = path[0]
        return (nx - head[0], ny - head[1])
    moves = safe_moves(game)
    return moves[0] if moves else game.direction


# the tail keeps moving away, so reaching it means you aren't boxed in
def can_reach_tail(snake):
    if len(snake) < 3:
        return True
    return find_path(snake[0], snake[-1], set(snake[1:-1])) is not None


def level3_move(game):
    head = game.snake[0]
    length = len(game.snake)
    path = find_path(head, game.apple, set(game.snake[:-1]))
    if path:
        future = (path[::-1] + game.snake)[:length + 1]
        safe = can_reach_tail(future)
        # after circling too long, go for the apple anyway
        if safe or game.waiting > COLS * ROWS * 2:
            game.plan = path
            game.plan_note = "safe" if safe else "risk"
            nx, ny = path[0]
            return (nx - head[0], ny - head[1])

    # not safe: follow the tail the long way round until a safe path opens up
    best, best_len = None, -1
    for d in safe_moves(game):
        nxt = (head[0] + d[0], head[1] + d[1])
        future = [nxt] + (game.snake if nxt == game.apple else game.snake[:-1])
        to_tail = find_path(future[0], future[-1], set(future[1:-1])) if len(future) >= 3 else [future[-1]]
        if to_tail is not None and len(to_tail) > best_len:
            best, best_len = d, len(to_tail)
    tail_path = find_path(head, game.snake[-1], set(game.snake[1:-1]))
    game.plan = tail_path or []
    game.plan_note = "tail"
    if best:
        return best
    moves = safe_moves(game)
    return moves[0] if moves else game.direction


LEVELS = {1: level1_move, 2: level2_move, 3: level3_move}
LEVEL_NAMES = {1: "LEVEL 1", 2: "LEVEL 2", 3: "LEVEL 3"}


class Sounds:
    def __init__(self):
        self.on = True
        self.ready = False
        try:
            pygame.mixer.init(44100, -16, 2, 512)
            self.rate, _, self.channels = pygame.mixer.get_init()
            self.eat = self.make([(660, 0.05), (990, 0.07)], volume=0.35)
            self.lose = self.make([(440, 0.12), (330, 0.12), (220, 0.28)], volume=0.4, wave="square")
            self.win = self.make([(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.35)], volume=0.4)
            self.click = self.make([(1200, 0.03)], volume=0.2)
            self.ready = True
        except pygame.error:
            pass  # no sound device, so play silently

    def make(self, notes, volume=0.4, wave="sine"):
        samples = array("h")
        for freq, length in notes:
            count = int(self.rate * length)
            for i in range(count):
                fade = min(1.0, i / (self.rate * 0.005), (count - i) / (self.rate * 0.02))
                x = math.sin(2 * math.pi * freq * i / self.rate)
                if wave == "square":
                    x = 0.6 if x > 0 else -0.6
                value = int(32767 * volume * fade * x)
                for _ in range(self.channels):
                    samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if self.on and self.ready:
            getattr(self, name).play()


def make_background():
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        k = y / HEIGHT
        c = [int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * k) for i in range(3)]
        pygame.draw.line(bg, c, (0, y), (WIDTH, y))
    shadow = pygame.Surface((BOARD_W + 40, BOARD_H + 40), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 120), shadow.get_rect(), border_radius=26)
    bg.blit(shadow, (BOARD_X - 20, BOARD_Y - 8))
    pygame.draw.rect(bg, PANEL, (BOARD_X - 6, BOARD_Y - 6, BOARD_W + 12, BOARD_H + 12), border_radius=18)
    for x in range(COLS):
        for y in range(ROWS):
            pygame.draw.rect(bg, CELL_A if (x + y) % 2 else CELL_B, (BOARD_X + x * CELL, BOARD_Y + y * CELL, CELL, CELL))
    pygame.draw.rect(bg, BORDER, (BOARD_X - 6, BOARD_Y - 6, BOARD_W + 12, BOARD_H + 12), width=2, border_radius=18)
    return bg


def cell_center(cell):
    x, y = cell
    return (BOARD_X + x * CELL + CELL // 2, BOARD_Y + y * CELL + CELL // 2)


def blend(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def draw_card(screen, rect, label, value, fonts, colour=TEXT, pop=0.0):
    pygame.draw.rect(screen, CARD, rect, border_radius=14)
    pygame.draw.rect(screen, BORDER, rect, width=1, border_radius=14)
    screen.blit(fonts["label"].render(label, True, MUTED), (rect.x + 16, rect.y + 10))
    text = fonts["value"].render(str(value), True, colour)
    if pop > 0:
        size = 1 + 0.25 * pop
        text = pygame.transform.smoothscale(text, (int(text.get_width() * size), int(text.get_height() * size)))
    screen.blit(text, (rect.x + 16, rect.y + 30 - (text.get_height() - fonts["value"].get_height()) // 2))


def draw_keycap(screen, x, y, key, label, fonts):
    cap = fonts["key"].render(key, True, TEXT)
    w = max(30, cap.get_width() + 16)
    pygame.draw.rect(screen, (30, 40, 62), (x, y + 3, w, 30), border_radius=7)
    pygame.draw.rect(screen, (44, 57, 88), (x, y, w, 30), border_radius=7)
    screen.blit(cap, (x + (w - cap.get_width()) // 2, y + 15 - cap.get_height() // 2))
    text = fonts["small"].render(label, True, MUTED)
    screen.blit(text, (x + w + 7, y + 15 - text.get_height() // 2))
    return x + w + 7 + text.get_width() + 15


def draw(screen, fonts, bg, game, autopilot, level, speed_i, best, paused, fx):
    t = pygame.time.get_ticks() / 1000
    screen.blit(bg, (0, 0))

    screen.blit(fonts["title"].render("SNAKE", True, TEXT), (PAD, 16))
    screen.blit(fonts["small"].render("Day 16 · 100 Python Projects", True, MUTED), (PAD + 2, 64))
    mode_key = f"level{level}" if autopilot else "you"
    cx = WIDTH - PAD - 380
    draw_card(screen, pygame.Rect(cx, 20, 130, 74), "SCORE", game.score, fonts, YELLOW, fx["pop"])
    draw_card(screen, pygame.Rect(cx + 140, 20, 130, 74), "BEST", best.get(mode_key, 0), fonts)
    draw_card(screen, pygame.Rect(cx + 280, 20, 100, 74), "SPEED", SPEEDS[speed_i], fonts)

    label = f"AUTOPILOT · LEVEL {level}" if autopilot else "YOU"
    colour = YELLOW if autopilot else GREEN
    tag = fonts["pill"].render(label, True, (10, 14, 24))
    pill = pygame.Rect(0, 0, tag.get_width() + 30, 34)
    pill.topleft = (PAD, 106)
    glow = pygame.Surface((pill.w + 24, pill.h + 24), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*colour, 35), glow.get_rect(), border_radius=26)
    screen.blit(glow, (pill.x - 12, pill.y - 12))
    pygame.draw.rect(screen, colour, pill, border_radius=17)
    screen.blit(tag, (pill.x + 15, pill.y + 17 - tag.get_height() // 2))
    if autopilot and level >= 2:
        note, dot = PLAN_NOTES[game.plan_note]
        n = fonts["small"].render(note, True, dot)
        pygame.draw.circle(screen, dot, (pill.right + 22, pill.centery), 5)
        screen.blit(n, (pill.right + 34, pill.centery - n.get_height() // 2))

    if autopilot and game.plan and game.alive:
        line = (120, 140, 180) if game.plan_note == "safe" else PLAN_NOTES[game.plan_note][1]
        pts = [cell_center(c) for c in [game.snake[0]] + game.plan]
        if len(pts) > 1:
            pygame.draw.lines(screen, line, False, pts, 3)
        for p in pts[1::2]:
            pygame.draw.circle(screen, line, p, 3)

    if game.apple:
        ax, ay = cell_center(game.apple)
        r = CELL // 2 - 4 + 1.5 * (1 + pygame.math.Vector2(1, 0).rotate(t * 360).x) / 2
        halo = pygame.Surface((CELL * 2, CELL * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo, (239, 68, 68, 55), (CELL, CELL), int(r + 8))
        screen.blit(halo, (ax - CELL, ay - CELL))
        pygame.draw.circle(screen, APPLE, (ax, ay + 1), int(r))
        pygame.draw.circle(screen, (255, 160, 160), (ax - 4, ay - 4), 3)
        pygame.draw.ellipse(screen, GREEN, (ax + 1, ay - r - 5, 9, 6))

    n = len(game.snake)
    width = CELL - 6
    for i in range(n - 1, -1, -1):
        k = i / max(1, n - 1)
        colour = blend(SNAKE_HEAD_END, SNAKE_TAIL_END, k)
        cx_, cy_ = cell_center(game.snake[i])
        if i < n - 1:
            nx_, ny_ = cell_center(game.snake[i + 1])
            if cy_ == ny_:
                rect = pygame.Rect(min(cx_, nx_), cy_ - width // 2, abs(cx_ - nx_), width)
            else:
                rect = pygame.Rect(cx_ - width // 2, min(cy_, ny_), width, abs(cy_ - ny_))
            pygame.draw.rect(screen, colour, rect)
        pygame.draw.circle(screen, colour, (cx_, cy_), width // 2)

    hx, hy = cell_center(game.snake[0])
    glow = pygame.Surface((CELL * 3, CELL * 3), pygame.SRCALPHA)
    pygame.draw.circle(glow, (245, 197, 24, 50), (CELL * 3 // 2, CELL * 3 // 2), CELL)
    screen.blit(glow, (hx - CELL * 3 // 2, hy - CELL * 3 // 2))
    pygame.draw.circle(screen, HEAD, (hx, hy), CELL // 2 - 1)
    dx, dy = game.direction
    for side in (-1, 1):
        ex = hx + dx * 4 + (-dy) * side * 6
        ey = hy + dy * 4 + dx * side * 6
        pygame.draw.circle(screen, (255, 255, 255), (ex, ey), 4)
        pygame.draw.circle(screen, (10, 14, 24), (ex + dx * 1.5, ey + dy * 1.5), 2)

    for p in fx["particles"]:
        a = max(0, p["life"] / p["max"])
        pygame.draw.circle(screen, blend((255, 120, 120), YELLOW, 1 - a), (int(p["x"]), int(p["y"])), max(1, int(4 * a)))

    # shrunk to fit if the font is wide on this computer
    strip = pygame.Surface((WIDTH * 2, 40), pygame.SRCALPHA)
    x = 0
    for key, label in (("Arrows", "move"), ("A", "autopilot"), ("1 2 3", "level"), ("+ -", "speed"), ("Space", "pause"), ("R", "restart"), ("M", "sound")):
        x = draw_keycap(strip, x, 2, key, label, fonts)
    used = x - 15
    room = WIDTH - PAD * 2
    if used > room:
        strip = pygame.transform.smoothscale(strip, (int(strip.get_width() * room / used), int(40 * room / used)))
        used = room
    screen.blit(strip, ((WIDTH - used) // 2, TOP + BOARD_H + 24 + (40 - strip.get_height()) // 2))

    if not game.alive or paused:
        shade = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        shade.fill((5, 8, 16, 170))
        screen.blit(shade, (BOARD_X, BOARD_Y))
        if paused and game.alive:
            title, sub, col = "PAUSED", "Press Space to keep going", TEXT
        elif game.apple is None:
            title, sub, col = "BOARD FILLED!", "Press R to play again", YELLOW
        else:
            title, sub, col = "GAME OVER", f"Score {game.score}  ·  Press R to play again", TEXT
        card = pygame.Rect(0, 0, 420, 150)
        card.center = (BOARD_X + BOARD_W // 2, BOARD_Y + BOARD_H // 2)
        pygame.draw.rect(screen, CARD, card, border_radius=20)
        pygame.draw.rect(screen, BORDER, card, width=2, border_radius=20)
        tt = fonts["big"].render(title, True, col)
        ss = fonts["small"].render(sub, True, MUTED)
        screen.blit(tt, (card.centerx - tt.get_width() // 2, card.y + 30))
        screen.blit(ss, (card.centerx - ss.get_width() // 2, card.y + 100))

    pygame.display.flip()


def update_fx(fx, dt):
    fx["pop"] = max(0.0, fx["pop"] - dt * 4)
    for p in fx["particles"]:
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["vy"] += 300 * dt
        p["life"] -= dt
    fx["particles"] = [p for p in fx["particles"] if p["life"] > 0]


def burst(fx, cell):
    x, y = cell_center(cell)
    for _ in range(14):
        v = pygame.math.Vector2(random.uniform(80, 220), 0).rotate(random.uniform(0, 360))
        fx["particles"].append({"x": x, "y": y, "vx": v.x, "vy": v.y, "life": 0.5, "max": 0.5})
    fx["pop"] = 1.0


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snake (Day 16)")
    face = "avenirnext,helveticaneue,segoeui,arial"
    fonts = {
        "title": pygame.font.SysFont(face, 44, bold=True),
        "big": pygame.font.SysFont(face, 46, bold=True),
        "value": pygame.font.SysFont(face, 30, bold=True),
        "pill": pygame.font.SysFont(face, 18, bold=True),
        "label": pygame.font.SysFont(face, 13, bold=True),
        "key": pygame.font.SysFont(face, 14, bold=True),
        "small": pygame.font.SysFont(face, 15),
    }
    bg = make_background()
    fx = {"pop": 0.0, "particles": []}
    sounds = Sounds()
    clock = pygame.time.Clock()

    game = Game()
    best = load_best()
    autopilot = False
    level = 1
    paused = False
    speed_i = START_SPEED
    move_timer = 0.0

    running = True
    while running:
        dt = clock.tick(120) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    record_best(game, best)
                    game.reset()
                    paused = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_m:
                    sounds.on = not sounds.on
                elif event.key == pygame.K_a:
                    sounds.play("click")
                    autopilot = not autopilot
                    game.plan = []
                elif event.key in (pygame.K_1, pygame.K_KP1) or event.unicode == "1":
                    level, autopilot = 1, True
                    game.plan = []
                elif event.key in (pygame.K_2, pygame.K_KP2) or event.unicode == "2":
                    level, autopilot = 2, True
                    game.plan = []
                elif event.key in (pygame.K_3, pygame.K_KP3) or event.unicode == "3":
                    level, autopilot = 3, True
                    game.plan = []
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed_i = min(len(SPEEDS) - 1, speed_i + 1)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_i = max(0, speed_i - 1)
                elif event.key in KEYS and not autopilot:
                    game.turn(KEYS[event.key])

        if game.alive and not paused:
            move_timer += dt
            interval = 1 / SPEEDS[speed_i]
            if move_timer >= interval:
                move_timer = min(move_timer - interval, interval)
                old_score, apple = game.score, game.apple
                game.modes.add(f"level{level}" if autopilot else "you")
                if autopilot and game.apple:
                    game.turn(LEVELS[level](game))
                    if level == 1:
                        game.plan = []
                    if level == 2:
                        game.plan_note = "safe"
                game.step()
                if game.score > old_score:
                    burst(fx, apple)
                    if game.alive:
                        sounds.play("eat")
                if not game.alive:
                    sounds.play("win" if game.apple is None else "lose")
                if autopilot and level >= 2 and game.alive and game.apple:
                    LEVELS[level](game)  # keeps the drawn path up to date
                if not game.alive:
                    record_best(game, best)

        update_fx(fx, dt)
        draw(screen, fonts, bg, game, autopilot, level, speed_i, best, paused, fx)

    record_best(game, best)
    pygame.quit()


if __name__ == "__main__":
    main()
