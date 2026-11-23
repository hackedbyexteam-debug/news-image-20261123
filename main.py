#!/usr/bin/env python3
"""The World in One Page -- Monday 23 November 2026.

make.fun bounty news-image-20261123: sum up 23 November 2026's world news
in one 1024x1024 PNG, drawn as a newspaper front page.

Stories were checked against wire and press reports published on Monday
23 November 2026 (Reuters, AP, CNN, BBC, The Guardian, CBS/NBC projections
and the One Turn daily digest). Numbers are as reported on the day; where
wires updated a toll through the day, the latest Monday figure is used and
the copy says so.

The program is deterministic and offline: copy and layout are fixed in this
file, fonts are bundled under assets/fonts/, and there is no network, clock
or randomness, so two runs write identical bytes. If Pillow cannot render
for any reason, it falls back to the pre-rendered image at assets/entry.png.
"""

import math
import shutil
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "assets" / "fonts"
FALLBACK = HERE / "assets" / "entry.png"
OUT = Path("/output/entry.png")

W = H = 1024
M = 34                      # page margin
CW = W - 2 * M              # 956 content width

# --- newsprint palette ---------------------------------------------------
PAPER = (250, 245, 233)
CARD = (255, 252, 244)
INK = (24, 24, 22)
SOFT = (74, 70, 62)
FAINT = (122, 116, 104)
TEAL = (13, 84, 78)         # lead accent: climate
TEAL_DARK = (9, 58, 54)
RED = (172, 32, 22)         # war accent
NAVY = (23, 38, 66)         # politics accent
GOLD = (184, 138, 24)
AMBER = (214, 132, 16)
SKY = (36, 110, 138)
HAIR = (198, 190, 172)


@lru_cache(maxsize=64)
def load(name, size):
    from PIL import ImageFont
    return ImageFont.truetype(str(FONTS / name), size)


class Page:
    """Small drawing helper bound to one Pillow canvas."""

    def __init__(self):
        from PIL import Image, ImageDraw
        self.img = Image.new("RGB", (W, H), PAPER)
        self.d = ImageDraw.Draw(self.img)

    def serif_b(self, s):
        return load("LiberationSerif-Bold.ttf", s)

    def serif(self, s):
        return load("LiberationSerif-Regular.ttf", s)

    def sans_b(self, s):
        return load("LiberationSans-Bold.ttf", s)

    def sans(self, s):
        return load("LiberationSans-Regular.ttf", s)

    def deja(self, s):
        return load("DejaVuSans.ttf", s)

    def width(self, text, font):
        return self.d.textlength(text, font=font)

    def split(self, text, font, max_w):
        """Greedy wrap into lines no wider than max_w."""
        out, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if self.width(trial, font) <= max_w or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = word
        if cur:
            out.append(cur)
        return out

    def flow(self, x, y, text, font, max_w, fill, step):
        """Draw wrapped text; return the y below the last line."""
        for line in self.split(text, font, max_w):
            self.d.text((x, y), line, font=font, fill=fill)
            y += step
        return y

    def caps(self, x, y, text, font, fill, gap=2):
        """Letter-spaced capitals; returns the width consumed."""
        cx = x
        for ch in text:
            self.d.text((cx, y), ch, font=font, fill=fill)
            cx += self.width(ch, font) + gap
        return cx - x

    def hline(self, x, y, w, fill=INK, px=2):
        self.d.line([(x, y), (x + w, y)], fill=fill, width=px)

    def chip(self, x, y, text, bg, font):
        """Solid label chip; returns its width."""
        inner = self.width(text, font) + 2 * (len(text) - 1) + 24
        self.d.rounded_rectangle([x, y, x + inner, y + 30], radius=3, fill=bg)
        self.caps(x + 12, y + 7, text, font, (255, 255, 255))
        return inner

    def story(self, x, y, w, accent, tag, head, body,
              head_size=27, body_size=16, body_step=21):
        """A headed story block with a coloured top bar."""
        self.d.rectangle([x, y, x + w, y + 5], fill=accent)
        self.caps(x, y + 15, tag, self.sans_b(13), accent)
        ny = self.flow(x, y + 37, head, self.serif_b(head_size), w,
                       INK, head_size + 6)
        self.flow(x, ny + 5, body, self.sans(body_size), w, SOFT,
                  body_step)


