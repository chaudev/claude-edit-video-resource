"""Core of the video kit. A video script defines SCENES = [(start_time, fn), ...] where fn(img, t, t0) draws,
plus background(t, scene_index) and calls core.main(...). See template.py."""
import sys, math, json, subprocess, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

KIT = Path(__file__).resolve().parents[1]
W, H, FPS = 1080, 1920, 30
SAFE = (80, 170, W - 80, 1600)          # layout guard: nothing may leave this box
LOGO_PATH = next((p for p in [KIT / 'logo-1.png', KIT / 'logo.png'] if p.exists()), None)
BGM_PATH = next((p for p in [KIT / 'nhac-nen-short.MP3', KIT / 'nhac-nen-short.mp3'] if p.exists()), None)

# ---------- fonts ----------
_fc = {}
FONTS = {'bv': 'BeVietnamPro-{w}.ttf', 'anton': 'Anton.ttf', 'mono': 'JBMono.ttf', 'hand': 'PatrickHand.ttf',
         'pixel': 'VT323.ttf', 'bungee': 'Bungee.ttf', 'lora': 'Lora.ttf', 'lorai': 'LoraItalic.ttf'}
def font(name, size, w='Bold'):
    """name: bv (w=Medium/SemiBold/Bold/ExtraBold), anton, mono (variable w), hand, pixel, bungee, lora/lorai (variable w)"""
    k = (name, size, w)
    if k not in _fc:
        fn = FONTS[name].format(w=w)
        f = ImageFont.truetype(str(KIT / 'fonts' / fn), size)
        if name in ('mono', 'lora', 'lorai'):
            try: f.set_variation_by_name(w)
            except Exception: pass
        _fc[k] = f
    return _fc[k]

# ---------- easing ----------
def clamp(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def prog(t, a, d): return clamp((t - a) / d)
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k
def ap(t, a, d=.3):
    """fade+slide-up appear: returns (alpha, dy)"""
    k = eo(prog(t, a, d)); return k, (1 - k) * 40
def pop(t, a, d=.32):
    """pop-in with overshoot: returns (alpha, scale)"""
    p = prog(t, a, d); return eo(p * 2), max(.01, back(p))

def paste_alpha(img, layer, x, y, alpha=1.0):
    if alpha <= 0: return
    if alpha < 1:
        a = layer.getchannel('A').point(lambda v: int(v * alpha)); layer = layer.copy(); layer.putalpha(a)
    img.paste(layer, (int(round(x)), int(round(y))), layer)

# ---------- layout guard registry ----------
BOXES = []
def reg(box, group, alpha=1):
    """register a solid element; elements in the same group may overlap each other"""
    if alpha > 0.5 and group is not False: BOXES.append((box, group))

def tx(img, text, f, x, y, color, alpha=1.0, scale=1.0, dy=0, group=None, rot=0, shadow=None, anchor='m'):
    """centered text (anchor='l' => x is left edge). shadow=(r,g,b) draws offset drop shadow."""
    if alpha <= 0.01: return None
    if anchor == 'l': x = x + f.getlength(text) * scale / 2
    if shadow:
        o = max(3, int(f.size * .06 * scale))
        tx(img, text, f, x + o, y + o, shadow, min(.45, alpha * .9), scale, dy, False, rot)
    bb = f.getbbox(text); pad = 30
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    L = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(L).text((pad - bb[0], pad - bb[1]), text, font=f, fill=tuple(color) + (255,))
    if scale != 1: L = L.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    if rot: L = L.rotate(rot, resample=Image.BICUBIC, expand=True)
    lw, lh = L.size; px, py = x - lw / 2, y - lh / 2 + dy
    paste_alpha(img, L, px, py, alpha)
    box = (px + pad * scale, py + pad * scale, px + lw - pad * scale, py + lh - pad * scale)
    reg(box, ('t', text) if group is None else group, alpha)
    return box

def rect(img, box, col, r=0, alpha=1.0, outline=None, width=0, group=None):
    x0, y0, x1, y1 = box
    if alpha <= 0 or x1 - x0 < 1 or y1 - y0 < 1: return
    w, h = int(x1 - x0), int(y1 - y0)
    L = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    ImageDraw.Draw(L).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=r * 2, fill=(tuple(col) + (255,)) if col else None,
                                        outline=(tuple(outline) + (255,)) if outline else None, width=width * 2)
    paste_alpha(img, L.resize((w, h), Image.LANCZOS), x0, y0, alpha)
    reg(box, ('r', box) if group is None else group, alpha)

