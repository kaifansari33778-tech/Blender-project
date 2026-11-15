---
name: documentary-template-2
description: "Documentary Template 2" - the full-frame layered photo-collage style for narrated vertical explainer videos (first used on the Bhopal 1984 video). One real photograph per phrase fills the frame, split into depth layers with a slow push-in, big words between the layers, typed captions with a highlight box, zoom-through and paper-tear transitions. Use whenever the user asks for "documentary template 2", "the Bhopal style", "the tearing style" or a new video in that look.
---

# Documentary Template 2 - full-frame layered photo collage

Code: `voxkit/collage.py` (plates, captions, tear), `voxkit/cine.py` (camera, pinned captions, hanging props), `voxkit/pop3d.py` (3D card renderer).
Reference build: `projects/bhopal/sample2.py` (scenes 1-3) and `projects/bhopal/sample3.py` (scenes 4-6, all transitions).

## Rules
1. **One image per phrase, and it must mean what is being said.** Never scatter small photos. Every image fills the frame and is picked for the words spoken over it. If no real photo fits, draw the scene (and say so in the report).
2. **Depth in every image.** Cut the photo into layers: a drawn sky plate (far), the subject with the sky removed (`nonsky` / `subject`), the lower part of the photo as a nearer torn band (`band`), and where possible a foreground object close to the lens (statue, crowd, wire) that is slightly blurred. Typical depths: sky z=75, big text z=46, subject z=30, band z=15, foreground z=6-10.
3. **Camera: slow push-in with a little drift** (`look(...)` from z about -2 to +5, x drifting 2-3 m, small rise). Vary the direction scene to scene. No constant low-angle shots.
4. **Big words between the layers**: one or two words in huge type behind the subject (`big_text`), popping up with `back()` easing.
5. **Captions** (written exactly as the script, e.g. Hinglish): narration typed word by word in a small cream label at the top, four words at a time (`typed`); the key phrase of the sentence pops in a yellow highlight box low in the frame (`hl`). One accent colour per video besides yellow.
6. **Grade**: photos nearly monochrome in one tone per scene (`grade`): warm sepia for day/archive, blue for night; colour only in the accent (gas, labels, text).
7. **Motion inside the scene**: something always moves - gas creeping between layers, a prop dropping on a string (`hang`), a figure rising from below, drifting dust.
8. **Transitions** (alternate them):
   - zoom-through: camera accelerates into the image, `zoom_blur`, exposure dip, next scene settles from a pull-back;
   - paper tear: `rip(new, old, k, ang)` - the old frame tears along a jagged line and the two pieces slide apart over the new scene (vertical ang=0, horizontal ang=pi/2, diagonal about +-0.6). About 0.5 s, with a short ripping-noise sfx.
9. **Sound**: low drone and heartbeat, soft thump on each highlight, light typing ticks on each word, whoosh on zoom-through, rip noise on tears. Always subtle under the voice.
10. Real photos come from Wikimedia Commons thumbnails (`thumb.wikimedia.org`), licence and author recorded in `photos/wm/meta.json`; list credits in the final report. No photos of private people presented as someone they are not; no unverified portraits.

## Workflow
Script (opens with a "did you know" shock fact) -> user records voice -> forced alignment to `voice/words.json` -> fetch photos -> pick one photo per phrase -> short sample -> full render in 10 s segments -> mux with voice + sfx -> send.
