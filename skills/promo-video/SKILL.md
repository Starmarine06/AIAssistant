---
name: promo-video
description: Build, edit, re-render, and publish the AI Assistant promotional video (Remotion project). Covers the 15-scene timing plan, landscape/portrait renders, music bed mixing, ElevenLabs voiceover, ffmpeg muxing, and embedding the final MP4 into the GitHub README via a user-attachments CDN URL. Use when modifying promo scenes, re-rendering the promo, adding a voiceover, changing music, or fixing the README embed.
metadata:
  origin: AIAssistant
---

# AI Assistant Promo Video — Build & Rerender

## Project Layout

Everything lives in `promo-video/`:

```
promo-video/
  package.json          # npm scripts: studio, render:landscape, render:portrait
  remotion.config.ts
  src/
    Root.tsx            # Compositions: Promo-Landscape (1920x1080), Promo-Portrait (1080x1920)
    Promo.tsx           # TransitionSeries timeline — THE timing plan
    LayoutContext.tsx   # responsive layout for both orientations
    lib.ts              # palette constants: CYAN, INK, RED
    scenes/             # Hook, Pain, Turn, Reveal, Feature1-5, Feature1b, Trust, Cta
  scripts/
    tts.mjs             # ElevenLabs voiceover generator (15 sections, Daniel voice)
  audio/
    music.mp3           # raw music bed (source asset)
    music-mix.mp3       # mixed 60s bed (volume/fade/normalize) — gitignored
    sections/           # per-section voiceover clips — gitignored
  assets/
    promo-landscape.mp4 # published landscape video (committed)
    promo-poster.png    # README poster frame
  out/                  # renders and finals — gitignored
```

## Key Commands

```bash
cd promo-video

npm install                      # first time (remotion 4.x, react 19, lucide-react)
npx remotion studio              # visual editing, live preview
npm run render:landscape         # -> out/promo-landscape.mp4  (1800 frames)
npm run render:portrait          # -> out/promo-portrait.mp4   (1800 frames)
```

The `out/` folder is gitignored; `assets/` holds the committed copies (currently
`promo-landscape.mp4`). Gitignored patterns: `node_modules/`, `out/`, `audio/sections/`,
`audio/*.mp3`.

## The Timing Plan (do not break this)

`Promo.tsx` sums sequence durations (`1968`) minus 14 transitions × 12 frames (=`168`)
to exactly **1800 frames = 60.0s @ 30fps**. If you insert or remove a scene, keep the
total at 1800 frames and re-check `durationInFrames` in `Root.tsx`.

The 15 tracked voiceover slots (start times in seconds, matching `scripts/tts.mjs`):

| id      | start | scene |
|---------|-------|-------|
| hook    | 0.20  | Hook (105f) |
| pain1   | 3.25  | Pain #1 (84f) |
| pain2   | 5.70  | Pain #2 (72f) |
| pain3   | 7.65  | Pain #3 (84f) |
| pain4   | 10.35 | Pain #4 (90f) |
| turn    | 12.80 | Turn (120f) |
| reveal  | 16.60 | Reveal (147f) |
| f1      | 21.00 | Feature1 (180f) |
| f1b     | 26.60 | Feature1b (120f) |
| f2      | 30.40 | Feature2 (186f) |
| f3      | 36.20 | Feature3 (168f) |
| f4      | 41.00 | Feature4 (141f) |
| f5      | 45.30 | Feature5 (141f) |
| trust   | 49.80 | Trust (120f) |
| cta     | 53.40 | Cta (210f) |

Transitions: 14 × `linearTiming({durationInFrames: 12})`, alternating `fade()` and
`slide({direction: 'from-right'})`.

Design rules already enforced in scenes:
- Feature2 grid labels: `COLS = ['A'..'J']` across the top, `ROWS = ['1'..'10']` down the left, so a cursor at 35%/55% reads cell `D6` — matching the byline "Tap D-six".
- Palette: background `#070A12`, cyan/ink/red from `lib.ts`. Keep abstract flat shapes; no external images.

