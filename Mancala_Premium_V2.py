
import math
import random
import sys
import pygame

# ============================================================
# MANCALA CLASSIC - PREMIUM EDITION
# ============================================================

pygame.init()
pygame.display.set_caption("MANCALA CLASSIC | Premium Edition")

info = pygame.display.Info()
SW = info.current_w or 1366
SH = info.current_h or 768

W = min(1500, max(1000, int(SW * 0.92)))
H = min(900, max(660, int(SH * 0.88)))

screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
clock = pygame.time.Clock()
FPS = 60

BG1 = (57, 25, 19)
BG2 = (22, 10, 9)
WOOD = (151, 101, 62)
WOOD_LIGHT = (202, 153, 105)
GOLD = (226, 190, 130)
CREAM = (250, 239, 219)
MUTED = (190, 164, 139)
GREEN = (119, 194, 151)


def font(size, bold=False, serif=False):
    name = "georgia" if serif else "arial"
    return pygame.font.SysFont(name, max(12, int(size)), bold=bold)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def ease(t):
    t = clamp(t, 0, 1)
    return 1 - (1 - t) ** 3


def text(dst, value, f, color, center, shadow=False):
    img = f.render(str(value), True, color)
    rect = img.get_rect(
        center=(int(center[0]), int(center[1]))
    )

    if shadow:
        shade = f.render(str(value), True, (12, 5, 4))
        dst.blit(shade, rect.move(2, 3))

    dst.blit(img, rect)
    return rect


def rounded(dst, rect, fill, radius=14,
            border=None, width=1):
    pygame.draw.rect(
        dst, fill, rect, border_radius=radius
    )

    if border:
        pygame.draw.rect(
            dst, border, rect, width,
            border_radius=radius
        )


def gradient(dst, top, bottom):
    for y in range(H):
        t = y / max(1, H - 1)

        c = tuple(
            int(top[i] + (bottom[i] - top[i]) * t)
            for i in range(3)
        )

        pygame.draw.line(dst, c, (0, y), (W, y))


def background():
    gradient(screen, BG1, BG2)

    glow = pygame.Surface((W, H), pygame.SRCALPHA)

    pygame.draw.ellipse(
        glow,
        (180, 91, 48, 22),
        (W*.18, H*.18, W*.64, H*.68)
    )

    screen.blit(glow, (0, 0))


