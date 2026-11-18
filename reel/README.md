# Elemental Duelists — promo reel

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
