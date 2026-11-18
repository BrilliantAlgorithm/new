# Elemental Duelists — promo reel

## v2: `elemental_duelists_reel_v2.mp4` (recommended)
33 s, 1080×1920, stereo, -14 LUFS. Built for retention:
- **Hook:** slow-mo Tempest Vortex cold open with "235 HP vs 310 HP — HOW?! 🤯", then a VHS rewind to the start
- **Pacing:** jump/Hydro Cannon detour cut, narration sped up 1.1×, a freeze-frame on the K.O.
- **Retention beats:** "Wait for the combo 👀", Attempt #1 ❌ / Attempt #2 ✅ stamps, emoji reactions, a progress bar, and a seamless loop flash
- **Visuals:** stadium crowd, spotlights, element particles, motion trails, impact frames, speed lines, camera push-ins
- **Audio:** sectioned music (build → groove → record-scratch stop → breakdown → riser → drop → outro), sidechain pump, meme boom, crowd cheer
- **CTA:** "▶ PLAY FREE NOW", "🔗 Link in bio • No download • Browser & iPad", "Who would you main? 👇"

Rebuild v2: `python3 make_edl.py && python3 make_audio_v2.py && node render.js audio/mix_v2.wav elemental_duelists_reel_v2.mp4`

## v1

`elemental_duelists_reel.mp4`: 1080×1920, 30 fps, 46 s. A vertical reel for Shorts, Reels or TikTok.

The format follows the "you, the absolute genius" explainer style: a problem, a dumb fix, a worse fix, then the smart fix.
1. Leo gets cornered by Marcus, the 310 HP tank
2. Mash punch → "Problem solved!" → Titan Haymaker
3. Jump over him → straight into Hydro Cannon
4. The plan: a Bunker Shield wall eats his Seismic Slam
5. Volt Dash → Sonic Straight → Cyclone Kick → Tempest Vortex → K.O.
6. End card: all three fighters + "PICK YOUR FIGHTER"

## Files
- `reel.html`: the animation renderer (open it in a browser to preview; Play syncs the voiceover)
- `timeline.js`: voiceover word timings, used for the captions
- `audio/voiceover.mp3`: narration (ElevenLabs, voice "Ethan")
- `make_audio.py`: synthesizes the music bed and SFX, then mixes them with the VO into `audio/mix.wav`
- `render.js`: renders the frames with Playwright and encodes the MP4 with ffmpeg

## Rebuild
```
python3 make_audio.py && node render.js
```

## Thumbnails
- `thumbnail_vertical.png` (1080×1920): cover for Shorts, Reels and TikTok
- `thumbnail_youtube.png` (1280×720): for a regular YouTube upload

Concept: tiny, smirking Leo (235 HP) against a giant Marcus (310 HP), "HOW DID HE WIN?! 🤯", and a locked, blurred "secret combo" that the video answers.
Rebuild: `node thumb.js`
