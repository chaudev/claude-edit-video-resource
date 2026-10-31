import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine.core import W, H, font, clamp, prog, eo, eio, back, lerp, paste_alpha, tx, rect, chip, reg
BP = (20, 70, 136); BPD = (12, 42, 88); LN = (236, 244, 255); CYN = (130, 214, 255); RED = (255, 96, 84); YEL = (255, 214, 92); MUTE = (150, 185, 225)
def jb(s, w='Bold'): return font('mono', s, w)
def hand(s): return font('hand', s)
def xb(s): return font('bv', s, 'ExtraBold')
# ---------- background: living blueprint ----------
def make_bg(base):
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - .22 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2
    rg = np.random.default_rng(9)
    arr = np.clip(np.array(base, np.float32)[None, None] * v[..., None] + rg.normal(0, 2.5, (H, W, 1)), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)
BGIMG = {'bp': make_bg(BP), 'dark': make_bg(BPD)}
GRID = Image.new('RGBA', (W + 150, H + 150), (0, 0, 0, 0)); g = ImageDraw.Draw(GRID)
for x in range(0, W + 151, 30): g.line([(x, 0), (x, H + 150)], fill=LN + (22 if x % 150 else 55,), width=1 if x % 150 else 2)
for y in range(0, H + 151, 30): g.line([(0, y), (W + 150, y)], fill=LN + (22 if y % 150 else 55,), width=1 if y % 150 else 2)
COMP = Image.new('RGBA', (900, 900), (0, 0, 0, 0)); c = ImageDraw.Draw(COMP)
for r in (440, 380, 250): c.ellipse((450 - r, 450 - r, 450 + r, 450 + r), outline=LN + (40,), width=2)
for i in range(72):
    a = math.radians(i * 5); r0 = 410 if i % 6 else 360
    c.line([(450 + math.cos(a) * r0, 450 + math.sin(a) * r0), (450 + math.cos(a) * 440, 450 + math.sin(a) * 440)], fill=LN + (45,), width=2)
for i in range(4):
    a = math.radians(i * 90)
    c.line([(450, 450), (450 + math.cos(a) * 440, 450 + math.sin(a) * 440)], fill=LN + (30,), width=2)
# faint drifting sketches (houses & dimension lines)
SK = Image.new('RGBA', (W * 2, 420), (0, 0, 0, 0)); s_ = ImageDraw.Draw(SK)
for i in range(6):
    x = 80 + i * 360; b = 380; w = 220; h = 160
    s_.rectangle((x, b - h, x + w, b), outline=LN + (35,), width=3)
    s_.polygon([(x - 20, b - h), (x + w / 2, b - h - 110), (x + w + 20, b - h)], outline=LN + (35,))
    s_.line([(x, b + 20), (x + w, b + 20)], fill=LN + (35,), width=2)
    s_.text((x + w / 2 - 30, b + 22), f'{w * 10}', font=jb(24, 'Regular'), fill=LN + (45,))

