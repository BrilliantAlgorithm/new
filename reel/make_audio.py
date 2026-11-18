"""Synthesize music bed + SFX and mix with the voiceover -> audio/mix.wav"""
import json, subprocess, numpy as np, wave
SR = 44100
DUR = 46.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR

def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def tone(freq, dur, kind='sine'):
    t = np.arange(int(SR * dur)) / SR
    ph = 2 * np.pi * freq * t if np.isscalar(freq) else 2 * np.pi * np.cumsum(freq) / SR
    if kind == 'saw': return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == 'sq': return np.sign(np.sin(ph))
    return np.sin(ph)

def noise(dur): return rng.uniform(-1, 1, int(SR * dur))
def lp(x, a=0.1):  # one-pole lowpass
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += a * (v - acc); y[i] = acc
    return y

def add(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += x * gain

# ---------------- music (128 BPM) ----------------
music = np.zeros(N)
bpm = 128; beat = 60 / bpm
kick = tone(np.linspace(150, 45, int(SR * 0.25)), 0.25) * env(int(SR * 0.25), 0.001, 0.12)
hat = np.diff(noise(0.06), prepend=0) * env(int(SR * 0.06), 0.001, 0.02)
snare = (noise(0.2) * 0.7 + tone(190, 0.2) * 0.3) * env(int(SR * 0.2), 0.001, 0.07)
roots = [45, 45, 41, 43]  # A, A, F, G (midi-ish offsets below)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
prog_notes = [57, 53, 48, 55]  # A3 F3 C3 G3
nbeats = int(DUR / beat) + 1
for b in range(nbeats):
    tb = b * beat
    if tb > 45.2: break
    section_drop = 31.4 <= tb < 37.6   # combo = full energy
    quiet = tb < 0.4 or (40.6 <= tb)
    add(music, kick, tb, 0.9 if not quiet else 0.5)
    add(music, hat, tb + beat / 2, 0.35)
    if section_drop: add(music, hat, tb + beat / 4, 0.25); add(music, hat, tb + 3 * beat / 4, 0.25)
    if b % 2 == 1: add(music, snare, tb, 0.5)
    bar = (b // 4) % 4
    root = mtof(prog_notes[bar] - 12)
    # offbeat bass
    bs = tone(root, beat / 2, 'saw'); bs = lp(bs, 0.08) * env(len(bs), 0.005, 0.15)
    add(music, bs, tb + beat / 2, 0.55)
    # pluck arp
    for k, iv in enumerate([0, 7, 12, 7]):
        f = mtof(prog_notes[bar] + 12 + iv + (3 if k == 2 else 0))
        pl = tone(f, beat / 4, 'sq') * env(int(SR * beat / 4), 0.002, 0.05)
        add(music, lp(pl, 0.25), tb + k * beat / 4, 0.08 if not section_drop else 0.12)
music = np.tanh(music * 0.9)

# ---------------- SFX ----------------
sfx = np.zeros(N)
def s_whoosh():
    n = noise(0.35); e = np.sin(np.linspace(0, np.pi, len(n))) ** 2
    return lp(n, 0.05) * e * 3
def s_hit(big=False):
    d = 0.45 if big else 0.22
    body = tone(np.linspace(220 if big else 300, 50, int(SR * d)), d) * env(int(SR * d), 0.001, 0.12 if big else 0.06)
    crack = noise(d) * env(int(SR * d), 0.0005, 0.02 if not big else 0.05)
    return np.tanh((body * 1.2 + crack * 0.9) * (2.2 if big else 1.4))
def s_tap(): return s_hit()[: int(SR * 0.08)] * 0.5
def s_thud(): return tone(np.linspace(110, 35, int(SR * 0.4)), 0.4) * env(int(SR * 0.4), 0.001, 0.15)
def s_ding():
    x = tone(1320, 0.6) * env(int(SR * 0.6), 0.001, 0.2) + tone(1980, 0.6) * env(int(SR * 0.6), 0.001, 0.1) * 0.5
    return x * 0.5
def s_water():
    n = noise(1.4); return lp(n, 0.18) * (0.6 + 0.4 * np.sin(np.arange(len(n)) / SR * 60)) * env(len(n), 0.03, 1.2) * 1.4
def s_charge():
    d = 0.55; return tone(np.linspace(200, 900, int(SR * d)), d, 'sq') * np.linspace(0, 1, int(SR * d)) * 0.15
def s_rise():
    d = 0.7; return (tone(np.linspace(300, 1200, int(SR * d)), d) * 0.3 + lp(noise(d), 0.1) * 0.6) * np.linspace(0.2, 1, int(SR * d)) * env(int(SR * d), 0.01, 0.6)
def s_quake():
    d = 1.0; return np.tanh(lp(noise(d), 0.02) * 6 + tone(40, d) * 0.8) * env(int(SR * d), 0.002, 0.45)
def s_shatter():
    d = 0.8; x = np.zeros(int(SR * d))
    for k in range(40):
        f = rng.uniform(2000, 6000); st = rng.uniform(0, 0.4)
        add(x, tone(f, 0.15) * env(int(SR * 0.15), 0.0005, 0.03), st, 0.25)
    return x + noise(d) * env(int(SR * d), 0.001, 0.08) * 0.6
def s_zap():
    d = 0.4; n = noise(d); sq = tone(np.linspace(1800, 200, int(SR * d)), d, 'sq')
    return (n * 0.5 + sq * 0.5) * (rng.uniform(0, 1, len(n)) > 0.4) * env(len(n), 0.001, 0.15)
def s_wind():
    d = 1.6; n = lp(noise(d), 0.06); m = 0.5 + 0.5 * np.sin(np.arange(len(n)) / SR * 2 * np.pi * 6)
    return n * m * np.sin(np.linspace(0, np.pi, len(n))) * 4
def s_land(): return s_thud() * 0.7

LIB = {'whoosh': (s_whoosh, 0.5), 'hit': (lambda: s_hit(False), 0.8), 'bighit': (lambda: s_hit(True), 1.0), 'tap': (s_tap, 0.55),
       'thud': (s_thud, 0.8), 'ding': (s_ding, 0.45), 'water': (s_water, 0.55), 'charge': (s_charge, 0.5), 'rise': (s_rise, 0.4),
       'quake': (s_quake, 0.9), 'shatter': (s_shatter, 0.7), 'zap': (s_zap, 0.6), 'wind': (s_wind, 0.55), 'land': (s_land, 0.6)}
cache = {}
for name, at in json.load(open('audio/sfx_events.json')):
    if name not in cache: cache[name] = LIB[name][0]()
    add(sfx, cache[name], at, LIB[name][1])

# ---------------- voiceover ----------------
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'audio/voiceover.mp3', '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
vo = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768
voice = np.zeros(N); add(voice, vo, 0.0, 1.0)

# duck music under voice
venv = np.abs(voice); k = int(SR * 0.15)
venv = np.convolve(venv, np.ones(k) / k, mode='same')
duck = 1 - 0.55 * np.clip(venv / 0.05, 0, 1)
fade = np.clip((DUR - t_all) / 1.5, 0, 1) * np.clip(t_all / 0.3, 0, 1)
mix = voice * 1.0 + music * 0.22 * duck * fade + sfx * 0.45
mix = mix / max(1e-6, np.max(np.abs(mix))) * 0.95
pcm = (mix * 32767).astype(np.int16)
with wave.open('audio/mix.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', len(pcm) / SR)
