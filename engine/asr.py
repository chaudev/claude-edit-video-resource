"""Vietnamese speech -> word timestamps.  python3 -m engine.asr voice.mp3 [words.json]
Prints a compact transcript: one line per VAD segment with its start time."""
import sys, json, wave, subprocess, unicodedata
from pathlib import Path
import numpy as np
KIT = Path(__file__).resolve().parents[1]

def transcribe(audio, out='words.json'):
    import sherpa_onnx
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', audio, '-ac', '1', '-ar', '16000', '/tmp/_asr.wav'], check=True)
    d = KIT / 'models' / 'vi'
    enc = next(d.glob('encoder*.onnx')); dec = next(d.glob('decoder*.onnx')); joi = next(d.glob('joiner*.onnx'))
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=str(enc), decoder=str(dec), joiner=str(joi), tokens=str(d / 'tokens.txt'),
                                                        num_threads=2, decoding_method='modified_beam_search')
    w = wave.open('/tmp/_asr.wav'); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = str(KIT / 'models' / 'silero_vad.onnx')
    cfg.silero_vad.min_silence_duration = 0.3; cfg.silero_vad.max_speech_duration = 12; cfg.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=120)
    for i in range(0, len(x), cfg.silero_vad.window_size): vad.accept_waveform(x[i:i + cfg.silero_vad.window_size])
    vad.flush(); words = []; lines = []
    while not vad.empty():
        s = vad.front; off = s.start / 16000
        st = rec.create_stream(); st.accept_waveform(16000, s.samples); rec.decode_stream(st)
        r = st.result; seg = []
        for tk, tm in zip(r.tokens, r.timestamps):
            if tk.startswith(' ') or not seg: seg.append({'w': tk.strip(), 't': round(off + tm, 2)})
            else: seg[-1]['w'] += tk
        if seg:
            lines.append(f"[{seg[0]['t']:5.1f}] " + ' '.join(o['w'] for o in seg)); words += seg
        vad.pop()
    json.dump(words, open(out, 'w'), ensure_ascii=False)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio], capture_output=True, text=True).stdout)
    print(f'duration {dur:.2f}s, {len(words)} words'); print('\n'.join(lines))
    return words

def _norm(s):
    s = unicodedata.normalize('NFD', s.upper()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('Đ', 'D')

class Cues:
    """cue('BỊ CHẶN') -> start time of that phrase (accent-insensitive). n = which occurrence. after = search after this time."""
    def __init__(self, path='words.json'):
        self.w = json.load(open(path)); self.n = [_norm(o['w']) for o in self.w]
    def __call__(self, phrase, n=0, after=0.0, end=False):
        p = _norm(phrase).split(); hits = []
        for i in range(len(self.n) - len(p) + 1):
            if self.n[i:i + len(p)] == p and self.w[i]['t'] >= after: hits.append(i)
        if len(hits) <= n: raise KeyError(f'cue not found: {phrase} (#{n})')
        i = hits[n] + (len(p) - 1 if end else 0)
        return self.w[i]['t']
    def last(self): return self.w[-1]['t']

if __name__ == '__main__':
    transcribe(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'words.json')