def cracked_globe(p, x0, y0, x1, y1):
    """Hero art: a cracked globe over the Antalya coast, COP31 in ruins.

    Flat editorial illustration: a low sun over the Taurus mountains and
    the sea, a globe with recognisable continents split by a heavy crack
    with splinters, a solid NO DEAL stamp, and the dateline beside it in
    the dark strip below the sea so it stays legible.
    """
    d = p.d
    d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=TEAL_DARK)
    # pale sun, low over the sea, clear of the globe
    sx, sy = x0 + 58, y0 + 46
    for r, col in ((38, (160, 116, 32)), (27, (201, 150, 44)),
                   (17, (240, 196, 90))):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=col)
    # distant Taurus mountains
    d.polygon([(x0, y0 + 118), (x0 + 70, y0 + 88), (x0 + 130, y0 + 118),
               (x0 + 190, y0 + 92), (x0 + 250, y0 + 118), (x1, y0 + 118),
               (x1, y0 + 122), (x0, y0 + 122)],
              fill=(24, 74, 72))
    # sea
    sea = y0 + 122
    d.rectangle([x0, sea, x1, y1 - 44], fill=(16, 96, 104))
    for wy in (sea + 16, sea + 38, sea + 58):
        for k in range(3):
            ax = x0 + 14 + k * 92
            d.arc([ax, wy - 8, ax + 60, wy + 10], 200, 340,
                  fill=(90, 170, 180), width=3)
    # the globe, cracked: vertices all inside the circle, so the flat
    # continents read as a world map and never poke past the rim
    gx, gy, gr = x0 + 196, y0 + 112, 76
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(38, 132, 120),
              outline=(240, 196, 90), width=3)

    def land(pts):
        d.polygon([(gx + u, gy + v) for u, v in pts], fill=(214, 178, 84))

    land([(-60, -36), (-34, -54), (-8, -46), (-14, -24), (-36, -12),
          (-54, -16)])                       # North America
    land([(-40, -2), (-20, 2), (-12, 26), (-26, 50), (-40, 38),
          (-46, 16)])                        # South America
    land([(6, -18), (32, -28), (48, -8), (40, 16), (22, 32),
          (8, 12)])                          # Africa
    land([(28, -50), (54, -46), (64, -30), (54, -18),
          (36, -32)])                        # Eurasia
    land([(56, -10), (70, -4), (66, 14), (52, 10)])   # S / SE Asia
    land([(48, 34), (62, 32), (60, 42), (50, 46)])    # Australia
    # the crack: a heavy jagged split down the globe, with splinters
    crack = [(gx + 2, gy - gr + 3), (gx - 14, gy - 40), (gx + 10, gy - 12),
             (gx - 10, gy + 16), (gx + 12, gy + 42), (gx - 2, gy + gr - 3)]
    d.line(crack, fill=(255, 255, 255), width=7, joint="curve")
    d.line(crack, fill=RED, width=3, joint="curve")
    d.line([(gx - 10, gy + 16), (gx - 30, gy + 30), (gx - 38, gy + 48)],
           fill=(255, 255, 255), width=4, joint="curve")
    d.line([(gx + 10, gy - 12), (gx + 30, gy - 22), (gx + 40, gy - 38)],
           fill=(255, 255, 255), width=4, joint="curve")
    # solid NO DEAL stamp and dateline, side by side in the dark strip
    # below the sea so neither fights the waves
    stamp = "NO DEAL"
    sf = p.sans_b(20)
    sw = p.width(stamp, sf)
    bx, by = x0 + 14, y1 - 38
    d.rectangle([bx, by, bx + sw + 22, by + 28], fill=RED)
    d.text((bx + 11, by + 4), stamp, font=sf, fill=(255, 255, 255))
    d.text((bx + sw + 36, by + 6), "ANTALYA, TURKEY",
           font=p.sans_b(14), fill=GOLD)


