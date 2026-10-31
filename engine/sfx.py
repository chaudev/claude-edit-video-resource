import numpy as np
SR = 44100
rng = np.random.default_rng(0)

def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
    return e

def lowpass(x, k):
    # one-pole lowpass, k in (0,1): smaller = darker
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += k * (x[i] - acc); y[i] = acc
    return y

def bandsweep(n, f0, f1):
    # cheap swept band: noise lowpassed with moving cutoff via chunks
    x = rng.normal(0, 1, n); out = np.zeros(n); acc = 0.0; acc2 = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n
        k = min(0.99, 2 * np.pi * f / SR)
        acc += k * (x[i] - acc); acc2 += k * (acc - acc2)
        out[i] = acc - acc2 * 0.6
    return out

def whoosh(dur=0.45, up=True):
    n = int(dur * SR); t = np.arange(n) / n
    s = bandsweep(n, 300 if up else 2500, 2500 if up else 300)
    e = np.sin(np.pi * t) ** 1.5
    return norm(s * e) * 0.55

def pop(f0=900, f1=280, dur=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.02)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return norm(np.sin(ph) * env(n, 0.001, 0.035)) * 0.6

def thud(dur=0.45):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 55 + 70 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.12)
    clk = lowpass(rng.normal(0, 1, n), 0.25) * env(n, 0.0005, 0.018)
    return norm(body + 0.8 * clk) * 0.85

def impact(dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 38 + 90 * np.exp(-t / 0.08)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.35)
    nz = lowpass(rng.normal(0, 1, n), 0.08) * env(n, 0.001, 0.25)
    return norm(sub + 0.9 * nz) * 0.95

def ding(f=1318.5, dur=0.9):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * m * t) for m, a in [(1, 1), (2.01, .35), (3.02, .15)])
    return norm(s * env(n, 0.002, 0.28)) * 0.4

def tick():
    n = int(0.03 * SR)
    return norm(lowpass(rng.normal(0, 1, n), 0.5) * env(n, 0.0005, 0.006)) * 0.35

def typing(dur, rate=14):
    n = int(dur * SR); out = np.zeros(n)
    k = 0.0
    while k < dur - 0.03:
        i = int(k * SR); tk = tick() * rng.uniform(.6, 1)
        out[i:i + len(tk)] += tk[:n - i]; k += 1 / rate * rng.uniform(.7, 1.3)
    return out

def riser(dur=1.4):
    n = int(dur * SR); t = np.arange(n) / n
    s = bandsweep(n, 200, 4000) * 0.6
    f = 180 + 900 * t ** 2
    s += 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    return norm(s * t ** 2) * 0.5

def swipe():
    return whoosh(0.28, True) * 0.8

def scratch(dur=0.35):
    n = int(dur * SR); t = np.arange(n) / n
    s = bandsweep(n, 3000, 900) * (1 + 0.6 * np.sin(2 * np.pi * 22 * t * dur))
    return norm(s * np.sin(np.pi * t)) * 0.4

def norm(x):
    m = np.max(np.abs(x)) + 1e-9
    return x / m

LIB = {'whoosh': lambda: whoosh(), 'whoosh_s': lambda: whoosh(0.3), 'pop': lambda: pop(), 'pop_hi': lambda: pop(1400, 500, .1),
       'thud': lambda: thud(), 'impact': lambda: impact(), 'ding': lambda: ding(), 'ding_lo': lambda: ding(987.8),
       'riser': lambda: riser(), 'swipe': lambda: swipe(), 'scratch': lambda: scratch()}

def build(events, dur, out_wav):
    import wave
    n = int(dur * SR); track = np.zeros(n)
    cache = {}
    for item in events:
        t, name, gain = item[0], item[1], item[2]
        if name == 'typing':
            s = typing(item[3])
        else:
            if name not in cache: cache[name] = LIB[name]()
            s = cache[name]
        i = int(t * SR)
        if i >= n: continue
        m = min(len(s), n - i); track[i:i + m] += s[:m] * gain
    track = np.clip(track, -1, 1)
    st = np.stack([track, track], 1)
    with wave.open(out_wav, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

LIB['whoosh_dn'] = lambda: whoosh(0.5, False)
LIB['blip'] = lambda: pop(1600, 1250, .09)
LIB['power'] = lambda: ding(880, .5) * .6 + ding(1318.5, .5)[:int(.5 * SR)] * .6
# names: whoosh whoosh_s whoosh_dn swipe pop pop_hi blip thud impact ding ding_lo power riser scratch ; ('typing', gain, dur)
