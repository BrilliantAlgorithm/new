"""Edit decision list for the v2 cut: which VO ranges to keep (source/old time) and where they land (new time)."""
import json
COLD = 1.75          # cold-open hook + rewind (new time)
SPEED = 1.1          # VO/visual speed-up
GAP = 0.10
TAIL = 2.3           # end-card hold after last line
# (src0, src1, speed, freeze_after)
CLIPS = [
    (0.05, 4.68, SPEED),     # If you pick Leo and get cornered by Marcus, a 310 HP tank,
    (7.44, 17.40, SPEED),    # being the absolute genius ... sends you flying.
    (24.44, 37.58, SPEED),   # Your huge brain finally gets a plan ... Tempest Vortex!
    ('freeze', 37.62, 0.45), # hit-stop on the K.O. blow
    (37.58, 38.30, 1.0),     # K.O.
    (40.62, 43.40, SPEED),   # Elemental Duelists. Pick your fighter!
]
segs, t = [], COLD
for i, c in enumerate(CLIPS):
    if c[0] == 'freeze':
        segs.append({'dst': round(t, 4), 'len': c[2], 'freeze': True, 'hold': c[1], 'src0': c[1], 'src1': c[1], 'speed': 0, 'gapAfter': 0})
        t += c[2]; continue
    s0, s1, sp = c
    ln = (s1 - s0) / sp
    nxt = CLIPS[i + 1] if i + 1 < len(CLIPS) else None
    gap = 0 if (nxt and (nxt[0] == 'freeze' or isinstance(CLIPS[i - 1], tuple) and CLIPS[i - 1][0] == 'freeze')) else GAP
    if nxt is None: gap = TAIL
    segs.append({'dst': round(t, 4), 'len': round(ln, 4), 'src0': s0, 'src1': s1, 'speed': sp, 'freeze': False, 'gapAfter': gap})
    t += ln + gap
edl = {'cold': COLD, 'segs': segs, 'total': round(t, 3)}
json.dump(edl, open('edl.json', 'w'), indent=1)
open('edl.js', 'w').write('window.EDL = ' + json.dumps(edl) + ';\n')
print('total', edl['total'])
for s in segs: print(s)