def chip(img, text, f, x, y, fg, bgc, alpha=1.0, scale=1.0, padx=34, pady=18, group=None, rot=0, outline=None, radius=12):
    """text on a filled/outlined rounded box (pill/button/label)"""
    if alpha <= .01 or scale <= .02: return
    bb = f.getbbox(text); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + 2 * padx, th + 2 * pady
    L = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius=radius * 2, fill=(tuple(bgc) + (255,)) if bgc else None,
                        outline=(tuple(outline) + (255,)) if outline else None, width=10)
    L = L.resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(L).text((padx - bb[0], pady - bb[1]), text, font=f, fill=tuple(fg) + (255,))
    if scale != 1: L = L.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    if rot: L = L.rotate(rot, resample=Image.BICUBIC, expand=True)
    paste_alpha(img, L, x - L.size[0] / 2, y - L.size[1] / 2, alpha)
    reg((x - w * scale / 2, y - h * scale / 2, x + w * scale / 2, y + h * scale / 2), ('c', text) if group is None else group, alpha)

def strike(img, f, text, cx, cy, k, col=(230, 50, 50), thick=10):
    """animated strikethrough over centered text"""
    k = eio(k)
    if k <= 0: return
    w = f.getlength(text) + 30
    rect(img, (cx - w / 2, cy - thick / 2, cx - w / 2 + w * k + 1, cy + thick / 2), col, r=thick // 2, group=('t', text))

def punch(img, text, f, x, y, col, t, at, glow=None, group=None):
    """text slams in from large scale; scale is clamped so it never leaves the safe area"""
    p = prog(t, at - .03, .2)
    if p <= 0: return
    smax = min(2.2, (SAFE[2] - SAFE[0] - 40) / (f.getlength(text) + 1))
    s = 1 + (max(1, smax) - 1) * (1 - eo(p))
    if glow and p < 1: tx(img, text, f, x + 6, y, glow, .45 * (1 - p), scale=s, group=False)
    tx(img, text, f, x, y, col, eo(p * 2), scale=s, group=group)

def counter(t, a, d, v0, v1, fmt='{:,}'):
    """animated number string, dots as thousand separators"""
    v = v0 + (v1 - v0) * eio(prog(t, a, d))
    return fmt.format(int(round(v))).replace(',', '.')

_LOGO = None
def logo_cta(img, t, t0, name_font, name_col, ring_col, follow_font, follow_fg, follow_bg, follow_at, y_logo=680, follow_from=None):
    """channel CTA: logo pops in (wobbles), channel name, pulsing follow button"""
    global _LOGO
    if _LOGO is None: _LOGO = Image.open(LOGO_PATH).convert('RGBA')
    p = prog(t, t0, .5)
    if p > 0:
        s = back(p); sz = int(380 * s)
        ring = Image.new('RGBA', (sz + 24, sz + 24), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse((0, 0, sz + 23, sz + 23), fill=tuple(ring_col) + (255,))
        paste_alpha(ring, _LOGO.resize((sz, sz), Image.LANCZOS), 12, 12, 1)
        ring = ring.rotate(8 * math.sin(max(0, t - t0) * 2.2), resample=Image.BICUBIC)
        paste_alpha(img, ring, 540 - ring.size[0] / 2, y_logo - ring.size[1] / 2, eo(p * 2))
        reg((540 - 202, y_logo - 202, 540 + 202, y_logo + 202), ('logo',), eo(p * 2))
        tx(img, 'NGƯỜI CHƠI NET', name_font, 540, y_logo + 280, name_col, eo(p * 2))
    a, s = pop(t, follow_at)
    if a > 0:
        pulse = 1 + .06 * math.sin(max(0, t - follow_at - .2) * 8)
        chip(img, '+ THEO DÕI KÊNH', follow_font, 540, y_logo + 460, follow_fg, follow_bg, a, s * pulse, padx=60, pady=26)

def shake_offset(t, hits):
    """hits = [(time, amplitude_px, duration)] -> (dx, dy)"""
    a = 0
    for t0, amp, d in hits:
        if t0 <= t < t0 + d: a = max(a, amp * (1 - (t - t0) / d))
    return int(a * math.sin(t * 90)), int(a * math.cos(t * 77))

# ---------- frame assembly ----------
class Video:
    def __init__(self, scenes, background, duration, voice, transition=None, shakes=(), name='video'):
        """scenes: [(start, fn)] ; background(t, si) -> RGB Image ; transition(img, t, dt, si) -> img (first ~.3s of a scene)"""
        self.scenes, self.background, self.dur, self.voice = scenes, background, duration, voice
        self.transition, self.shakes, self.name = transition, list(shakes), name
    def scene_at(self, t):
        si = 0
        for j, s in enumerate(self.scenes):
            if t >= s[0]: si = j
        return si
    def frame(self, t):
        BOXES.clear()
        si = self.scene_at(t); s0, fn = self.scenes[si][0], self.scenes[si][1]
        base = self.background(t, si); img = base.copy()
        fn(img, t, s0)
        dx, dy = shake_offset(t, self.shakes)
        if dx or dy:
            im2 = base.copy(); im2.paste(img, (dx, dy)); img = im2
        if self.transition and si > 0 and t - s0 < .35: img = self.transition(img, t, t - s0, si)
        return img
    def check(self, step=.1):
        issues, seen = [], set(); t = 0.0
        while t < self.dur:
            self.frame(t); bx = list(BOXES)
            for i, (a, ga) in enumerate(bx):
                if a[0] < SAFE[0] - 1 or a[2] > SAFE[2] + 1 or a[1] < SAFE[1] or a[3] > SAFE[3]:
                    k = ('margin', ga)
                    if k not in seen: seen.add(k); issues.append((round(t, 1), 'margin', ga, tuple(int(v) for v in a)))
                for b, gb in bx[i + 1:]:
                    if ga == gb: continue
                    ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
                    k = ('ov', ga, gb)
                    if ox > 4 and oy > 4 and k not in seen: seen.add(k); issues.append((round(t, 1), 'overlap', ga, gb))
            t += step
        return issues
    def sheet(self, times, out, thumb=(270, 480), cols=6):
        ims = [self.frame(t).resize(thumb, Image.LANCZOS) for t in times]
        rows = math.ceil(len(ims) / cols)
        sh = Image.new('RGB', (cols * (thumb[0] + 6) - 6, rows * (thumb[1] + 6) - 6), (30, 30, 30))
        for k, im in enumerate(ims): sh.paste(im, ((k % cols) * (thumb[0] + 6), (k // cols) * (thumb[1] + 6)))
        sh.save(out)
    def seg(self, a, b, out):
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '21', '-preset', 'veryfast', out], stdin=subprocess.PIPE)
        for n in range(int(round(a * FPS)), int(round(b * FPS))):
            p.stdin.write(self.frame(n / FPS).tobytes())
        p.stdin.close(); p.wait(); print('seg done', a, b, p.returncode, flush=True)

def mix_audio(voice, sfx_wav, dur, out_wav, voice_db=4, music_gain=1.25, duck_ratio=3):
    """voice boosted, background music (from repo) a bit loud with gentle ducking, sfx, loudness-normalized"""
    fc = (f"[0:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={voice_db}dB,apad,asplit=2[v][vsc];"
          f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{dur},asetpts=N/SR/TB,afade=t=in:d=0.6,"
          f"afade=t=out:st={dur - 1.8}:d=1.8,volume={music_gain}[m];"
          f"[m][vsc]sidechaincompress=threshold=0.05:ratio={duck_ratio}:attack=20:release=350[md];[2:a]volume=0.75[s];"
          f"[v][md][s]amix=inputs=3:normalize=0:duration=shortest,atrim=0:{dur},loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', voice, '-stream_loop', '-1', '-i', str(BGM_PATH), '-i', sfx_wav,
                    '-filter_complex', fc, '-map', '[out]', '-ar', '44100', '-c:a', 'pcm_s16le', out_wav], check=True)

def main(video, sfx_events=None):
    """CLI: python3 myvideo.py check | sheet t1,t2,.. out.png | seg A B out.mp4 | finish out.mp4 seg1.mp4 seg2.mp4 ..."""
    cmd = sys.argv[1]
    if cmd == 'check':
        for it in video.check(): print(it)
        print('check done')
    elif cmd == 'sheet':
        video.sheet([float(x) for x in sys.argv[2].split(',')], sys.argv[3])
    elif cmd == 'seg':
        video.seg(float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
    elif cmd == 'finish':
        out, segs = sys.argv[2], sys.argv[3:]
        from engine import sfx
        sfx.build(sfx_events or [], video.dur, '/tmp/_sfx.wav')
        mix_audio(video.voice, '/tmp/_sfx.wav', video.dur, '/tmp/_mix.wav')
        Path('/tmp/_segs.txt').write_text(''.join(f"file '{os.path.abspath(s)}'\n" for s in segs))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', '/tmp/_segs.txt', '-i', '/tmp/_mix.wav',
                        '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
        print('finished', out)

def assign_variants(n, variants, seed=0):
    """one background variant per scene, never the same as the previous scene, cycling through all before repeating"""
    import random
    r = random.Random(seed); pool = []; out = []
    for i in range(n):
        if not pool: pool = list(variants); r.shuffle(pool)
        v = pool.pop()
        if out and (v == out[-1] or v.split('/')[0] == out[-1].split('/')[0]) and pool: pool.insert(0, v); v = pool.pop()
        out.append(v)
    return out
