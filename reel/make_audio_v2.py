"""v2 audio: re-cut + sped-up VO, sectioned stereo music (build / groove / breakdown / drop / outro),
extra SFX, sidechain pump, loudness-normalised to -14 LUFS -> audio/mix_v2.wav"""
import json, subprocess, numpy as np, wave
SR = 44100
E = json.load(open('edl.json'))
DUR = E['total']; N = int(SR * DUR)
rng = np.random.default_rng(11)

def o2n(old, tol=0.06):
    """map a source-time event into new time (None if it falls in a cut)"""
    for s in E['segs']:
        if s['freeze']: continue
        if s['src0'] - tol <= old <= s['src1'] + tol:
            return s['dst'] + (old - s['src0']) / s['speed']
    return None
seg_by = lambda i: E['segs'][i]
T_PLAN = seg_by(2)['dst']; T_FREEZE = seg_by(3)['dst']; T_END = seg_by(5)['dst']
T_COMBO = o2n(31.42); T_EXCEPT = o2n(12.15); T_COLD = E['cold']

def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def tone(freq, dur, kind='sine'):
    n = int(SR * dur)
    ph = 2 * np.pi * freq * np.arange(n) / SR if np.isscalar(freq) else 2 * np.pi * np.cumsum(freq[:n]) / SR
    if kind == 'saw': return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == 'sq': return np.sign(np.sin(ph))
    return np.sin(ph)
def noise(dur): return rng.uniform(-1, 1, int(SR * dur))
def lp(x, a):
    # vectorised one-pole lowpass via lfilter-like recursion in chunks
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a * (x[i] - acc); y[i] = acc
    return y
def hp(x, a): return x - lp(x, a)
def add(buf, x, at, gain=1.0, pan=0.0):
    if at is None: return
    i = int(at * SR)
    if i < 0: x = x[-i:]; i = 0
    if i >= buf.shape[1]: return
    x = x[: buf.shape[1] - i]
    l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    buf[0, i:i + len(x)] += x * gain * l * 1.414
    buf[1, i:i + len(x)] += x * gain * r * 1.414
def mtof(m): return 440 * 2 ** ((m - 69) / 12)

# ================= VOICE =================
voice = np.zeros((2, N))
for s in E['segs']:
    if s['freeze']: continue
    af = f"atrim={s['src0']}:{s['src1']},asetpts=PTS-STARTPTS,atempo={s['speed']},highpass=f=90,acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=3,afade=t=in:d=0.02,afade=t=out:st={(s['src1']-s['src0'])/s['speed']-0.03:.3f}:d=0.03"
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'audio/voiceover.mp3', '-af', af, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    add(voice, np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768, s['dst'])

# ================= MUSIC =================
music = np.zeros((2, N)); kick_env = np.zeros(N)
bpm = 128; beat = 60 / bpm
kick = tone(np.linspace(160, 42, int(SR * 0.3)), 0.3) * env(int(SR * 0.3), 0.001, 0.13)
kick[:200] += noise(200 / SR) * np.linspace(1, 0, 200) * 0.6
hat = hp(noise(0.05), 0.5) * env(int(SR * 0.05), 0.001, 0.018)
ohat = hp(noise(0.25), 0.5) * env(int(SR * 0.25), 0.001, 0.09)
snare = (hp(noise(0.25), 0.2) * 0.8 + tone(185, 0.25) * 0.4) * env(int(SR * 0.25), 0.001, 0.09)
clap = np.concatenate([hp(noise(0.01), 0.3) * 0.6, np.zeros(int(SR * 0.008)), hp(noise(0.2), 0.3) * env(int(SR * 0.2), 0.001, 0.06)])
prog = [57, 53, 48, 55]  # Am F C G
def section(t):
    if t < T_COLD: return 'cold'
    if T_EXCEPT is not None and T_EXCEPT <= t < T_EXCEPT + 0.55: return 'stop'
    if t < T_PLAN: return 'groove'
    if t < T_COMBO: return 'break'
    if t < T_FREEZE: return 'drop'
    if t < T_FREEZE + 0.45: return 'stop'
    return 'outro'
