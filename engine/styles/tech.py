import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine.core import W, H, font, clamp, prog, eo, eio, back, lerp, paste_alpha, tx, rect, chip, reg
BGC = (9, 12, 22); PANEL = (20, 26, 42); LINE = (36, 46, 70)
OR = (255, 112, 40); CY = (70, 205, 255); WH = (240, 244, 250); MU = (120, 132, 156); RD = (255, 70, 80); GN = (60, 220, 140); SILVER = (178, 186, 198)
def mono(s): return font('mono', s, 'Bold')
def xb(s): return font('bv', s, 'ExtraBold')
def bv(s, w='Bold'): return font('bv', s, w)
def layer(w, h): 
    L = Image.new('RGBA', (int(w * 2), int(h * 2)), (0, 0, 0, 0)); return L, ImageDraw.Draw(L)
def put(img, L, cx, cy, alpha=1.0, scale=1.0, rot=0):
    if alpha <= 0 or scale <= .01: return
    L = L.resize((max(1, int(L.size[0] / 2 * scale)), max(1, int(L.size[1] / 2 * scale))), Image.LANCZOS)
    if rot: L = L.rotate(rot, resample=Image.BICUBIC, expand=True)
    paste_alpha(img, L, cx - L.size[0] / 2, cy - L.size[1] / 2, alpha)

def xmark(img, cx, cy, s, k):
    if k <= 0: return
    L, d = layer(s, s)
    a = eio(clamp(k * 2)); b = eio(clamp(k * 2 - 1))
    d.line([(20, 20), (20 + (s * 2 - 40) * a, 20 + (s * 2 - 40) * a)], fill=RD + (255,), width=int(s * .16))
    if b > 0: d.line([(s * 2 - 20, 20), (s * 2 - 20 - (s * 2 - 40) * b, 20 + (s * 2 - 40) * b)], fill=RD + (255,), width=int(s * .16))
    put(img, L, cx, cy)

def ic_card(w=300, h=190, col=CY, label='VISA'):
    L, d = layer(w, h)
    d.rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=36, fill=PANEL + (255,), outline=col + (255,), width=8)
    d.rounded_rectangle((44, 120, 140, 196), radius=14, fill=(210, 180, 90, 255))
    for i in range(4): d.rounded_rectangle((44 + i * 120, 260, 140 + i * 120, 290), radius=10, fill=MU + (255,))
    return L
def ic_bank(s=220, col=CY):
    L, d = layer(s, s); S = s * 2
    d.polygon([(S * .5, S * .06), (S * .95, S * .3), (S * .05, S * .3)], fill=col + (255,))
    for i in range(4):
        x = S * (.16 + i * .23); d.rectangle((x, S * .36, x + S * .1, S * .8), fill=col + (255,))
    d.rectangle((S * .05, S * .84, S * .95, S * .94), fill=col + (255,))
    return L
def ic_person(s=60, col=MU):
    L, d = layer(s, s * 1.4); S = s * 2
    d.ellipse((S * .3, 0, S * .7, S * .4), fill=col + (255,))
    d.rounded_rectangle((S * .12, S * .48, S * .88, S * 1.4), radius=int(S * .3), fill=col + (255,))
    return L
def ic_wallet(s=240):
    L, d = layer(s, s * .78); S = s * 2
    d.rounded_rectangle((0, S * .08, S, S * .78), radius=40, fill=PANEL + (255,), outline=OR + (255,), width=10)
    d.rounded_rectangle((S * .62, S * .3, S, S * .56), radius=20, fill=OR + (255,))
    d.ellipse((S * .7, S * .38, S * .78, S * .46), fill=PANEL + (255,))
    return L
def ic_controller(s=260, col=WH):
    L, d = layer(s, s * .62); S = s * 2
    d.rounded_rectangle((S * .06, S * .08, S * .94, S * .6), radius=int(S * .26), fill=col + (255,))
    d.rectangle((S * .2, S * .3, S * .36, S * .36), fill=BGC + (255,)); d.rectangle((S * .25, S * .25, S * .31, S * .41), fill=BGC + (255,))
    for (x, y) in [(.68, .26), (.76, .34), (.6, .34), (.68, .42)]:
        d.ellipse((S * x - 12, S * y - 12, S * x + 12, S * y + 12), fill=BGC + (255,))
    return L
