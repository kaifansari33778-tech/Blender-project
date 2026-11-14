---
name: documentary-template-1
description: >
  "Documentary Template 1" - the saved house style for narrated vertical explainer videos in this repo:
  a paper-diorama evidence-board look with real halftone photo cutouts, flowing flags, letterpress labels,
  whip-pan camera and subtle synthesized sound, rendered entirely in code (voxkit) and timed word-by-word
  to a supplied voice-over. Use whenever the user asks for a video "in documentary template 1", "the same
  style as the NVIDIA video", or a new video in this chat's style.
---

# Documentary Template 1

Reference implementation: `projects/nvidia-spy/show.py` (finished video: `projects/nvidia-spy/final.mp4`).
Engine: `voxkit/core.py` (compositor, camera, blur, film post) and `voxkit/art.py` (props, cutouts, flags).

## The look (do not change without being asked)

- 9:16, 1080x1920, 30 fps. Sepia newsprint world, warm tungsten grade, vignette, grain, light tilt-shift.
- **Real people = real photos**, printed as monochrome halftone cutouts with a rough white paper border
  (`art.photo_cutout`). Group photos / screenshots become pinned photo prints (`art.photo_print`).
  Never use an unverified photo of a private person; ask the user for the photo and where it came from.
- Whenever a country or leader is mentioned, show the **flag, flowing** (`wave(...)`, `wv=` on an element)
  and the leader's real photo cutout behind the subject.
- Real logos / seals as colour stickers (`art.sticker`); drawn stand-ins only when the real one can't be fetched.
- Accent colours: burnt orange (labels, chips, strokes), red (stamps, string, China), NVIDIA green only for NVIDIA.
- **One letterpress label per beat** carrying the key phrase or number, slammed on the exact word.
- Every panel is dense: rotating sunburst, 10-25 elements (cash, chips, dossier pages, pins + red string,
  calendars, stamps, buildings), out-of-focus paper scraps drifting near the lens.
- Censor bar only as a story beat (e.g. "second job", "one mission"), not on every face.

## Motion

- One shot per sentence/clause. Shots sit in separate world zones; a 0.34 s whip-pan with motion blur joins them.
- Elements enter on their word: `pop`, `slam` (impact + shake + paper burst), `drop`, `rise`, `L`/`R` slides,
  hand-drawn marker `S(...)` strokes (arrows, circles, charts, dashed routes).
- Slow push-in during each shot; everything has a slight wobble so nothing is ever static.

## Sound - subtle

Synthesized in `soundtrack()` from the same event list: soft thump per slam, quiet pops, light whoosh per whip,
faint scribble for strokes, low drone + heartbeat. Voice is the star; SFX gains stay at the levels in
`projects/nvidia-spy/show.py` (the user asked for subtle).

## Workflow for a new video

1. User supplies script + one voice-over file. Fact-check the script; flag anything unverifiable.
2. Word timings: `pocketsphinx` forced alignment (see `words_v2.json` format `[word, start, end]`); use `T('word', n)`.
3. List the photos needed; fetch public figures from Wikimedia Commons (rate-limited - go slowly, honest
   User-Agent), ask the user for anyone else. Record credits in `photos/CREDITS.md`.
4. Copy `projects/nvidia-spy/show.py` to the new project, replace assets and the `SHOTS` list.
5. `python3 show.py stills <dir> t1,t2,...` to check every shot, then `render <outdir>` (10 s segments,
   resumable), `mux <outdir> <out.mp4>`, and compress with x264 crf 27 (keeps the file under ~75 MB).

## Script rule: open with a "did you know" shock fact

Every script opens with one shocking, verified fact from the first story, asked as a question:
"Did you know that in just five years, one disease killed up to half of everyone in Europe?"
Then one line naming it, then the signature line (for list videos: "That's one. Give me sixty seconds,
and I'll show you six more."). No made-up scenes, no generic teasers.
