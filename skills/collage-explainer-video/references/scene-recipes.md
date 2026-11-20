# Scene recipes

Patterns that were built and checked in the example film (`example_film/film.py`, `example_film/sample.py`).
All use `import engine as E` names; `t` is absolute film time; `c = E.new()` is the canvas.
Coordinates are screen pixels on 1080x1920.

## Skeleton of a scene
```python
def s_name(t):
    c = new(); k = ease(seg(t, T0, T1))                 # 0..1 over the scene, for slow camera moves
    bg_pan(c, BG, 750, 1200 + 20 * k, 1.0)              # background (flat_bg is 1500x2400: centre 750,1200)
    p = pop(t, T0 + .3)
    if p > 0: obj(c, THING, 540, 1000 + (1 - p) * 700, 1.0, rot=(1 - p) * 10, rx=(1 - p) * 45, ry=sin(t * 1.2) * 6)
    return c
```
For a photo background use `bg_pan(c, PHOTO, 700 + dx * k, 1245 + dy * k, lerp(.84, 1.0, k))`: photos are
1400x2490, zoom must stay at or above 0.80 to cover the frame, and a slow push sells depth.

## Object on a heat source (pot on a flame)
Screen-blend a flame photo that has a black background (`place(..., add=True)`), flicker its scale with
two fast sines, draw the pot over it with a blue `under=` bounce in its grade, add `steam()` above, and
sweep one glint across the metal 0.5 s after it lands.

## Card that multiplies
Draw one card; place it three times, back to front, with staggered `pop` times, offsets of 60 to 150 px,
rotations of plus or minus 5 degrees, increasing `depth` (1.2, 1.55, 1.9) so they slide apart with the camera.

## Scene shrinks into a phone screen
Render the previous scene into a buffer, warp it with `cv2.warpPerspective` into the phone's screen quad,
multiply by the screen-hole mask, draw the hand-and-phone cutout over it. Start with the hand scaled so the
screen fills the frame and ease it down (`s0 * (s1/s0) ** k`). See `s_phone` in `example_film/sample.py`.

## Wall of duplicates with depth
Loop a shuffled 7x7 grid; give each copy a random depth 0.75 to 1.1, scale and spacing by depth, random
`rx`/`ry` up to 28 degrees, a stagger of 0.016 s, and use a pre-blurred darker sprite when depth < 0.9.
Keep one hero copy sharp in the centre with the strongest parallax.

## Document with highlighter, then push in
Draw the document so you know the row geometry. Use `Grp(F, C, Z)` with F at the row and animate Z from 1
to about 1.7; send every layer's position through it. Reveal a translucent highlight bar left to right
and move a marker cutout with its tip. Fade out side cards as the zoom starts. Keep the zoom target near
y 1240 so the document header does not slide under the caption.

## Through the window, then rewind
Layers back to front: sky/city photo (depth 0.15), the thrown object while it is beyond the window, a
wall texture with a transparent window hole, the object while it is inside. Scale the wall up fast about
the window centre and fade it out to "pass through". For the rewind, call the same forward function with
time running backwards, mix in a wide horizontal blur and roll five random horizontal bands sideways.

## Evidence desk
Object with a hanging tag (decaying swing), a magnifier following `path()` with `lens()` magnifying what
is under it, an evidence bag whose label text fades to blank, then `STAMP` arriving blurred and leaving an
ink sprite with a 0.1 s scale punch and a 0.3 s canvas shake.

## Rack focus to foreground objects
Crossfade the background to its blurred darker copy over 0.45 s, slide the previous foreground subject
out, and pop the new objects in at depth 1.5 to 1.7. Grow dark spots on them with `dark_spot()` sprites
whose scale and opacity ease up over a second.

## Comparison ghost
Place a soft-edged crop of the other scene (ellipse alpha mask) above the subject at 85% opacity, draw a
red cross over it stroke by stroke, fade it away. Keep it clear of the subject or it reads as transparency.

## Beads: surface, grid, fall, travel
One list of 100 positions on the food and one 10x10 grid. Beads pop on staggered by 0.013 s, bob, then
each eases from its food position to its grid cell along a small arc. Draw the grid lines as they arrive,
pop a badge, dim all but one and give that one an additive glow. Next scene: same grid positions on a new
background (match cut), 99 fall with `2600 * dt**2` staggered by row, the lit one stays and then travels.

## Zoom chain
Give each step its own short scene (1.2 to 1.6 s) and join them with `zoom` transitions: tissue, vessel,
organ. Carry one glowing element through all of them. End with an inset circle (`cv2.circle` fill, the
detail cutout, a gold ring) that pops beside the organ.

## Shelf with flipping tags
Wall + `shelf_plank()` + cutouts placed by their bottom edge (`y - height/2`). Tags hang from an anchor
at the top with a small swing; flip with `ry` 0 to 90 showing the first sprite, then 90 to 0 showing the
second, staggered 0.13 s. The same function with `tags=False` and a `Grp` zoom gives the "this one is the
danger" push-in; add a red edge glow and a warning triangle.

## Macro liquid and things dropping in
Photo of the liquid filling the frame, slow zoom, 4% brightness shimmer, objects falling with `min(1,q)**2`
and `splash()` rings at the landing point, then small square grains for salt.

## Micro surface
`micro_surface()` style: a Voronoi tile texture placed with `rx` about 60 as a ground plane, crossfaded to
a pitted version, with beads rising from the pits (use `proj()` to find where a texture point lands on
screen). Fade the far edge of the plane into the liquid colour.

## Top-down choice
Two versions of an object one above the other, a tick drawn on the good one, items dropping onto the bad
one each followed by a red cross. Make the objects large (1.7x): top-down shots look empty fast.

## Tile reveal
A light tile pops; the dark tile `slam()`s beside it on the keyword with a dust ring and shake. For
"not A, it is B": slide A out with rotation and `ry`, then slam B in the centre. Do not leave the frame
empty for more than half a second between them.

## Pile-up with a counter
Precompute a pyramid of positions; drop items staggered by 0.065 s with a small bounce; show
`num_sprite(int(N * ease(...)))` counting up beside a pinned paper. To single one out, dim everything to
60%, enlarge that item with a red glow behind it and pop a label tag.

## Outro
Three or four of the film's objects on a shelf, then comment bubbles popping in one by one with slight
rotation. Caption asks the question.
