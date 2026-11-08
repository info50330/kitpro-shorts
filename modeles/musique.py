"""Génère une musique de fond originale (libre de droits, synthétisée) pour les vidéos Kit Pro.

Usage : python3 musique.py <sortie.wav> <durée_en_s> [graine]
Style : lo-fi doux, 84 BPM, accords variés selon la graine, fondu d'entrée et de sortie.
Volume volontairement bas (fond sonore sous le texte).
"""
import sys, numpy as np, wave

SR = 44100

def note(f, dur, kind='pad'):
    t = np.arange(int(SR * dur)) / SR
    if kind == 'pad':
        w = 0.6 * np.sin(2*np.pi*f*t) + 0.25 * np.sin(2*np.pi*2*f*t + 0.3) + 0.1 * np.sin(2*np.pi*3*f*t)
        env = np.minimum(1, t / 0.35) * np.exp(-t * 0.35)
    elif kind == 'bass':
        w = np.sin(2*np.pi*f*t)
        env = np.minimum(1, t / 0.02) * np.exp(-t * 2.2)
    else:  # pluck
        w = np.sign(np.sin(2*np.pi*f*t)) * 0.3 + np.sin(2*np.pi*f*t) * 0.7
        env = np.minimum(1, t / 0.005) * np.exp(-t * 6)
    return w * env

def kick(dur=0.3):
    t = np.arange(int(SR * dur)) / SR
    f = 110 * np.exp(-t * 18) + 45
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 9)

def hat(dur=0.06, rng=None):
    n = int(SR * dur)
    return rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 70) * 0.25

def build(duration, seed=1):
    rng = np.random.default_rng(seed)
    bpm = 84; beat = 60 / bpm; bar = beat * 4
    roots = {'A': 220.0, 'F': 174.61, 'C': 261.63, 'G': 196.0, 'D': 293.66, 'E': 164.81}
    progs = [['A', 'F', 'C', 'G'], ['C', 'G', 'A', 'F'], ['F', 'C', 'G', 'A'], ['D', 'G', 'C', 'A']]
    prog = progs[seed % len(progs)]
    minor = {'A', 'D', 'E'}
    out = np.zeros(int(SR * (duration + 2)))
    def add(sig, start, gain):
        i = int(start * SR)
        if i >= len(out):
            return
        j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i] * gain
    tcur = 0.0; k = 0
    while tcur < duration:
        r = roots[prog[k % 4]]
        third = r * (2 ** (3/12) if prog[k % 4] in minor else 2 ** (4/12))
        for f in (r, third, r * 2 ** (7/12)):
            add(note(f, bar + 0.5, 'pad'), tcur, 0.10)
        add(note(r / 2, beat * 1.5, 'bass'), tcur, 0.22)
        add(note(r / 2, beat * 1.5, 'bass'), tcur + beat * 2, 0.18)
        for b in range(4):
            add(kick(), tcur + b * beat, 0.30 if b % 2 == 0 else 0.0)
            add(hat(rng=rng), tcur + b * beat + beat / 2, 0.5)
        melody = [r * 2, third * 2, r * 2 ** (7/12) * 2, third * 2]
        for b in range(4):
            if rng.random() < 0.55:
                add(note(melody[(b + k) % 4], beat * 0.9, 'pluck'), tcur + b * beat + (beat / 2 if rng.random() < 0.3 else 0), 0.05)
        tcur += bar; k += 1
    out = out[:int(SR * duration)]
    fade = int(SR * 1.2)
    out[:fade] *= np.linspace(0, 1, fade); out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.35  # bas niveau : fond sonore
    return out

if __name__ == '__main__':
    path, dur = sys.argv[1], float(sys.argv[2])
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    sig = build(dur, seed)
    st = np.stack([sig, sig], axis=1)
    data = (st * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
    print('ok', path)