# lay the grid starting at the cold-open end so the downbeat lands on the first line
t0 = T_COLD
b = -int(T_COLD / beat) - 1
while True:
    tb = t0 + b * beat; b += 1
    if tb > DUR: break
    if tb < 0: continue
    sec = section(tb)
    bi = b - 1; bar = (bi // 4) % 4; root = prog[bar]
    if sec in ('groove', 'drop', 'outro'):
        add(music, kick, tb, 0.95); kick_env[int(tb * SR):int(tb * SR) + int(SR * 0.22)] = np.linspace(1, 0, int(SR * 0.22))[: max(0, min(int(SR * 0.22), N - int(tb * SR)))]
        add(music, hat, tb + beat / 2, 0.35, 0.3)
        if bi % 2 == 1: add(music, snare, tb, 0.55); add(music, clap, tb, 0.35, -0.1)
        if sec == 'drop':
            for q in (0.25, 0.75): add(music, hat, tb + beat * q, 0.25, -0.3)
            if bi % 4 == 3: add(music, ohat, tb + beat / 2, 0.25, 0.4)
        bs = lp(tone(mtof(root - 24), beat / 2, 'saw'), 0.07 if sec != 'drop' else 0.12) * env(int(SR * beat / 2), 0.004, 0.16)
        add(music, bs, tb + beat / 2, 0.6 if sec != 'drop' else 0.75)
        if sec == 'drop': add(music, bs * 0.8, tb, 0.5)
    if sec in ('groove', 'drop', 'break', 'outro'):
        for k, iv in enumerate([0, 7, 12, 15] if sec != 'outro' else [0, 4, 7, 12]):
            f = mtof(root + 12 + iv)
            pl = lp(tone(f, beat / 4, 'sq'), 0.22) * env(int(SR * beat / 4), 0.002, 0.06)
            g = {'groove': 0.07, 'drop': 0.11, 'break': 0.09, 'outro': 0.08}[sec]
            add(music, pl, tb + k * beat / 4, g, -0.5 + k * 0.33)
    if sec in ('break', 'outro', 'cold') and bi % 4 == 0:  # pads
        pad = sum(tone(mtof(root + iv), beat * 4, 'saw') for iv in (0, 3 if sec != 'outro' else 4, 7, 12))
        pad = lp(pad, 0.03) * np.minimum(1, np.arange(len(pad)) / (SR * 0.4)) * np.minimum(1, (len(pad) - np.arange(len(pad))) / (SR * 0.3))
        add(music, pad, tb, 0.05, -0.4); add(music, pad, tb + 0.012, 0.05, 0.4)
# risers: cold open + into the combo drop
def riser(d):
    n = int(SR * d); x = lp(noise(d), 0.15) * 0.6 + tone(np.linspace(200, 1600, n), d, 'saw') * 0.15
    return x * np.linspace(0, 1, n) ** 2
add(music, riser(1.25), 0.0, 0.5)
add(music, riser(1.6), T_COMBO - 1.6, 0.55)
# snare roll before drop
for k in range(12): add(music, snare, T_COMBO - 1.5 + k * 0.125, 0.12 + k * 0.03)
# sidechain pump
pump = 1 - 0.45 * kick_env
music *= pump
music = np.tanh(music * 0.9)

# ================= SFX =================
sfx = np.zeros((2, N))
def s_whoosh(d=0.35):
    n = noise(d); e = np.sin(np.linspace(0, np.pi, len(n))) ** 2
    return lp(n, 0.06) * e * 3
def s_hit(big=False):
    d = 0.5 if big else 0.25
    body = tone(np.linspace(240 if big else 320, 45, int(SR * d)), d) * env(int(SR * d), 0.001, 0.14 if big else 0.07)
    crack = noise(d) * env(int(SR * d), 0.0005, 0.025 if not big else 0.06)
    return np.tanh((body * 1.3 + crack) * (2.4 if big else 1.6))
def s_tap(): return s_hit()[: int(SR * 0.08)] * 0.5
def s_thud(): return tone(np.linspace(110, 35, int(SR * 0.4)), 0.4) * env(int(SR * 0.4), 0.001, 0.15)
def s_ding():
    return (tone(1320, 0.7) * env(int(SR * 0.7), 0.001, 0.25) + tone(1980, 0.7) * env(int(SR * 0.7), 0.001, 0.12) * 0.5) * 0.5
def s_charge(): d = 0.55; return tone(np.linspace(200, 900, int(SR * d)), d, 'sq') * np.linspace(0, 1, int(SR * d)) * 0.15
def s_rise(): d = 0.7; return (tone(np.linspace(300, 1200, int(SR * d)), d) * 0.3 + lp(noise(d), 0.1) * 0.6) * np.linspace(0.2, 1, int(SR * d)) * env(int(SR * d), 0.01, 0.6)
def s_quake(): d = 1.0; return np.tanh(lp(noise(d), 0.02) * 6 + tone(40, d) * 0.8) * env(int(SR * d), 0.002, 0.45)
def s_shatter():
    d = 0.8; x = np.zeros((2, int(SR * d)))
    for k in range(40): add(x, tone(rng.uniform(2000, 6000), 0.15) * env(int(SR * 0.15), 0.0005, 0.03), rng.uniform(0, 0.4), 0.25, rng.uniform(-0.8, 0.8))
    return x.mean(0) * 2 + noise(d) * env(int(SR * d), 0.001, 0.08) * 0.6
def s_zap():
    d = 0.45; n = noise(d); sq = tone(np.linspace(1800, 200, int(SR * d)), d, 'sq')
    return (n * 0.5 + sq * 0.5) * (rng.uniform(0, 1, len(n)) > 0.4) * env(len(n), 0.001, 0.15)
def s_wind():
    d = 1.6; n = lp(noise(d), 0.06); m = 0.5 + 0.5 * np.sin(np.arange(len(n)) / SR * 2 * np.pi * 6)
    return n * m * np.sin(np.linspace(0, np.pi, len(n))) * 4
def s_boom():  # meme-style deep boom
    d = 1.4; x = tone(np.linspace(90, 38, int(SR * d)), d) * env(int(SR * d), 0.002, 0.5)
    return np.tanh(x * 3) * 0.9
def s_scratch():  # record scratch
    d = 0.45; f = 600 + 500 * np.sin(np.linspace(0, 6 * np.pi, int(SR * d)))
    return (lp(noise(d), 0.3) * 0.7 + tone(f, d, 'saw') * 0.3) * np.abs(np.sin(np.linspace(0, 3 * np.pi, int(SR * d)))) * 0.9
def s_stamp(): return np.tanh(s_hit(True) * 1.2) * 0.8 + s_thud() [: int(SR * 0.5)].tolist().__len__() * 0 
def s_pop():
    d = 0.12; return tone(np.linspace(500, 1400, int(SR * d)), d) * env(int(SR * d), 0.001, 0.04)
def s_crowd():
    d = 3.0; x = sum(lp(noise(d), 0.02 + 0.03 * k) * (0.6 + 0.4 * np.sin(np.arange(int(SR * d)) / SR * (2 + k) + k)) for k in range(5))
    return x * np.minimum(1, np.arange(len(x)) / (SR * 0.15)) * np.exp(-np.arange(len(x)) / (SR * 1.6)) * 1.6
def s_rewind():
    d = 0.5; f = np.linspace(2400, 300, int(SR * d))
    return (tone(f, d, 'saw') * 0.3 + lp(noise(d), 0.4) * 0.5) * (0.5 + 0.5 * np.sign(np.sin(np.arange(int(SR * d)) / SR * 2 * np.pi * 28)))
def s_impact(): return np.tanh(s_hit(True) * 1.5 + np.pad(s_boom(), (0, 0))[: int(SR * 0.5)] * 0.8)

LIB = {'whoosh': (s_whoosh, 0.5), 'hit': (lambda: s_hit(False), 0.85), 'bighit': (lambda: s_hit(True), 1.0), 'tap': (s_tap, 0.55),
       'thud': (s_thud, 0.8), 'ding': (s_ding, 0.45), 'charge': (s_charge, 0.5), 'rise': (s_rise, 0.4), 'land': (lambda: s_thud() * 0.7, 0.6),
       'quake': (s_quake, 0.9), 'shatter': (s_shatter, 0.7), 'zap': (s_zap, 0.6), 'wind': (s_wind, 0.55), 'water': (lambda: noise(0.1) * 0, 0),
       'boom': (s_boom, 0.7), 'scratch': (s_scratch, 0.7), 'stamp': (lambda: s_hit(True), 0.8), 'pop': (s_pop, 0.35), 'crowd': (s_crowd, 0.5)}
cache = {}
for name, at in json.load(open('audio/sfx_events.json')):
    if name not in cache: cache[name] = LIB[name][0]()
    add(sfx, cache[name], o2n(at), LIB[name][1], (rng.uniform(-0.25, 0.25)))
# new-time events: cold-open impact, rewind, cut whooshes, freeze impact
add(sfx, s_impact(), 0.0, 0.9)
add(sfx, s_wind()[: int(SR * 1.2)], 0.05, 0.3)
add(sfx, s_rewind(), 1.25, 0.6)
for s in E['segs'][1:]:
    if not s['freeze'] and s['src0'] not in (37.58,): add(sfx, s_whoosh(0.3), s['dst'] - 0.15, 0.4)
add(sfx, s_impact(), T_FREEZE, 1.0)
add(sfx, s_boom(), T_FREEZE, 0.5)

# ================= MIX =================
venv = np.abs(voice[0]); k = int(SR * 0.12)
venv = np.convolve(venv, np.ones(k) / k, mode='same')
duck = 1 - 0.5 * np.clip(venv / 0.05, 0, 1)
t_all = np.arange(N) / SR
fade = np.clip((DUR - t_all) / 0.6, 0, 1)
mix = voice * 1.0 + music * 0.30 * duck * fade + sfx * 0.42
mix /= max(1e-6, np.max(np.abs(mix))) / 0.9
pcm = (np.clip(mix.T, -1, 1) * 32767).astype(np.int16)
with wave.open('audio/mix_v2_raw.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', 'audio/mix_v2_raw.wav', '-af', 'loudnorm=I=-14:TP=-1.0:LRA=9', '-ar', str(SR), 'audio/mix_v2.wav'], check=True)
print('ok', DUR, 'combo', round(T_COMBO, 2), 'freeze', T_FREEZE)