## Audio

### Music bed

The mixed 60.03s bed `audio/music-mix.mp3` is produced from the source `music.mp3`:

```bash
npx remotion ffmpeg -y -i audio/music.mp3 \
  -af "volume='0.1*min(1,t/2)*min(1,(60-t)/3)':eval=frame,atrim=0:60,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100" \
  -c:a libmp3lame -b:a 192k audio/music-mix.mp3
```

- 2s fade-in, 3s fade-out ending at 60s, normalized to `I=-16`, 44.1kHz, 192kbps.
- **Do NOT use an `afade` filter**: the Remotion-bundled ffmpeg (n7.1) was compiled with a
  limited filter set that has no `afade`. Always express fades via a `volume` expression with `eval=frame`.

### Voiceover (optional)

`scripts/tts.mjs` synthesizes 15 clips with the ElevenLabs **Daniel** voice
(`onwK4e9ZLuTAKqWW03F9`, model `eleven_multilingual_v2`) into `audio/sections/`:

```bash
$env:ELEVENLABS_API_KEY="<key>"; node scripts/tts.mjs
```

Per-section preset mapping lives in the script (neutral/urgent/playful/whisper/dramatic/
confident/warm = stability 0.2–0.68, similarity 0.83–0.9). Editing copy = edit the
`SECTIONS` array in `tts.mjs`. The script zero-fills existing clips before regenerating.

### Final mux

```bash
npx remotion ffmpeg -y -i out/promo-landscape.mp4 -i audio/music-mix.mp3 \
  -c:v copy -c:a aac -b:a 192k -shortest -pix_fmt yuv420p out/promo-landscape-final.mp4
```

(`Promo-Portrait` analog for portrait.) Width/height are already baked into the render.

## Publishing (README embed)

GitHub does NOT render `<video>` when `src` is a repo-relative path — you must use an
**absolute GitHub CDN URL**, i.e. a `https://github.com/user-attachments/assets/<uuid>`.

The `--attach` flag on `gh` only exists in v2.99+; this machine has gh 2.96.0. Instead
upload through the same endpoint the web drag-and-drop uses:

```pwsh
# upload repo's committed asset to get a UUID
$token = gh auth token
$repo = gh api repos/Starmarine06/AIAssistant --jq .id
curl.exe -s "https://uploads.github.com/user-attachments/assets?name=promo-landscape.mp4&content_type=video%2Fmp4&repository_id=$repo" \
  -X POST -H "Authorization: Bearer $token" -H "Accept: application/json" \
  --data-binary "@promo-video/assets/promo-landscape.mp4"
# -> {"url":"https://github.com/user-attachments/assets/<uuid>"}
```

Then embed like the repo's animated-logo style — seamless, silent, looping:

```html
<p align="center">
  <video src="https://github.com/user-attachments/assets/<uuid>"
         poster="https://raw.githubusercontent.com/Starmarine06/AIAssistant/main/promo-video/assets/promo-poster.png"
         width="70%" autoplay loop muted playsinline></video>
</p>
```

- The video must stay under ~10 MB and be H.264 mp4 (current 6.1 MB file qualifies).
- `poster` avoids a black box pre-playback; regenerate it if scenes change:
  `npx remotion ffmpeg -y -ss 2.5 -i out/promo-landscape-final.mp4 -frames:v 1 -update 1 assets/promo-poster.png`
  (note: the bare `-frames:v 1` to a `.png` fails with an image2 pattern error unless you pass `-update 1`).
- If the referenced scene starts later, pick a poster frame time that shows something on screen.

## Render Failure Checklist

1. Total duration drift: sum `Promo.tsx` sequences − transitions ≠ 1800 → trim a scene.
2. Blank poster / missing CDN: re-upload the asset, don't reuse a stale UUID.
3. ffmpeg filter errors: the Remotion ffmpeg build is minimal — no `afade`, keep filtering to volume/atrim/loudnorm/aresample.
4. Voiceover timing: regenerate after editing scene durations, keep section starts inside their scenes.