def ic_shop(w, h, sign, col, awn):
    L, d = layer(w, h); Wd, Hd = w * 2, h * 2
    d.rectangle((20, Hd * .3, Wd - 20, Hd - 4), fill=PANEL + (255,))
    for i in range(8):
        x0 = Wd * i / 8
        d.rectangle((x0, Hd * .2, x0 + Wd / 8, Hd * .34), fill=(awn if i % 2 else WH) + (255,))
        d.pieslice((x0, Hd * .29, x0 + Wd / 8, Hd * .39), 0, 180, fill=(awn if i % 2 else WH) + (255,))
    d.rounded_rectangle((Wd * .12, 0, Wd * .88, Hd * .16), radius=18, fill=col + (255,))
    f = xb(int(Hd * .1)); d.text((Wd / 2, Hd * .08), sign, font=f, fill=BGC + (255,), anchor='mm')
    d.rectangle((Wd * .1, Hd * .48, Wd * .45, Hd - 4), fill=(32, 40, 62, 255))
    d.rectangle((Wd * .55, Hd * .48, Wd * .9, Hd * .78), fill=(255, 220, 140, 255) if col == OR else (120, 220, 255, 255))
    return L
def ic_note(w=360, h=170):
    L, d = layer(w, h); Wd, Hd = w * 2, h * 2
    d.rounded_rectangle((0, 0, Wd - 1, Hd - 1), radius=20, fill=(110, 170, 140, 255))
    d.rounded_rectangle((16, 16, Wd - 17, Hd - 17), radius=14, outline=(70, 120, 95, 255), width=6)
    d.ellipse((Wd * .62, Hd * .2, Wd * .9, Hd * .8), fill=(140, 195, 165, 255))
    d.text((Wd * .3, Hd * .5), '10.000', font=xb(int(Hd * .3)), fill=(40, 80, 60, 255), anchor='mm')
    return L

# icosphere-ish wireframe
PHI = (1 + 5 ** .5) / 2
V0 = np.array([(-1, PHI, 0), (1, PHI, 0), (-1, -PHI, 0), (1, -PHI, 0), (0, -1, PHI), (0, 1, PHI), (0, -1, -PHI), (0, 1, -PHI),
               (PHI, 0, -1), (PHI, 0, 1), (-PHI, 0, -1), (-PHI, 0, 1)], float)
F0 = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
      (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
def subdiv(V, F):
    V = [tuple(v) for v in V]; cache = {}; NF = []
    def mid(a, b):
        k = (min(a, b), max(a, b))
        if k not in cache:
            m = (np.array(V[a]) + np.array(V[b])) / 2; V.append(tuple(m)); cache[k] = len(V) - 1
        return cache[k]
    for a, b, c in F:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a); NF += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    return np.array(V), NF
MESH = [(V0, F0)]
for _ in range(2): MESH.append(subdiv(*MESH[-1]))
MESH = [(V / np.linalg.norm(V, axis=1)[:, None], F) for V, F in MESH]
def sphere(img, cx, cy, r, t, level, alpha=1.0, col=CY):
    V, F = MESH[level]
    a, b = t * .8, .4
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    P = V @ Ry.T @ Rx.T
    L, d = layer(r * 2.2, r * 2.2); c = r * 2.2
    edges = set()
    for f in F:
        for i in range(3):
            e = (min(f[i], f[(i + 1) % 3]), max(f[i], f[(i + 1) % 3])); edges.add(e)
    for i, j in edges:
        z = (P[i, 2] + P[j, 2]) / 2
        a_ = int(255 * (.25 + .75 * (z + 1) / 2))
        d.line([(c + P[i, 0] * r * 2, c - P[i, 1] * r * 2), (c + P[j, 0] * r * 2, c - P[j, 1] * r * 2)], fill=col + (a_,), width=3)
    put(img, L, cx, cy, alpha)

# ---------- backgrounds ----------
yy, xx = np.mgrid[0:H, 0:W]
vg = np.clip(1 - .55 * (((xx - W / 2) / (W * .7)) ** 2 + ((yy - H * .42) / (H * .7)) ** 2), .35, 1)
base = np.array(BGC, np.float32)[None, None, :] * (0.7 + 0.6 * vg[..., None])
glow = np.exp(-(((xx - W * .5) / 520) ** 2 + ((yy - 760) / 620) ** 2))[..., None] * np.array([18, 28, 58], np.float32)
BG = Image.fromarray(np.clip(base + glow, 0, 255).astype(np.uint8))
GRID = Image.new('RGBA', (W, H + 120), (0, 0, 0, 0)); gd = ImageDraw.Draw(GRID)
for x in range(0, W + 1, 120): gd.line([(x, 0), (x, H + 120)], fill=LINE + (70,), width=1)
for y in range(0, H + 121, 120): gd.line([(0, y), (W, y)], fill=LINE + (70,), width=1)
BGUP = BG.crop((0, 110, W, H)).resize((W, H - 110)); _b = BG.copy(); _b.paste(BGUP, (0, 0)); BGUP = _b
VIG = Image.fromarray((np.clip(vg * 1.25, 0, 1) * 255).astype(np.uint8)).convert('RGB')
GR = np.random.default_rng(2)
GRAIN = [Image.fromarray(np.clip(128 + GR.normal(0, 9, (H, W)), 0, 255).astype(np.uint8)).convert('RGB') for _ in range(3)]


