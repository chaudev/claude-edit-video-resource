import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine.core import W, H, font, clamp, prog, eo, eio, back, lerp, paste_alpha, tx, rect, chip, reg
BG = (16, 6, 36); PINK = (255, 64, 180); CY = (60, 230, 255); YEL = (255, 220, 60); RED = (255, 60, 70); WH = (245, 240, 255); GRN = (80, 255, 120); MUT = (160, 130, 210)
SHADOW = (8, 2, 20)   # pass shadow=SHADOW to tx for arcade drop shadow
def px(s): return font('pixel', s)
def bg_(s): return font('bungee', s)
# ---------- synthwave background ----------
HZ = 1420
yy, xx = np.mgrid[0:H, 0:W]
sky = np.zeros((H, W, 3), np.float32)
g = np.clip(yy / HZ, 0, 1)[..., None]
sky += np.array(BG, np.float32) * (1 - g) + np.array((70, 14, 90), np.float32) * g
sky[HZ:] = np.array((10, 3, 24), np.float32)
SKY = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8))
SUN = Image.new('RGBA', (700, 700), (0, 0, 0, 0)); sd = ImageDraw.Draw(SUN)
for y in range(0, 350):
    c = (int(lerp(255, 255, y / 350)), int(lerp(220, 60, y / 350)), int(lerp(60, 150, y / 350)))
    half = math.sqrt(max(0, 350 ** 2 - (350 - y) ** 2))
    stripe = y > 170 and int((y - 170) / 18) % 2 == 1 and (y - 170) % 18 < 4 + (y - 170) / 18
    if not stripe: sd.line([(350 - half, y), (350 + half, y)], fill=c + (58,))
SUNG = Image.new('RGBA', (1100, 1100), (0, 0, 0, 0)); ImageDraw.Draw(SUNG).ellipse((250, 250, 850, 850), fill=PINK + (38,))
SUNG = SUNG.filter(ImageFilter.GaussianBlur(90))
SR = np.random.default_rng(3)
STARS = [(SR.uniform(0, W), SR.uniform(0, HZ - 250), SR.uniform(1.5, 3.5), SR.uniform(0, 6.3)) for _ in range(90)]
SCAN = Image.new('RGBA', (W, H), (0, 0, 0, 0)); scd = ImageDraw.Draw(SCAN)
for y in range(0, H, 4): scd.line([(0, y), (W, y)], fill=(0, 0, 0, 38))

