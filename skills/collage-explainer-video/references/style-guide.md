# Style guide

The numbers here are the ones used in the finished example film. Treat them as a starting point that is
known to look right, and move away from them on purpose, not by accident.

## Frame
- 1080x1920, 30 fps. Scenes 2 to 4 seconds. A 2-minute film has about 30 scenes.
- Safe areas: captions own the top-left block (x 30 to 980, y 96 to 330). Keep the subject between
  y 450 and y 1650. Platform UI covers roughly the bottom 250 px, so nothing essential goes there.

## Colour chapters
The background colour is the chapter marker. The palette that was used:

| Chapter | Background | `flat_bg` RGB | Caption palette |
|---|---|---|---|
| Home / kitchen | green wall, tile band, dark counter | (.07, .38, .26) | BLU |
| Rumour / social media | purple with bokeh | (.30, .08, .42) | PNK |
| Evidence / facts / documents | mustard yellow desk | (.82, .62, .09) | RED |
| Factory / fire | graded photo, orange | photo tint (1, .55, .25) | YLW / ORG |
| Inside the body | maroon | (.36, .05, .11) | TEAL |
| Cold storage | blurred photo, blue | photo tint (.5, .7, 1) | BLU |
| Night / outside | graded city photo | photo tint (.6, .6, 1) | RED |

Pick a palette like this for a new topic before building anything, and return to a colour when the
topic returns. Viewers read the colour faster than the caption.

## Making flat cutouts look 3D
Five things, all of them cheap, and the look needs all five:
1. **Perspective tilt.** Enter with `rx` 40 to 55 degrees easing to about 5, and keep an idle `ry` wobble
   of plus or minus 5 to 10 degrees (`sin(t*1.2)*7`). Cards and phones at the sides sit at a fixed
   `ry` of about 18 to 28 degrees facing inward.
2. **Parallax.** The camera sways continuously (24 px horizontally, 13 px vertically, slow sines).
   Backgrounds move 0.3x, far objects 0.5x, normal 1x, foreground 1.6 to 2.2x. Set `depth` on every layer.
3. **Shadow separation.** The shadow is its own blurred layer, offset down-right. Raise `lift` for objects
   that float (cards 1.5, flying things 2 to 6) and lower it for things resting on a surface (0.5).
4. **Depth of field.** Far duplicates are pre-blurred and darkened (blur 2 px, 60% brightness). A rack
   focus is a crossfade to a blurred, darker copy of the background while a foreground object pops in.
5. **Light.** A diagonal glint sweeps across metal once after it lands. Tilted layers get brighter or
   darker with the tilt (the engine does this).

Avoid strong tilts on photo cutouts; beyond about 30 degrees they visibly stretch.

## Grading a cutout to its scene
`grade(img, amb, s, rim, rim_k, top, bot, under, sat)`:
- `amb`, `s`: tint towards the scene's light colour. s = 0.3 to 0.45 for most objects, up to 0.6 in
  strongly coloured scenes (purple, night).
- `top`, `bot`: vertical falloff. 1.08 to 0.75 reads as light from above; darker `bot` (0.55 to 0.7)
  for tall figures standing in a dark place.
- `rim`: edge light in the background's colour (pink on purple, orange in the factory, gold on yellow).
  rim_k 0.4 to 0.6 for products, 0.8 to 1.1 for people and dramatic scenes.
- `under`: bounce light from below (blue from a gas flame, orange from a city or fire).
- `sat`: pull saturation down to 0.25 to 0.7 to make something look unhealthy or cold.
An ungraded cutout looks pasted on. This single step is what users notice as "quality".

## Motion vocabulary
| Move | How | Use for |
|---|---|---|
| Pop | `pop(t, t0)` on scale, small rotation settling | any entrance |
| Flip-in | `rx=(1-p)*55` plus slide from below | cards, pages, phones |
| Drop | fall from above with `min(1,q)**2`, then a splash ring or bounce | food into a pot, items into a pile |
| Slam | `slam()` : fast drop, dust ring, canvas shake | the reveal object, stamps |
| Multiply | same sprite several times, staggered 0.15 to 0.25 s, offset and rotated | "everyone is saying it" |
| Draw-on | `reveal()` / `draw_on()` on a stroke image | arrows, crosses, ticks, highlighter |
| Swing | rotation about the top anchor, decaying sine | hanging tags |
| Flip tag | `ry` 0 to 90 with one sprite, 90 to 0 with the other | SAFE becoming "?" |
| Particles | deterministic `random.Random(seed)` per frame, phase from time | beads, sparks, bubbles, smoke |
| Group zoom | `Grp(F, C, Z)` maps every layer about one point | push in on one row or one object |
| Rewind | play the previous shot's time backwards with streaks and torn scan bands | "but it's not that simple" |

Every object keeps a small idle motion after it lands. A layer that stops completely looks dead.

## Captions
- Two lines, top-left, Anton, all caps. Line 1 at 74 px white; line 2 at 116 px with a vertical gradient,
  a glow in its own colour and a soft drop shadow. Long lines shrink automatically to fit 930 px.
- Line 1 appears with the first word of the sentence, line 2 on the punch word. Each caption stays until
  the next one starts.
- 2 to 5 words per line. Summarise the claim; do not transcribe the sentence.
- Colour follows meaning: red for danger and verdicts, teal for body and chemistry, blue for calm or
  kitchen, pink for social media, yellow and orange for fire and industry.

## Transitions
Centre each one on the scene change, 0.35 to 0.45 seconds long.
- `h` / `v` whip pan: default between unrelated scenes; alternate direction.
- `zoom`: punch through the subject into the next scene. Use when the next scene is "inside" or "more
  about" the thing on screen (a highlighted word, a pot, an organ).
- `fade`: blurred dissolve, for the same subject continuing in a new place.
- `flash` / `smoke`: a white or grey cover, for steam and smoke.
- No transition at all when a moving element carries over (beads holding position while the background
  changes). That match cut is the strongest transition available; plan one or two per film.

## Finish
`finish_overlay()` adds the crease line at 62% width, punch-hole dots down the left edge, a vignette, a
darker top band behind captions, and grain is added per frame. Do not skip it: it is what makes drawn
art, photos and cutouts look like one piece.

## Sound
Whoosh on each transition, thud on impacts, pop on entrances, scribble on drawn strokes, a low bed for
fire or cooking. Effects at about 0.4 against the voice.