FLOW = [np.random.default_rng(i) for i in range(1)]
def background(t, theme=None):
    """navy gradient + drifting grid + slow-moving glow blobs (always moving)"""
    img = BG.copy()
    gy = int((t * 40) % 120); g = GRID.crop((0, gy, W, gy + H)); img.paste(g, (0, 0), g)
    L = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for i, col in enumerate([CY, OR, (120, 80, 255)]):
        cx = W / 8 + W / 8 * math.sin(t * .35 + i * 2.1); cy = H / 8 + H / 9 * math.cos(t * .27 + i * 1.7)
        d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=col + (40,))
    L = L.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR); img.paste(L, (0, 0), L)
    return img
def transition(img, t, dt, theme=None):
    """RGB-split glitch"""
    if dt >= .22: return img
    k = 1 - dt / .22; arr = np.asarray(img).copy(); s = int(30 * k)
    arr[..., 0] = np.roll(arr[..., 0], s, axis=1); arr[..., 2] = np.roll(arr[..., 2], -s, axis=1)
    rg = np.random.default_rng(int(t * 100))
    for _ in range(int(8 * k)):
        y0 = rg.integers(0, H - 80); hh = rg.integers(10, 80)
        arr[y0:y0 + hh] = np.roll(arr[y0:y0 + hh], rg.integers(-80, 80), axis=1)
    return Image.fromarray(arr)
def bg(t, theme=None): return background(t)

# ---------- per-scene background variants (same palette) ----------
_rg = np.random.default_rng(21)
_NODES = [(_rg.uniform(0, W), _rg.uniform(0, H), _rg.uniform(-30, 30), _rg.uniform(-30, 30)) for _ in range(46)]
_COLS = []
for i in range(22):
    L = Image.new('RGBA', (48, H * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(L); r = np.random.default_rng(i)
    for y in range(0, H * 2, 44):
        d.text((6, y), str(r.integers(0, 2)) if r.random() < .7 else chr(int(r.integers(65, 90))), font=font('mono', 34), fill=CY + (int(r.uniform(25, 90)),))
    _COLS.append((L, _rg.uniform(60, 220), i * 50 + 10))
def _v_network(t):
    img = BG.copy(); d = ImageDraw.Draw(img); pts = []
    for x, y, vx, vy in _NODES:
        px_ = (x + vx * t) % W; py_ = (y + vy * t) % H; pts.append((px_, py_))
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dd = math.dist(pts[i], pts[j])
            if dd < 230: d.line([pts[i], pts[j]], fill=tuple(int(c * (1 - dd / 230) * .5 + b * (1 - (1 - dd / 230) * .5)) for c, b in zip(CY, BGC)), width=2)
    for p in pts: d.ellipse((p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), fill=CY)
    return img
def _v_rain(t):
    img = BG.copy()
    for L, sp, x in _COLS:
        o = int((t * sp) % H); c = L.crop((0, H - o, 48, H * 2 - o)); img.paste(c, (x, 0), c)
    return img
def _v_rings(t):
    img = BG.copy(); d = ImageDraw.Draw(img); cx, cy = W / 2, 760
    for i, r in enumerate((180, 300, 430, 560, 700)):
        rot = t * (12 if i % 2 else -9) * (1 + i * .2)
        for k in range(0, 360, 12):
            a0 = k + rot
            d.arc((cx - r, cy - r, cx + r, cy + r), a0, a0 + 7, fill=LINE if i % 2 else (40, 70, 110), width=4)
    a = math.radians(t * 70)
    d.line([(cx, cy), (cx + math.cos(a) * 700, cy + math.sin(a) * 700)], fill=(50, 110, 160), width=3)
    return img
def _v_bars(t):
    img = BG.copy(); d = ImageDraw.Draw(img); n = 18; bw = W / n
    for i in range(n):
        h = 260 + 220 * (0.5 + 0.5 * math.sin(t * 2.3 + i * .7)) * (0.6 + 0.4 * math.sin(t * .7 + i))
        d.rectangle((i * bw + 6, H - h, (i + 1) * bw - 6, H), fill=(26, 40, 66))
        d.rectangle((i * bw + 6, H - h, (i + 1) * bw - 6, H - h + 8), fill=OR if i % 3 == 0 else CY)
    for i in range(n):
        h = 200 + 160 * (0.5 + 0.5 * math.sin(t * 1.9 + i * .9))
        d.rectangle((i * bw + 6, 0, (i + 1) * bw - 6, h * .45), fill=(18, 28, 48))
    return img
VARIANTS = {'grid': lambda t: background(t), 'network': _v_network, 'rain': _v_rain, 'rings': _v_rings, 'bars': _v_bars}
def bg(t, variant='grid'): return VARIANTS[variant](t)