def background(t, flash=0):
    img = SKY.copy(); d = ImageDraw.Draw(img)
    for x, y, r, ph in STARS:
        b = .5 + .5 * math.sin(t * 2.5 + ph)
        c = int(120 + 135 * b); d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c, 255))
    img.paste(SUNG, (W // 2 - 550, HZ - 400 - 550 + 100), SUNG)
    sun = SUN.crop((0, 0, 700, 350))
    yo = HZ - 350 + int(6 * math.sin(t * .8))
    img.paste(sun, (W // 2 - 350, yo), sun)
    d.rectangle((0, HZ, W, H), fill=(10, 3, 24))
    # perspective floor
    sp = (t * 0.9) % 1
    for i in range(16):
        z = (i + 1 - sp) / 16
        y = HZ + (H - HZ) * (z ** 2.2)
        a = int(80 + 175 * z)
        d.line([(0, y), (W, y)], fill=(min(255, a), 40, min(255, 120 + a // 2)), width=2 + int(3 * z))
    for k in range(-12, 13):
        x_far = W / 2 + k * 40; x_near = W / 2 + k * 260
        d.line([(x_far, HZ), (x_near, H)], fill=(200, 50, 200), width=3)
    d.line([(0, HZ), (W, HZ)], fill=PINK, width=4)
    img.paste(SCAN, (0, 0), SCAN)
    roll = int((t * 180) % (H + 300)) - 150
    band = Image.new('RGBA', (W, 120), (255, 255, 255, 12)); img.paste(band, (0, roll), band)
    return img


def hpbar(img, label, value, alpha=1, y=205):
    """fighting-game health bar at top; value 0..1"""
    if alpha <= 0: return
    tx(img, label, px(56), 190, y, WH, alpha, group=('hud',))
    rect(img, (300, y - 19, 1000, y + 21), (40, 20, 70), r=4, alpha=alpha, group=('hud',))
    col = GRN if value > .5 else (YEL if value > .25 else RED)
    if value * 690 > 2: rect(img, (305, y - 14, 305 + 690 * value, y + 16), col, r=3, alpha=alpha, group=('hud',))
    rect(img, (300, y - 19, 1000, y + 21), None, r=4, outline=WH, width=3, alpha=alpha, group=('hud',))
def transition(img, t, dt, theme=None):
    """pixel dissolve flash"""
    if dt >= .25: return img
    k = dt / .25; arr = np.asarray(img).copy(); blk = 24
    rg = np.random.default_rng(int(t * 1000) % 99999)
    m = np.kron(rg.random((H // blk, W // blk)) > k, np.ones((blk, blk), bool))[:H, :W]
    arr[m] = (arr[m] * .25 + np.array(PINK) * .35).astype(np.uint8)
    return Image.fromarray(arr)
def bg(t, theme=None): return background(t)

# ---------- per-scene background variants: synth | warp | tunnel | tetris | clouds ----------
_SR = np.random.default_rng(5)
_WARP = [(_SR.uniform(-1, 1), _SR.uniform(-1, 1), _SR.uniform(0, 1)) for _ in range(220)]
def _warp(t):
    img = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(img); cx, cy = W / 2, 760
    for x, y, z0 in _WARP:
        z = 1 - ((z0 + t * .35) % 1); z2 = min(1, z + .04)
        sx, sy = cx + x / z * 260, cy + y / z * 260; ex, ey = cx + x / z2 * 260, cy + y / z2 * 260
        b = int(255 * (1 - z)); d.line([(ex, ey), (sx, sy)], fill=(b, min(255, b // 2 + 60), 255), width=1 + int(3 * (1 - z)))
    img.paste(SCAN, (0, 0), SCAN); return img
def _tunnel(t):
    img = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(img); cx, cy = W / 2, 760
    for i in range(14):
        z = ((i - t * 2.2) % 14) / 14; s = 40 + 1500 * z ** 2.2
        col = PINK if i % 2 else CY; a = (.25 + .75 * z) * .55
        d.rectangle((cx - s * .56, cy - s, cx + s * .56, cy + s), outline=tuple(int(c * a + b * (1 - a)) for c, b in zip(col, BG)), width=3 + int(5 * z))
    img.paste(SCAN, (0, 0), SCAN); return img
_TET = [(_SR.integers(0, 12), _SR.uniform(40, 120), _SR.uniform(0, H), [PINK, CY, YEL, GRN][i % 4]) for i in range(26)]
def _tetris(t):
    img = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(img)
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(40, 16, 70), width=2)
    for col, sp, y0, c in _TET:
        y = (y0 + t * sp) % (H + 180) - 180; x = col * 90
        for k in range(3): d.rectangle((x + 4, y + k * 60 + 4, x + 86, y + k * 60 + 56), fill=tuple(int(v * .22) for v in c))
    img.paste(SCAN, (0, 0), SCAN); return img
_CL = [(_SR.uniform(0, W), _SR.uniform(150, 1700), _SR.uniform(20, 70), _SR.uniform(.6, 1.6)) for _ in range(12)]
def _clouds(t):
    img = SKY.copy(); d = ImageDraw.Draw(img)
    for x0, y, sp, s in _CL:
        x = (x0 + t * sp) % (W + 400) - 200
        for k, (dx, dy, r) in enumerate([(0, 0, 60), (60, -20, 70), (130, 0, 55), (60, 25, 60)]):
            px_ = int((x + dx * s) / 12) * 12; py_ = int((y + dy * s) / 12) * 12; rr = r * s
            d.rectangle((px_ - rr, py_ - rr * .6, px_ + rr, py_ + rr * .6), fill=(70, 30, 110))
    img.paste(SCAN, (0, 0), SCAN); return img
VARIANTS = {'synth': lambda t: background(t), 'warp': _warp, 'tunnel': _tunnel, 'tetris': _tetris, 'clouds': _clouds}
def bg(t, variant='synth'): return VARIANTS[variant](t)