def build():
    p = Page()
    d = p.d

    # --- frame ------------------------------------------------------------
    d.rectangle([0, 0, W - 1, H - 1], outline=NAVY, width=4)
    d.rectangle([10, 10, W - 11, H - 11], outline=INK, width=1)

    # --- masthead: cream, big serif nameplate ----------------------------
    p.caps(M, 26, "MONDAY  ·  ONE DAY, ONE IMAGE", p.sans_b(13), FAINT)
    right = "EST. 2026 — THE DAILY FRONT PAGE"
    d.text((W - M - p.width(right, p.sans(13)), 26), right,
           font=p.sans(13), fill=FAINT)
    d.text((W // 2, 44), "THE WORLD IN ONE PAGE", font=p.serif_b(56),
           fill=INK, anchor="ma")
    d.text((W // 2, 108), "Monday, 23 November 2026",
           font=p.serif(22), fill=SOFT, anchor="ma")
    p.hline(M, 140, CW, fill=INK, px=3)
    p.hline(M, 145, CW, fill=INK, px=1)

    # --- lead: COP31 collapses --------------------------------------------
    ly = 158
    p.chip(M, ly, "CLIMATE — COP31 COLLAPSES", RED, p.sans_b(14))
    mood = "WORLD MOOD: FRACTURED"
    d.text((W - M - p.width(mood, p.sans_b(15)), ly + 6), mood,
           font=p.sans_b(15), fill=RED)
    y = p.flow(M, ly + 44, "Climate talks collapse with no deal",
               p.serif_b(42), 600, INK, 48)
    y = p.flow(M, y + 6,
               "After 14 days in Antalya — two days past deadline — COP31 "
               "ended on Sunday with no deal, the first climate summit to "
               "collapse since 2009. The EU and about 130 other parties "
               "rejected a final text silent on fossil fuels.",
               p.sans(17), 600, SOFT, 23)
    # key figures at a glance, echoing the lead's own facts
    p.caps(M, y + 6, "14 DAYS  ·  130+ PARTIES SAID NO  ·  FIRST COLLAPSE "
           "SINCE 2009", p.sans_b(13), RED)
    cracked_globe(p, 668, ly, W - M, 386)
    p.hline(M, 400, CW, px=2)

    # --- second row: Ukraine, two fronts ----------------------------------
    ry = 414
    p.story(M, ry, 468, RED, "UKRAINE — DYMER",
            "Strike on flats kills 11 as rescuers dig on",
            "A Russian drone hit a five-storey block in Dymer, 45 km north "
            "of Kyiv, as the region counted at least 14 dead. A seven-year-"
            "old boy was pulled alive from the rubble after nearly 14 hours; "
            "the Kyiv region declared 23 November a day of mourning.")
    p.story(522, ry, 468, NAVY, "LIBYA — BENGHAZI",
            "Ukraine sinks a Russian warship in Libya",
            "President Zelensky confirmed on Monday that seven Ukrainian "
            "sea drones sank the corvette Merkury in Benghazi and destroyed "
            "a Ka-27 helicopter aboard. A second target, the cargo ship MV "
            "Angara, was also hit — the war reaching far beyond Ukraine.")
    p.hline(M, 606, CW, fill=HAIR, px=1)

    # --- third row: three stories ------------------------------------------
    ty = 620
    p.story(M, ty, 305, NAVY, "USA — MIDTERMS",
            "Democrats take 258 House seats",
            "Chuck Hubbard's recount win over Virginia Foxx in North "
            "Carolina gave Democrats their largest House majority since "
            "1992 — and control of both chambers of Congress.",
            head_size=24, body_size=15, body_step=19)
    p.story(359, ty, 306, RED, "THE GULF — HORMUZ",
            "Iran claims a US drone downed",
            "Tehran said it shot down a US MQ-9 Reaper over the Strait of "
            "Hormuz, its 58th such claim. Houthis said they hit a Saudi "
            "refinery; Brent crude held near $93 on the war risk.",
            head_size=24, body_size=15, body_step=19)
    p.story(685, ty, 305, SKY, "NATO — BRUSSELS",
            "Allies meet over Poland missiles",
            "NATO's council meets in Brussels after Russian missiles fell "
            "on Polish soil. The US spy chief called Putin \"not America's "
            "friend\" — days after Trump called him one.",
            head_size=24, body_size=15, body_step=19)
    p.hline(M, 806, CW, px=2)

    # --- markets strip -------------------------------------------------------
    d.rectangle([M, 818, W - M, 854], fill=NAVY)
    tick = ("MARKETS   KOSPI opens ~3% lower   ·   ASIAN SHARES SLIDE ON AI "
            "FEARS   ·   BRENT $92.67  ▲ 0.11%   ·   KOREAN CHIPMAKERS ~-3%")
    tf = p.deja(15)
    for size in (15, 14, 13, 12):
        tf = p.deja(size)
        if p.width(tick, tf) <= CW - 24:
            break
    while p.width(tick, tf) > CW - 24 and len(tick) > 20:
        tick = tick[:-4].rstrip() + "…"
    d.text((M + 12, 828), tick, font=tf, fill=(255, 255, 255))

    # --- also today -----------------------------------------------------------
    ay = 862
    p.caps(M, ay, "ALSO TODAY", p.sans_b(14), INK)
    src = "Compiled from wire reports published on Monday 23 November 2026"
    d.text((W - M - p.width(src, p.sans(11)), ay + 2), src,
           font=p.sans(11), fill=FAINT)
    p.hline(M, ay + 22, CW, fill=HAIR, px=1)

    left = [
        ("USA — ", "Delta outage delays 1,600+ flights from Atlanta as "
         "Thanksgiving travel begins."),
        ("USA — ", "Trump signs the Common Cents Act: the penny ends, cash "
         "rounds to the nearest nickel."),
        ("BELGIUM — ", "Airports face a near-total shutdown in a nationwide "
         "austerity strike."),
    ]
    right_items = [
        ("NEPAL — ", "PM Balen Shah received in Delhi on his first bilateral "
         "trip to India."),
        ("INDONESIA — ", "Search resumes at the Cikande candy factory: 3 "
         "dead, dozens still missing."),
        ("BRAZIL — ", "Bolsonaro in intensive care with an intestinal "
         "obstruction; Mongolia's president resigns."),
    ]

    def column(x, w, items):
        yy = ay + 28
        for lead, body in items:
            tag_font = p.sans_b(13)
            body_font = p.sans(13)
            tag_w = p.width(lead, tag_font)
            d.text((x, yy), lead, font=tag_font, fill=INK)
            # Wrap the body into the space left on the tag's line, then
            # flow the rest at full column width. Measuring the tag in
            # its real (bold) font keeps the first line inside the
            # column; the old code wrapped tag+body in the regular font
            # and sliced by character count, which could overshoot.
            words = body.split()
            first = []
            while words and p.width(" ".join(first + [words[0]]),
                                    body_font) <= w - tag_w:
                first.append(words.pop(0))
            d.text((x + tag_w, yy), " ".join(first), font=body_font,
                   fill=SOFT)
            yy += 16
            rest = " ".join(words)
            if rest:
                yy = p.flow(x, yy, rest, body_font, w, SOFT, 16)
            yy += 4

    column(M, 468, left)
    column(522, 468, right_items)

    return p.img


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        build().save(OUT, format="PNG", optimize=True)
    except Exception as exc:
        print(f"render failed ({exc}); using fallback image",
              file=sys.stderr)
        shutil.copyfile(FALLBACK, OUT)


if __name__ == "__main__":
    main()
