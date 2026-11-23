#!/usr/bin/env python3
"""Render the 'Day one, day seven' TikTok video (1080x1920, 30fps).

Same tiny game (Ghost Grab), same map, same start — day one sparse,
day seven dense. The camera never moves; the change is the story.
Scenes: title, day-one play, transition, day-seven play, close,
then the official 9:16 referral end card with the code typed in.
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
FRAMES = os.path.join(WORK, "frames")
os.makedirs(FRAMES, exist_ok=True)

W, H, FPS = 1080, 1920, 30
INK = (29, 27, 22)
PAPER = (16, 13, 26)
CREAM = (242, 234, 216)
MAG = (200, 30, 130)
GOLD = (255, 217, 74)
RED = (229, 72, 77)
CYAN = (122, 224, 255)
PURPLE = (180, 154, 255)
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def centered(d, cx, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)
    return y + font.size


# ---- game simulation -------------------------------------------------
GW, GH = 1020, 574           # game window size on the vertical canvas
GX, GY = 30, 660             # its top-left corner
ARENA = (29, 24, 48)         # #1d1830
FIRST_COINS = [(300, 150), (520, 300), (760, 180)]  # identical day 1 & 7


def star(d, x, y, r, fill):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rad = r * 0.45 if i % 2 else r
        pts.append((x + rad * math.cos(a), y + rad * math.sin(a)))
    d.polygon(pts, fill=fill)


def ghost(d, x, y, r=22):
    d.ellipse([x - r, y - r, x + r, y + r + 6], fill=CREAM)
    for ex in (-8, 8):
        d.ellipse([x + ex - 3, y - 6, x + ex + 3, y + 2], fill=INK)
    d.arc([x - 7, y + 4, x + 7, y + 14], 20, 160, fill=INK, width=2)


def draw_game(d, state):
    d.rounded_rectangle([GX, GY, GX + GW, GY + GH], 10, fill=ARENA,
                        outline=(74, 63, 117), width=3)
    gx = lambda v: GX + v * GW / 960
    gy = lambda v: GY + v * GH / 540
    # trail (day 7)
    for i, (tx, ty) in enumerate(state.get("trail", [])):
        a = int(30 + i * 8)
        d.ellipse([gx(tx) - 14, gy(ty) - 14, gx(tx) + 14, gy(ty) + 14],
                  fill=(90, 80, 130))
    for (cx, cy) in state["coins"]:
        star(d, gx(cx), gy(cy), 15, GOLD)
    for (cx, cy) in state.get("golds", []):
        star(d, gx(cx), gy(cy), 19, (255, 179, 0))
    if state.get("magnet_on"):
        d.ellipse([gx(state["gx"]) - 120, gy(state["gy"]) - 120,
                   gx(state["gx"]) + 120, gy(state["gy"]) + 120],
                  outline=CYAN, width=3)
    for (bx, by, s) in state["blocks"]:
        d.rectangle([gx(bx), gy(by), gx(bx + s), gy(by + s)], fill=RED)
    for p in state.get("parts", []):
        d.rectangle([gx(p[0]) - 3, gy(p[1]) - 3, gx(p[0]) + 3, gy(p[1]) + 3],
                    fill=p[2])
    ghost(d, gx(state["gx"]), gy(state["gy"]))
    if state.get("shield_on"):
        d.ellipse([gx(state["gx"]) - 34, gy(state["gy"]) - 34,
                   gx(state["gx"]) + 34, gy(state["gy"]) + 34],
                  outline=PURPLE, width=4)
    for (px, py, txt) in state.get("pops", []):
        d.text((gx(px), gy(py)), txt, font=F(SANS_B, 26), fill=CREAM)
    # HUD inside the game window
    d.text((GX + 18, GY + 12), state["hud"], font=F(MONO_B, 30), fill=CREAM)


def day1_state(t):
    """t seconds into the day-one clip (10s). Sparse and slow."""
    waypoints = [(90, 287)] + FIRST_COINS + [(620, 420), (300, 460)]
    # walk the waypoints at a gentle pace
    seg = 10.0 / (len(waypoints) - 1)
    i = min(int(t / seg), len(waypoints) - 2)
    f = (t - i * seg) / seg
    x0, y0 = waypoints[i]
    x1, y1 = waypoints[i + 1]
    gx, gy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
    taken = sum(1 for k in range(1, 4) if t >= k * seg - 0.05)
    coins = [c for k, c in enumerate(FIRST_COINS) if k >= taken]
    blocks = [(450, 80 + 40 * math.sin(t * 0.5), 34), (650, 380 + 40 * math.cos(t * 0.4), 34)]
    return {"gx": gx, "gy": gy, "coins": coins, "blocks": blocks,
            "hud": f"SCORE {taken} · TIME {60 - int(t)}"}


def day7_state(t, rng_state):
    """t seconds into the day-seven clip (14s). Same start, far more going on."""
    # ghost chases a fast waypoint loop; first three coins sit exactly
    # where they did on day one, plus seven more and three golds.
    path = [(90, 287), (300, 150), (520, 300), (760, 180), (830, 430),
            (560, 470), (300, 380), (150, 470), (420, 90), (700, 330)]
    seg = 14.0 / len(path)
    i = int(t / seg) % len(path)
    f = (t - i * seg) / seg
    x0, y0 = path[i]
    x1, y1 = path[(i + 1) % len(path)]
    gx, gy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
    rng_state.setdefault("trail", []).append((gx, gy))
    if len(rng_state["trail"]) > 10:
        rng_state["trail"].pop(0)
    magnet_on = 5.0 < t < 8.0
    shield_on = t > 9.5
    # coins shrink as the ghost "collects" them on its loop; respawns keep
    # the arena busy. Deterministic pseudo-collect by distance.
    extra = [(180, 90), (640, 90), (880, 260), (120, 300), (430, 430),
             (760, 470), (880, 90)]
    coins = []
    grabs = 0
    for c in FIRST_COINS + extra:
        ph = (t * 0.9 + (c[0] % 7) * 0.35) % 3.0
        if ph < 2.6:
            coins.append(c)
        else:
            grabs += 1
    golds = [(240, 470), (700, 140), (520, 60)] if (t % 4) < 3.2 else [(520, 60)]
    score = int(t * 11) + grabs * 3
    combo = min(9, 1 + int(t / 2.2))
    blocks = [(200 + 60 * math.sin(t * 1.3), 60, 34), (420, 300 + 90 * math.sin(t * 1.7), 34),
              (600 + 50 * math.cos(t * 1.1), 120, 34), (820, 350 + 80 * math.cos(t * 1.9), 34),
              (330, 430 + 60 * math.sin(t * 2.2), 34), (700, 190, 84)]
    parts = []
    if int(t * 30) % 9 == 0:
        for k in range(6):
            a = k * 1.05 + t
            parts.append((gx + 26 * math.cos(a), gy + 26 * math.sin(a), GOLD))
    pops = []
    if (t % 2.2) < 0.5:
        pops.append((gx + 20, gy - 40, f"+{5 * combo}"))
    return {"gx": gx, "gy": gy, "coins": coins, "golds": golds, "blocks": blocks,
            "trail": list(rng_state["trail"]), "magnet_on": magnet_on,
            "shield_on": shield_on, "parts": parts, "pops": pops,
            "hud": f"SCORE {score} · COMBO x{combo} · TIME {60 - int(t)}" +
                   (" · MAGNET" if magnet_on else "") + (" · SHIELD" if shield_on else "")}


def base():
    return Image.new("RGB", (W, H), PAPER)


def chip(d, text, fill):
    f = F(SANS_B, 40)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([W / 2 - w / 2 - 26, 470, W / 2 + w / 2 + 26, 546], 14, fill=fill)
    d.text((W / 2 - w / 2, 486), text, font=f, fill=(255, 255, 255))


def caption(d, text, y=1330, size=44, fill=CREAM):
    centered(d, W / 2, y, text, F(SANS, size), fill)


def render():
    total = 34.5
    n = int(total * FPS)
    rng7 = {}
    for idx in range(n):
        t = idx / FPS
        img = base()
        d = ImageDraw.Draw(img)
        if t < 2.0:  # title
            centered(d, W / 2, 700, "DAY ONE.", F(SERIF_B, 130), CREAM)
            caption(d, "my AI agent built a game", 900)
            caption(d, "from ONE prompt", 960)
        elif t < 12.0:  # day one gameplay
            centered(d, W / 2, 240, "DAY ONE", F(SERIF_B, 92), CREAM)
            chip(d, "GHOST GRAB · DAY ONE BUILD", (90, 80, 130))
            draw_game(d, day1_state(t - 2.0))
            caption(d, "3 coins. 2 blocks. that was the game.", 1330)
        elif t < 16.0:  # transition
            centered(d, W / 2, 700, "then it kept", F(SERIF_B, 96), CREAM)
            centered(d, W / 2, 830, "UPDATING IT", F(SERIF_B, 110), GOLD)
            caption(d, "every day — for a week", 1010)
        elif t < 30.0:  # day seven gameplay
            centered(d, W / 2, 240, "DAY SEVEN", F(SERIF_B, 92), GOLD)
            chip(d, "GHOST GRAB · DAY SEVEN BUILD", MAG)
            draw_game(d, day7_state(t - 16.0, rng7))
            caption(d, "same start. everything else — MORE.", 1330)
            caption(d, "gold stars · magnet · shield · combos · particles", 1400, 36, (200, 195, 220))
        else:  # close
            st = day7_state(13.9, {"trail": []})
            draw_game(d, st)
            ov = Image.new("RGB", (W, H), (10, 8, 18))
            img = Image.blend(img, ov, 0.45)
            d = ImageDraw.Draw(img)
            centered(d, W / 2, 780, "Same game.", F(SERIF_B, 104), CREAM)
            centered(d, W / 2, 930, "Start yours at", F(SERIF_B, 84), CREAM)
            centered(d, W / 2, 1050, "make.fun", F(SERIF_B, 120), MAG)
        img.save(os.path.join(FRAMES, f"f{idx:04d}.png"))
    print("frames:", n)


if __name__ == "__main__":
    render()
