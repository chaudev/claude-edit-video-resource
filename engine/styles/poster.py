import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine.core import W, H, font, clamp, prog, eo, eio, back, lerp, paste_alpha, tx, rect, chip, reg
PAPER = (243, 236, 222); INK = (22, 20, 20); RED = (214, 38, 30); YEL = (255, 204, 0); CREAM = (250, 244, 232); GREY = (140, 130, 118)
def an(s): return font('anton', s)
def xb(s): return font('bv', s, 'ExtraBold')
# ---------- moving backgrounds ----------
THEMES = {'red': (RED, (190, 28, 22), YEL), 'paper': (PAPER, (226, 214, 194), RED), 'ink': (INK, (44, 40, 38), YEL), 'yel': (YEL, (238, 186, 0), RED)}
def make_rays(col):
    S = 1100; L = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for i in range(24):
        if i % 2: continue
        d.pieslice((0, 0, S - 1, S - 1), i * 15, i * 15 + 15, fill=col + (70,))
    return L
def make_dots(col):
    L = Image.new('RGBA', (W + 60, H + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for y in range(0, H + 60, 30):
        for x in range(0, W + 60, 30):
            r = 3 + 2.5 * math.sin(x * .01 + y * .006) ** 2
            d.ellipse((x - r, y - r, x + r, y + r), fill=col + (90,))
    return L
def make_marq(col, text):
    f = an(260); w = int(f.getlength(text + '  ·  ')) 
    L = Image.new('RGBA', (w * 2 + 10, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for k in range(2):
        d.text((k * w, 0), text + '  ·  ', font=f, fill=(0, 0, 0, 0), stroke_width=3, stroke_fill=col + (110,))
    return L, w
BGS = {}
for k, (base, sec, acc) in THEMES.items():
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - .18 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2
    arr = np.clip(np.array(base, np.float32)[None, None] * v[..., None], 0, 255).astype(np.uint8)
    BGS[k] = dict(base=Image.fromarray(arr), rays=make_rays(sec), dots=make_dots(sec),
                  marq=make_marq(sec, 'NGƯỜI VIỆT LÀM GAME'), marq2=make_marq(sec, 'CHUYỆN ÍT AI BIẾT'))
def background(theme, t):
    B = BGS[theme]; img = B['base'].copy()
    r = B['rays'].rotate(t * 9, resample=Image.BILINEAR).resize((2300, 2300), Image.BILINEAR)
    img.paste(r, (W // 2 - 1150, 760 - 1150), r)
    o = int(t * 28) % 30
    d = B['dots'].crop((o, o, o + W, o + H)); img.paste(d, (0, 0), d)
    for (L, w), y, sp in [(B['marq'], -90, 90), (B['marq2'], 1640, -70)]:
        off = int((t * sp) % w)
        c = L.crop((off, 0, off + W, 330)) if sp > 0 else L.crop((w - off, 0, w - off + W, 330))
        img.paste(c, (0, y), c)
    return img


def transition(img, t, dt, theme):
    """diagonal accent band sweep (first .3s of a scene)"""
    if dt >= .3: return img
    k = eio(dt / .3); acc = THEMES[theme][2]; x = lerp(-900, W + 900, k)
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(L).polygon([(x - 300, 0), (x + 200, 0), (x - 200, H), (x - 700, H)], fill=acc + (255,))
    img.paste(L, (0, 0), L); return img
def bg(t, theme='red'):
    """themes: red | paper | ink | yel"""
    return background(theme, t)

# ---------- per-scene background variants: 'pattern/color' e.g. 'stripes/paper' ----------
# patterns: rays (default) | stripes | circles | halftone | blocks ; colors: red | paper | ink | yel
_STRIPE = {}
def _stripes(theme, t):
    B = BGS[theme]; img = B['base'].copy(); sec = THEMES[theme][1]
    if theme not in _STRIPE:
        L = Image.new('RGBA', (W + 400, H + 400), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        for x in range(-H, W + 800, 120): d.polygon([(x, 0), (x + 60, 0), (x + 60 + H + 400, H + 400), (x + H + 400, H + 400)], fill=sec + (120,))
        _STRIPE[theme] = L
    o = int(t * 60) % 120; c = _STRIPE[theme].crop((o, 0, o + W, H)); img.paste(c, (0, 0), c); return img
def _circles(theme, t):
    B = BGS[theme]; img = B['base'].copy(); sec = THEMES[theme][1]; d = ImageDraw.Draw(img)
    for i in range(14):
        r = ((t * 90 + i * 120) % 1680)
        d.ellipse((540 - r, 760 - r, 540 + r, 760 + r), outline=sec, width=34)
    return img
def _halftone(theme, t):
    B = BGS[theme]; img = B['base'].copy(); sec = THEMES[theme][1]; d = ImageDraw.Draw(img)
    for y in range(0, H + 40, 40):
        for x in range(0, W + 40, 40):
            r = 4 + 12 * (0.5 + 0.5 * math.sin(x * .006 + y * .004 - t * 1.6))
            d.ellipse((x - r, y - r, x + r, y + r), fill=sec)
    return img
def _blocks(theme, t):
    B = BGS[theme]; img = B['base'].copy(); sec = THEMES[theme][1]; acc = THEMES[theme][2]; d = ImageDraw.Draw(img)
    for i in range(9):
        y = (i * 230 + t * 80) % (H + 230) - 230; x = 60 if i % 2 else W - 380
        d.rectangle((x, y, x + 320, y + 150), fill=sec)
        d.rectangle((x + 20, y + 20, x + 80, y + 40), fill=acc)
    return img
def _rays(theme, t): return background(theme, t)
PATTERNS = {'rays': _rays, 'stripes': _stripes, 'circles': _circles, 'halftone': _halftone, 'blocks': _blocks}
VARIANTS = [f'{p}/{c}' for p in PATTERNS for c in THEMES]
def bg(t, variant='rays/red'):
    if '/' not in variant: variant = 'rays/' + variant
    p, c = variant.split('/'); return PATTERNS[p](c, t)
def transition(img, t, dt, variant='rays/red'):
    theme = variant.split('/')[-1]
    if dt >= .3: return img
    k = eio(dt / .3); acc = THEMES[theme][2]; x = lerp(-900, W + 900, k)
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(L).polygon([(x - 300, 0), (x + 200, 0), (x - 200, H), (x - 700, H)], fill=acc + (255,))
    img.paste(L, (0, 0), L); return img
