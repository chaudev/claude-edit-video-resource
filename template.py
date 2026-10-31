"""TEMPLATE for one video. Copy to /tmp/v.py, edit VOICE + scenes + SFX. Run from repo root:
  python3 /tmp/v.py check            -> must print only 'check done'
  python3 /tmp/v.py sheet 1,5,9,.. /tmp/s.png   (view ONE small sheet)
  python3 /tmp/v.py seg 0 25 /tmp/a.mp4 ; seg 25 50 /tmp/b.mp4 ...  (~25s per call)
  python3 /tmp/v.py finish /mnt/user-data/outputs/name.mp4 /tmp/a.mp4 /tmp/b.mp4
"""
import sys; sys.path.insert(0, '.')
from engine.core import *
from engine.asr import Cues
from engine.styles import poster as S          # poster | blueprint | arcade | tech  (pick a NEW one each video)

VOICE = '/mnt/user-data/uploads/voice.mp3'
c = Cues('words.json')                          # c('bị chặn') -> seconds ; c('ấn độ', 1) second occurrence
DUR = c.last() + 2.0                            # hold the CTA ~2s after the voice ends

def s_hook(img, t, t0):
    a, s = pop(t, 0)
    tx(img, 'HOOK TEXT', S.an(150), 540, 600, S.YEL, a, scale=s)
    punch(img, 'BOOM', S.an(200), 540, 900, S.CREAM, t, c('chặn'))

def s_cta(img, t, t0):
    k, dy = ap(t, t0)
    tx(img, 'Thích chuyện kiểu này?', S.xb(56), 540, 330, S.CREAM, k, dy=dy)
    logo_cta(img, t, t0 + .2, S.an(100), S.CREAM, S.CREAM, S.an(70), S.INK, S.YEL, c('theo dõi'))

SCENES = [(0, s_hook), (c('thích'), s_cta)]
# every scene gets its OWN moving background variant of the style (never same as previous scene). Override with a list if needed.
BGV = assign_variants(len(SCENES), S.VARIANTS, seed=7)
video = Video(SCENES, lambda t, si: S.bg(t, BGV[si]), DUR, VOICE,
              transition=lambda img, t, dt, si: S.transition(img, t, dt, BGV[si]),
              shakes=[(c('chặn'), 26, .5)])
SFX = [(0, 'riser', .4), (c('chặn') - .03, 'impact', .85)] + [(a - .05, 'swipe', .4) for a, _ in SCENES[1:]]
if __name__ == '__main__': main(video, SFX)