def wood_texture(size, seed=9):
    w, h = size

    s = pygame.Surface((w, h)).convert()
    s.fill(WOOD)

    rng = random.Random(seed)

    for _ in range(max(12, h // 15)):
        y = rng.randrange(max(1, h))

        shade = rng.choice(
            [-18, -12, -7, 7, 12, 17]
        )

        col = tuple(
            clamp(c + shade, 0, 255)
            for c in WOOD
        )

        phase = rng.random() * 6.28
        amp = rng.uniform(1, 3)
        wave = rng.uniform(220, 500)

        pts = []

        for x in range(0, w + 8, 8):
            pts.append((
                x,
                int(y + math.sin(x / wave + phase) * amp)
            ))

        if len(pts) > 1:
            pygame.draw.lines(
                s, col, False, pts,
                rng.choice([1, 2])
            )

    pygame.draw.line(
        s, (194, 147, 99),
        (0, 4), (w, 4), 2
    )

    return s


def draw_seed(dst, x, y, radius, kind=0):

    palettes = [
        ((95, 12, 27), (184, 39, 57), (255, 160, 164)),
        ((139, 119, 109), (218, 198, 181), (255, 246, 231)),
        ((25, 23, 22), (76, 69, 62), (179, 167, 151)),
        ((119, 69, 29), (198, 137, 63), (255, 219, 151)),
    ]

    dark, mid, hi = palettes[kind % len(palettes)]

    x, y = int(x), int(y)
    r = max(3, int(radius))

    pygame.draw.ellipse(
        dst, (13, 7, 5),
        (x-r+2, y-r+3, 2*r+4, 2*r+4)
    )

    pygame.draw.circle(dst, dark, (x, y), r)

    pygame.draw.circle(
        dst, mid, (x-1, y-1), max(2, r-2)
    )

    pygame.draw.ellipse(
        dst, hi,
        (x-r//2, y-r//2-2,
         max(3, r), max(2, r//2+1))
    )

    pygame.draw.circle(
        dst, (255, 252, 241),
        (x-r//3, y-r//3-1), max(1, r//5)
    )


# ============================================================
# MAIN GAME
# ============================================================

class Mancala:

    INTRO, OPENING, GAME, HELP, OVER = range(5)

    def __init__(self):

        self.state = self.INTRO

        self.board = [4] * 14
        self.board[6] = 0
        self.board[13] = 0

        self.turn = 1

        self.message = (
            "PLAYER 1 — choose a pit from A to F."
        )

        self.animation = None
        self.winner = None
        self.hover = None

        self.open_start = 0
        self.open_t = 0

        self.make_layout()

    # --------------------------------------------------------
    # RESPONSIVE SCREEN LAYOUT
    # --------------------------------------------------------

    def make_layout(self):

        self.header_y = max(82, int(H * .13))

        self.card_y = self.header_y + 18

        self.card_h = max(
            82, min(112, int(H * .14))
        )

        self.board_w = min(W - 90, 1420)

        self.board_h = min(
            360, max(260, int(H * .46))
        )

        self.board_x = (W - self.board_w) // 2

        self.board_y = (
            self.card_y + self.card_h + 30
        )

        footer_top = H - 112

        self.board_y = min(
            self.board_y,
            footer_top - self.board_h - 12
        )

        self.board_y = max(
            self.card_y + self.card_h + 12,
            self.board_y
        )

        self.board_rect = pygame.Rect(
            self.board_x,
            self.board_y,
            self.board_w,
            self.board_h
        )

        store_w = int(self.board_w * .105)

        gap = max(
            8, int(self.board_w * .012)
        )

        side = 12

        pit_w = int(
            (
                self.board_w
                - 2*store_w
                - 2*side
                - 5*gap
            ) / 6
        )

        pit_h = int(self.board_h * .34)

        x0 = self.board_x + store_w + side

        top_y = (
            self.board_y + int(self.board_h * .16)
        )

        bottom_y = (
            self.board_y + int(self.board_h * .57)
        )

        self.pits = {}

        for j, idx in enumerate(
            [12, 11, 10, 9, 8, 7]
        ):
            self.pits[idx] = pygame.Rect(
                x0 + j*(pit_w+gap),
                top_y,
                pit_w,
                pit_h
            )

        for j, idx in enumerate(range(6)):
            self.pits[idx] = pygame.Rect(
                x0 + j*(pit_w+gap),
                bottom_y,
                pit_w,
                pit_h
            )

        store_h = int(self.board_h * .78)

        self.stores = {

            13: pygame.Rect(
                self.board_x+10,
                self.board_y+int(self.board_h*.11),
                store_w,
                store_h
            ),

            6: pygame.Rect(
                self.board_rect.right-store_w-10,
                self.board_y+int(self.board_h*.11),
                store_w,
                store_h
            )
        }

        self.wood = wood_texture(
            (self.board_w, self.board_h), 21
        )

        self.restart_rect = pygame.Rect(
            W-220, H-66, 170, 44
        )

        self.menu_rect = pygame.Rect(
            50, H-66, 170, 44
        )

        self.message_rect = pygame.Rect(
            245, H-72, W-490, 56
        )

    # --------------------------------------------------------
    # RESET AND START
    # --------------------------------------------------------

    def reset(self):

        self.board[:] = [4] * 14

        self.board[6] = 0
        self.board[13] = 0

        self.turn = 1

        self.message = (
            "PLAYER 1 — choose a pit from A to F."
        )

        self.animation = None
        self.winner = None
        self.hover = None

        self.state = self.GAME

    def start_game(self):

        self.reset()

        self.state = self.OPENING

        self.open_start = pygame.time.get_ticks()
        self.open_t = 0

    # --------------------------------------------------------
    # GAME LOGIC
    # --------------------------------------------------------

    def center(self, idx):

        if idx in self.stores:
            return self.stores[idx].center

        return self.pits[idx].center

    def own_pit(self, idx):

        if self.turn == 1:
            return idx in range(6)

        return idx in range(7, 13)

    def start_move(self, idx):

        if (
            self.state != self.GAME
            or self.animation
            or not self.own_pit(idx)
        ):
            return

        if self.board[idx] == 0:

            self.message = (
                "That pit is empty. Choose another pit."
            )

            return

        player = self.turn

        seeds = self.board[idx]

        self.board[idx] = 0

        path = []

        pos = idx

        while seeds:

            pos = (pos + 1) % 14

            # Skip opponent's store
            if pos == (13 if player == 1 else 6):
                continue

            path.append(pos)

            seeds -= 1

        self.animation = {

            "player": player,
            "source": idx,
            "path": path,
            "last": path[-1],
            "step": 0,
            "timer": 0.0,
            "bead": None
        }

        self.message = (
            f"PLAYER {player} is sowing the seeds..."
        )

    def side_empty(self, player):

        slots = (
            range(6)
            if player == 1
            else range(7, 13)
        )

        return all(
            self.board[i] == 0 for i in slots
        )

    def finish_move(self):

        a = self.animation

        player = a["player"]
        last = a["last"]

        # Capture rule
        own_slots = (
            range(6)
            if player == 1
            else range(7, 13)
        )

        if last in own_slots:

            if self.board[last] == 1:

                opposite = 12 - last

                if self.board[opposite] > 0:

                    store = (
                        6 if player == 1 else 13
                    )

                    self.board[store] += (
                        self.board[opposite] + 1
                    )

                    self.board[last] = 0
                    self.board[opposite] = 0

                    self.message = (
                        "NICE CAPTURE! Seeds moved into your store."
                    )

        store = 6 if player == 1 else 13

        extra = last == store

        self.animation = None

        # End game
        if self.side_empty(1) or self.side_empty(2):

            for i in range(6):

                self.board[6] += self.board[i]
                self.board[i] = 0

            for i in range(7, 13):

                self.board[13] += self.board[i]
                self.board[i] = 0

            if self.board[6] > self.board[13]:
                self.winner = 1

            elif self.board[13] > self.board[6]:
                self.winner = 2

            else:
                self.winner = 0

            self.state = self.OVER

            self.message = "The game is complete."

        elif extra:

            self.turn = player

            self.message = (
                f"PLAYER {player} landed in the store — play again!"
            )

        else:

            self.turn = (
                2 if player == 1 else 1
            )

            self.message = (
                f"PLAYER {self.turn}'S TURN — choose a pit."
            )

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    def update(self, dt):

        if self.state == self.OPENING:

            self.open_t = clamp(
                (
                    pygame.time.get_ticks()
                    - self.open_start
                ) / 1250,
                0, 1
            )

            if self.open_t >= 1:
                self.state = self.GAME

        if not self.animation:
            return

        a = self.animation

        a["timer"] += dt

        if a["bead"]:

            a["bead"]["t"] += dt / .16

            if a["bead"]["t"] >= 1:

                a["bead"] = None
                a["step"] += 1
                a["timer"] = 0

            return

        if a["step"] >= len(a["path"]):

            self.finish_move()
            return

        if a["timer"] >= .09:

            idx = a["path"][a["step"]]

            prev = (
                a["source"]
                if a["step"] == 0
                else a["path"][a["step"]-1]
            )

            self.board[idx] += 1

            a["bead"] = {

                "start": self.center(prev),
                "end": self.center(idx),
                "t": 0.0
            }

            a["timer"] = 0

    # --------------------------------------------------------
    # DRAW PITS AND STORES
    # --------------------------------------------------------

    def draw_pit(self, idx, rect, store=False):

        x, y, w, h = rect

        cx, cy = rect.center

        active = (
            not store
            and self.state == self.GAME
            and self.own_pit(idx)
            and self.board[idx] > 0
            and not self.animation
        )

        hover = active and self.hover == idx

        # Outer shadow and wooden rim
        pygame.draw.ellipse(
            screen, (45, 22, 13),
            (x+2, y+7, w, h)
        )

        pygame.draw.ellipse(
            screen, (85, 51, 31), rect
        )

        pygame.draw.ellipse(
            screen, WOOD_LIGHT,
            rect.inflate(-3, -5), 3
        )

        pygame.draw.ellipse(
            screen, (116, 75, 48),
            rect.inflate(-12, -14), 3
        )

        inner = rect.inflate(-22, -24)

        pygame.draw.ellipse(
            screen, (29, 19, 14), inner
        )

        pygame.draw.arc(
            screen, (139, 96, 63),
            inner.inflate(-8, -8),
            3.3, 6.1, 2
        )

        if active:

            edge = (
                (166, 230, 181)
                if hover else GREEN
            )

            pygame.draw.ellipse(
                screen, edge,
                rect.inflate(9, 9), 3
            )

        elif hover:

            pygame.draw.ellipse(
                screen, GOLD,
                rect.inflate(8, 8), 2
            )

        # Draw seeds
        count = self.board[idx]

        rng = random.Random(
            idx*701 + count*31 + 15
        )

        r = max(
            5,
            int(min(w, h) * (
                .065 if not store else .045
            ))
        )

        visible = min(
            count,
            18 if not store else 28
        )

        coords = [(0, 0)]

        for ring, n in ((1, 5), (2, 8), (3, 10)):

            for j in range(n):

                ang = j*math.tau/n + ring*.42

                rr = r * (
                    1.5 if ring == 1
                    else 2.45 if ring == 2
                    else 3.15
                )

                coords.append((
                    math.cos(ang)*rr,
                    math.sin(ang)*rr*.72
                ))

        rng.shuffle(coords)

        for j in range(visible):

            dx, dy = coords[j % len(coords)]

            draw_seed(
                screen,
                cx+dx+rng.uniform(-1, 1),
                cy+dy+rng.uniform(-1, 1),
                r,
                rng.choices(
                    [0, 1, 2],
                    [3, 3, 4]
                )[0]
            )

        # Seed count badge
        badge_y = y - 17

        pygame.draw.circle(
            screen, (48, 22, 15),
            (int(cx), int(badge_y)), 18
        )

        pygame.draw.circle(
            screen, (153, 103, 65),
            (int(cx), int(badge_y)), 18, 1
        )

        text(
            screen, count,
            font(16, True),
            CREAM,
            (cx, badge_y)
        )

        label = (
            "STORE" if store
            else chr(65+idx) if idx < 6
            else chr(71+idx-7)
        )

        text(
            screen, label,
            font(13, True),
            GOLD if active else MUTED,
            (cx, y+h+13)
        )

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    def draw_button(self, rect, label, primary=False):

        hover = rect.collidepoint(
            pygame.mouse.get_pos()
        )

        fill = (
            (132, 78, 47)
            if primary
            else (56, 29, 22)
        )

        if hover:

            fill = (
                (163, 99, 58)
                if primary
                else (83, 44, 31)
            )

        rounded(
            screen, rect, fill, 10,
            GOLD if primary else (125, 83, 58),
            2
        )

        text(
            screen, label,
            font(15, True),
            CREAM,
            rect.center
        )

    # --------------------------------------------------------
    # PLAYER SCORE CARDS
    # --------------------------------------------------------

    def draw_card(self, player, rect):

        active = (
            self.state != self.OVER
            and self.turn == player
        )

        edge = (
            GREEN if player == 1 else GOLD
        )

        rounded(
            screen, rect,
            (51, 27, 21),
            17,
            edge if active else (111, 73, 52),
            2
        )

        text(
            screen, f"PLAYER {player}",
            font(19, True),
            edge,
            (rect.x+92, rect.y+27)
        )

        store = 6 if player == 1 else 13

        text(
            screen, self.board[store],
            font(43, True, True),
            CREAM,
            (rect.x+92, rect.y+72),
            True
        )

        text(
            screen, "SEEDS IN STORE",
            font(12, True),
            MUTED,
            (rect.x+210, rect.y+74)
        )

        text(
            screen,
            "YOUR TURN" if active else (
                "BOTTOM ROW"
                if player == 1
                else "TOP ROW"
            ),
            font(12, True),
            edge if active else MUTED,
            (rect.right-76, rect.y+27)
        )

    # --------------------------------------------------------
    # MAIN GAME BOARD
    # --------------------------------------------------------

    def draw_board(self):

        background()

        text(
            screen, "MANCALA",
            font(39, True, True),
            GOLD,
            (150, 38),
            True
        )

        text(
            screen, "C L A S S I C",
            font(13, True),
            MUTED,
            (150, 70)
        )

        pygame.draw.line(
            screen, (116, 73, 51),
            (50, self.header_y),
            (W-50, self.header_y), 1
        )

        card_w = min(320, int(W*.25))

        self.draw_card(
            2,
            pygame.Rect(
                55, self.card_y,
                card_w, self.card_h
            )
        )

        self.draw_card(
            1,
            pygame.Rect(
                W-55-card_w,
                self.card_y,
                card_w,
                self.card_h
            )
        )

        title = (
            "MATCH COMPLETE"
            if self.state == self.OVER
            else f"PLAYER {self.turn}'S TURN"
        )

        text(
            screen, title,
            font(20, True),
            GREEN if self.turn == 1 else GOLD,
            (W//2, self.card_y+self.card_h//2)
        )

        b = self.board_rect

        pygame.draw.rect(
            screen, (33, 16, 11),
            b.inflate(22, 28),
            border_radius=28
        )

        screen.blit(self.wood, b.topleft)

        pygame.draw.rect(
            screen, (226, 185, 132),
            b, 4, border_radius=22
        )

        pygame.draw.rect(
            screen, (91, 53, 31),
            b.inflate(-14, -14),
            2, border_radius=17
        )

        pygame.draw.line(
            screen, (104, 63, 39),
            (b.x+18, b.centery),
            (b.right-18, b.centery), 3
        )

        for idx, rect in self.stores.items():
            self.draw_pit(idx, rect, True)

        for idx, rect in self.pits.items():
            self.draw_pit(idx, rect, False)

        text(
            screen,
            "PLAYER 2  ·  G  H  I  J  K  L",
            font(12, True),
            (93, 57, 37),
            (W//2, b.y+13)
        )

        text(
            screen,
            "PLAYER 1  ·  A  B  C  D  E  F",
            font(12, True),
            (93, 57, 37),
            (W//2, b.bottom-12)
        )

        # Animated seed flying between pits
        if self.animation and self.animation["bead"]:

            bead = self.animation["bead"]

            t = ease(bead["t"])

            sx, sy = bead["start"]
            ex, ey = bead["end"]

            draw_seed(
                screen,
                sx+(ex-sx)*t,
                sy+(ey-sy)*t-math.sin(t*math.pi)*35,
                11, 3
            )

        rounded(
            screen,
            self.message_rect,
            (48, 25, 19),
            11,
            (116, 76, 53),
            1
        )

        text(
            screen, self.message,
            font(15),
            CREAM,
            self.message_rect.center
        )

        self.draw_button(
            self.menu_rect,
            "MENU  [ESC]"
        )

        self.draw_button(
            self.restart_rect,
            "↻  RESTART",
            True
        )

        if self.state == self.OVER:
            self.draw_winner()

    # --------------------------------------------------------
    # INTRO WOODEN BOX
    # --------------------------------------------------------

    def draw_box(self, t=0):

        x = int(W*.23)
        y = int(H*.14)
        w = int(W*.54)
        h = int(H*.48)

        base = pygame.Rect(
            x,
            y+int(h*.22),
            w,
            int(h*.78)
        )

        rounded(
            screen, base,
            (91, 52, 31),
            20,
            (39, 20, 13),
            4
        )

        boardwood = wood_texture(
            (w-18, int(h*.68)), 31
        )

        screen.blit(
            boardwood,
            (x+9, y+int(h*.27))
        )

        pygame.draw.rect(
            screen, WOOD_LIGHT,
            base, 3, border_radius=20
        )

        lift = int(ease(t)*h*.58)

        lid_y = y-lift

        lid_h = int(
            h*.66*(1-.14*ease(t))
        )

        lid_w = int(
            w*(1-.035*ease(t))
        )

        lid_x = (W-lid_w)//2

        lid = pygame.Rect(
            lid_x, lid_y,
            lid_w, lid_h
        )

        lidwood = wood_texture(
            (lid_w, max(90, lid_h)), 12
        )

        screen.blit(lidwood, lid.topleft)

        pygame.draw.rect(
            screen, (230, 190, 139),
            lid, 4, border_radius=14
        )

        pygame.draw.rect(
            screen, (119, 75, 46),
            lid.inflate(-18, -18),
            2, border_radius=10
        )

        if t < .45:

            text(
                screen, "MANCALA",
                font(48, True, True),
                (103, 57, 35),
                (W//2, lid.centery-9),
                True
            )

            text(
                screen, "C L A S S I C",
                font(18, True),
                (113, 68, 42),
                (W//2, lid.centery+35)
            )

    # --------------------------------------------------------
    # INTRO SCREEN
    # --------------------------------------------------------

    def draw_intro(self):

        background()

        self.draw_box(0)

        text(
            screen,
            "A GAME OF STRATEGY  ·  PATIENCE  ·  PRECISION",
            font(16, True),
            (222, 193, 161),
            (W//2, H*.72)
        )

        start = pygame.Rect(
            W//2-150,
            int(H*.80)-25,
            300, 52
        )

        helpb = pygame.Rect(
            W//2-150,
            int(H*.89)-22,
            300, 46
        )

        self.draw_button(
            start,
            "▶   START GAME",
            True
        )

        self.draw_button(
            helpb,
            "HOW TO PLAY"
        )

        self.intro_start_rect = start
        self.intro_help_rect = helpb

    # --------------------------------------------------------
    # OPENING ANIMATION
    # --------------------------------------------------------

    def draw_opening(self):

        self.draw_board()
        self.draw_box(self.open_t)

    # --------------------------------------------------------
    # HOW TO PLAY
    # --------------------------------------------------------

    def draw_help(self):

        background()

        text(
            screen, "HOW TO PLAY",
            font(42, True, True),
            GOLD,
            (W//2, 105),
            True
        )

        lines = [

            "1. Player 1 controls the bottom row (A–F).",

            "2. Player 2 controls the top row (G–L).",

            "3. Click a non-empty pit on your own side.",

            "4. Seeds are placed one by one around the board.",

            "5. Skip your opponent's store while sowing.",

            "6. Landing in your own store gives you an extra turn.",

            "7. Landing in an empty pit on your side can capture opposite seeds.",

            "8. When one side is empty, the player with the most seeds wins."

        ]

        step = min(47, int(H*.075))
        start_y = max(190, int(H*.25))

        for i, line in enumerate(lines):

            text(
                screen, line,
                font(17),
                CREAM,
                (W//2, start_y+i*step)
            )

        back = pygame.Rect(
            W//2-135, H-90,
            270, 48
        )

        self.draw_button(
            back,
            "←  BACK TO MENU",
            True
        )

        self.help_back_rect = back

    # --------------------------------------------------------
    # WINNER SCREEN
    # --------------------------------------------------------

    def draw_winner(self):

        shade = pygame.Surface(
            (W, H), pygame.SRCALPHA
        )

        shade.fill((8, 4, 3, 185))

        screen.blit(shade, (0, 0))

        box = pygame.Rect(
            W//2-270,
            H//2-145,
            540, 290
        )

        rounded(
            screen, box,
            (49, 27, 20),
            22,
            GOLD,
            3
        )

        text(
            screen, "MATCH COMPLETE",
            font(21, True),
            GOLD,
            (W//2, box.y+48)
        )

        headline = (
            "IT'S A DRAW"
            if self.winner == 0
            else f"PLAYER {self.winner} WINS!"
        )

        text(
            screen, headline,
            font(39, True, True),
            CREAM,
            (W//2, box.y+115),
            True
        )

        text(
            screen,
            f"PLAYER 1  {self.board[6]}     ·     PLAYER 2  {self.board[13]}",
            font(17),
            MUTED,
            (W//2, box.y+185)
        )

        text(
            screen,
            "Press RESTART to play again",
            font(14, True),
            GREEN,
            (W//2, box.y+235)
        )

    # --------------------------------------------------------
    # MOUSE CONTROLS
    # --------------------------------------------------------

    def click(self, pos):

        if self.state == self.INTRO:

            if self.intro_start_rect.collidepoint(pos):
                self.start_game()

            elif self.intro_help_rect.collidepoint(pos):
                self.state = self.HELP

            return

        if self.state == self.HELP:

            if self.help_back_rect.collidepoint(pos):
                self.state = self.INTRO

            return

        if self.state in (self.GAME, self.OVER):

            if self.restart_rect.collidepoint(pos):
                self.reset()
                return

            if self.menu_rect.collidepoint(pos):

                self.state = self.INTRO
                self.animation = None

                return

        if self.state == self.GAME and not self.animation:

            for idx, rect in self.pits.items():

                if rect.collidepoint(pos):

                    self.start_move(idx)
                    return

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    def run(self):

        global W, H, screen

        running = True

        while running:

            dt = min(
                clock.tick(FPS)/1000,
                .05
            )

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    running = False

                elif event.type == pygame.VIDEORESIZE:

                    W = max(1000, event.w)
                    H = max(660, event.h)

                    screen = pygame.display.set_mode(
                        (W, H),
                        pygame.RESIZABLE
                    )

                    self.make_layout()

                elif event.type == pygame.MOUSEMOTION:

                    self.hover = None

                    if (
                        self.state == self.GAME
                        and not self.animation
                    ):

                        for idx, rect in self.pits.items():

                            if (
                                rect.collidepoint(event.pos)
                                and self.own_pit(idx)
                                and self.board[idx] > 0
                            ):

                                self.hover = idx
                                break

                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):

                    self.click(event.pos)

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        if self.state in (
                            self.GAME,
                            self.OVER,
                            self.HELP
                        ):

                            self.state = self.INTRO
                            self.animation = None

                    elif (
                        event.key == pygame.K_r
                        and self.state in (
                            self.GAME,
                            self.OVER
                        )
                    ):

                        self.reset()

            self.update(dt)

            if self.state == self.INTRO:

                self.draw_intro()

            elif self.state == self.HELP:

                self.draw_help()

            elif self.state == self.OPENING:

                self.draw_opening()

            else:

                self.draw_board()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ============================================================
# START GAME
# ============================================================

if __name__ == "__main__":
    Mancala().run()