def background(theme, t):
    img = BGIMG[theme].copy()
    o = int(t * 18) % 150
    gc = GRID.crop((o, o // 2, o + W, o // 2 + H)); img.paste(gc, (0, 0), gc)
    cp = COMP.rotate(t * 6, resample=Image.BILINEAR)
    img.paste(cp, (W // 2 - 450 + 260, 720 - 450 + 120), cp)
    off = int(t * 40) % W
    sk = SK.crop((off, 0, off + W, 420)); img.paste(sk, (0, 1520), sk)
    # scanning light band
    yb = (t * 260) % (H + 600) - 300
    band = Image.new('RGBA', (W, 200), CYN + (0,))
    a = np.clip(np.exp(-((np.arange(200) - 100) / 45) ** 2) * 28, 0, 255).astype(np.uint8)
    band.putalpha(Image.fromarray(np.repeat(a[:, None], W, 1)))
    img.paste(band, (0, int(yb)), band)
    return img

# ---------- line-art helpers ----------
def path(img, pts, k, col=LN, width=6, group=None):
    if k <= 0 or len(pts) < 2: return
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    lens = [math.dist(a, b) for a, b in segs]; tot = sum(lens); lim = tot * clamp(k)
    d = ImageDraw.Draw(img); acc = 0
    for (a, b), l in zip(segs, lens):
        if acc >= lim: break
        f = min(1, (lim - acc) / l) if l else 1
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, e], fill=col, width=width); acc += l
    if group is not False:
        for a, b in segs:
            reg((min(a[0], b[0]) - width / 2, min(a[1], b[1]) - width / 2, max(a[0], b[0]) + width / 2, max(a[1], b[1]) + width / 2), group or ('path', pts[0]), 1)

def house(img, cx, by, w, h, k, col=LN, group=None, xmark=0, width=6):
    x0, x1 = cx - w / 2, cx + w / 2
    path(img, [(x0, by), (x0, by - h), (x1, by - h), (x1, by), (x0, by)], k * 2, col, width, group=group or ('house', cx))
    path(img, [(x0 - 30, by - h), (cx, by - h - w * .45), (x1 + 30, by - h)], k * 2 - 1, col, width, group=group or ('house', cx))
    if k > .6:
        q = (k - .6) / .4
        path(img, [(cx - w * .12, by), (cx - w * .12, by - h * .55), (cx + w * .12, by - h * .55), (cx + w * .12, by)], q, col, width - 2, group=group or ('house', cx))
    reg((x0 - 30, by - h - w * .45, x1 + 30, by), group or ('house', cx), 1)
    if xmark > 0:
        d = ImageDraw.Draw(img); s = eio(clamp(xmark * 2)); s2 = eio(clamp(xmark * 2 - 1))
        d.line([(x0 - 20, by - h - w * .45), (x0 - 20 + (w + 40) * s, by - h - w * .45 + (h + w * .45) * s)], fill=RED, width=12)
        if s2 > 0: d.line([(x1 + 20, by - h - w * .45), (x1 + 20 - (w + 40) * s2, by - h - w * .45 + (h + w * .45) * s2)], fill=RED, width=12)

def dim(img, x0, x1, y, label, k, col=CYN):
    if k <= 0: return
    xe = lerp(x0, x1, eio(k)); d = ImageDraw.Draw(img)
    d.line([(x0, y), (xe, y)], fill=col, width=3)
    d.line([(x0, y - 14), (x0, y + 14)], fill=col, width=3)
    if k >= 1: d.line([(x1, y - 14), (x1, y + 14)], fill=col, width=3)
    if k >= 1: tx(img, label, jb(34), (x0 + x1) / 2, y + 36, col, 1, group=('dim', label))

def stampbox(img, text, cx, cy, at, t, col=RED, rot=-8, size=96, group=None):
    p = prog(t, at - .05, .22)
    if p <= 0: return
    f = jb(size, 'ExtraBold'); w = int(f.getlength(text) + 80); h = size + 80
    L = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle((8, 8, w * 2 - 8, h * 2 - 8), radius=24, outline=col + (255,), width=14)
    d.text((w, h), text, font=jb(size * 2, 'ExtraBold'), fill=col + (255,), anchor='mm')
    sc = 1 + 1.3 * (1 - eo(p))
    L = L.resize((int(w * sc), int(h * sc)), Image.LANCZOS).rotate(rot, resample=Image.BICUBIC, expand=True)
    paste_alpha(img, L, cx - L.size[0] / 2, cy - L.size[1] / 2, eo(p * 1.5))
    if p >= 1: reg((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), group or ('stamp', text), 1)


def transition(img, t, dt, theme=None):
    """white line sweep like turning a drawing sheet"""
    if dt >= .3: return img
    k = eio(dt / .3); x = max(1, lerp(-60, W + 60, k))
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rectangle((0, 0, x, H), fill=BP + (int(200 * (1 - k)),)); d.line([(x, 0), (x, H)], fill=LN + (255,), width=6)
    img.paste(L, (0, 0), L); return img
def bg(t, theme='bp'):
    """themes: bp | dark"""
    return background(theme, t)

# ---------- per-scene background variants: 'pattern/color' ; patterns grid|iso|graph|plan|protractor ; colors bp|dark ----------
def _iso(theme, t):
    img = BGIMG[theme].copy(); d = ImageDraw.Draw(img); o = (t * 25) % 80
    for k in range(-40, 60):
        x = k * 80 + o
        d.line([(x, 0), (x + H * .577, H)], fill=(50, 100, 170), width=1); d.line([(x, 0), (x - H * .577, H)], fill=(50, 100, 170), width=1)
    for i in range(5):
        cx = 180 + i * 190; cy = 1600 + 40 * math.sin(t + i); s = 60 + 10 * i
        pts = [(cx, cy - s), (cx + s * .87, cy - s / 2), (cx + s * .87, cy + s / 2), (cx, cy + s), (cx - s * .87, cy + s / 2), (cx - s * .87, cy - s / 2)]
        d.polygon(pts, outline=LN); d.line([(cx, cy), (cx, cy + s)], fill=LN); d.line([(cx, cy), (cx - s * .87, cy - s / 2)], fill=LN); d.line([(cx, cy), (cx + s * .87, cy - s / 2)], fill=LN)
    return img
def _graph(theme, t):
    img = BGIMG[theme].copy(); gc = GRID.crop((0, 0, W, H)); img.paste(gc, (0, 0), gc); d = ImageDraw.Draw(img)
    for k, (amp, fr, col) in enumerate([(120, 1.2, (80, 140, 210)), (80, 2.1, (70, 120, 190)), (160, .7, (60, 110, 180))]):
        pts = [(x, 1450 + k * 90 + amp * math.sin(x * .006 * fr + t * (1 + k * .4))) for x in range(0, W + 10, 10)]
        d.line(pts, fill=col, width=4)
    return img
_PLAN = [((120, 1500), (520, 1500), (520, 1820), (120, 1820), (120, 1500)), ((520, 1560), (960, 1560), (960, 1820), (520, 1820)),
         ((300, 1500), (300, 1640)), ((740, 1560), (740, 1700)), ((120, 1660), (220, 1660))]
def _plan(theme, t):
    img = BGIMG[theme].copy(); gc = GRID.crop((0, 0, W, H)); img.paste(gc, (0, 0), gc)
    k = (t * .25) % 1.4
    for i, pts in enumerate(_PLAN): path(img, list(pts), clamp(k * 3 - i * .4), (110, 160, 220), 5, group=False)
    cp = COMP.rotate(-t * 4, resample=Image.BILINEAR); img.paste(cp, (W // 2 - 450, 700 - 450), cp)
    return img
def _protractor(theme, t):
    img = BGIMG[theme].copy(); d = ImageDraw.Draw(img); cx, cy = W / 2, 1650
    for r in (300, 420, 560, 720):
        d.arc((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=(70, 120, 190), width=3)
    for a in range(0, 181, 5):
        ra = math.radians(180 + a); r0 = 680 if a % 15 else 640
        d.line([(cx + math.cos(ra) * r0, cy + math.sin(ra) * r0), (cx + math.cos(ra) * 720, cy + math.sin(ra) * 720)], fill=(90, 140, 210), width=2)
    a = math.radians(180 + 90 + 80 * math.sin(t * .6)); d.line([(cx, cy), (cx + math.cos(a) * 720, cy + math.sin(a) * 720)], fill=(140, 190, 240), width=4)
    return img
def _grid(theme, t): return background(theme, t)
PATTERNS = {'grid': _grid, 'iso': _iso, 'graph': _graph, 'plan': _plan, 'protractor': _protractor}
VARIANTS = [f'{p}/{c}' for p in PATTERNS for c in ('bp', 'dark')]
def bg(t, variant='grid/bp'):
    if '/' not in variant: variant = 'grid/' + variant
    p, c = variant.split('/'); return PATTERNS[p](c, t)
