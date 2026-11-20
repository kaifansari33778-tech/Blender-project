# Sourcing and cutting images

## Where images can come from
1. **The user** (their own photos or AI-generated cutouts). Best quality. Ask early.
2. **Wikimedia Commons** via `scripts/commons.py`. Free licences, reachable from most sandboxes.
3. **Drawn with Pillow.** Always the right choice for documents, phones, chat cards, tags, tiles, stamps,
   badges and anything with text. The engine has these; follow their flat-shaded look for new ones.

In the sandbox this was built in, these hosts were reachable: commons.wikimedia.org, upload.wikimedia.org,
raw.githubusercontent.com (fonts), GitHub release downloads (the rembg and Whisper models), PyPI.
Unsplash, Pexels, Pixabay, Flickr, Openverse, Poly Haven and Hugging Face were blocked. Test quickly with
`curl -s -o /dev/null -w "%{http_code}" <url>` before planning around a source, and read the environment's
network documentation if a needed host is blocked.

## Commons rules learned the hard way
- Thumbnails are only served at fixed widths (500, 960, 1280, 1920, 3840). Any other width returns an
  error page that looks like a successful download. `commons.py` snaps to a valid width.
- It rate-limits with HTTP 429. One process at a time, a couple of seconds between calls, retry with
  growing waits. A batch of 30 images can take 15 minutes; run it in the background and keep working.
- Never run two fetches at once.
- After every fetch, check file sizes and look at the sheet. A 3 KB "jpg" is an error page.

## Search queries that work
Commons search is literal and uneven. Search several phrasings at once and expect half to be useless.
- Add "isolated", "white background" or "model" for cutout-friendly product shots.
- Museum and anatomical models photograph well: "kidney anatomical model", "human lungs model".
- Processes: search the activity, not the object: "aluminium pot casting", "pouring molten aluminium".
- Try another language for everyday objects ("Kochtopf Aluminium", "marmite aluminium").
- 3D medical illustrations exist for many organs: "intestinal villi", "red blood cells blood vessel".
- Top-down food on a dark table cuts out cleanly: "roast chicken plate".

Choose by: clean background, 3/4 or top view that matches the scene's camera, at least 1000 px on the
subject, no visible brand names, no identifiable private person's face.

## Cutouts
`commons.py fetch ... :cut` runs rembg (model `isnet-general-use`) and crops to the subject. Then always
run `commons.py sheet` and look. Typical failures and fixes:

| Failure | Fix |
|---|---|
| Plate removed, only the food left | draw a plate (two ellipses) and paste the food on it |
| Hand removed, only the fork/phone left | accept the object alone, or find a photo with a plain background |
| Subject comes with a large machine or second person | crop the raw photo to the subject first, then cut |
| Ghostly, half-transparent result (shiny metal, glass, clutter) | use the photo as a framed card with `framed()` |
| Faint rectangle or haze around the subject | threshold the alpha: `clip((a - 0.6) * 3.5, 0, 1)` |
| Screen of a phone becomes transparent | good: find the hole (largest transparent region not touching the border), fit a quad, and warp your own screen into it (see `s_phone` in the example film) |

Source photos smaller than about 600 px on the subject look soft when used large; use them small or as
background-distance objects.

## Background photos
`photo(key, tint, s, contrast, vig, blur_r, focus)` cover-crops to 1400x2490 so there is room for camera
movement. Tint them towards the chapter colour (s 0.3 to 0.6), add vignette 0.4 to 0.5, and keep a blurred
darker copy for rack focus. A landscape photo cropped to portrait loses most of its width; use `focus` to
choose which part survives.

## Licences
`commons.py` stores title, author and licence for everything fetched; `commons.py credits WORK` prints the
table. Most results are CC BY or CC BY-SA, which require attribution (and share-alike for derivatives).
Tell the user this when handing over the video and give them the table.

## Documents and on-screen claims
Draw documents as generic illustrations of what the narration says. Do not copy an organisation's logo
or letterhead, and do not present a drawn notice as the genuine document. If the script makes factual
claims you have not checked, say so in the handover.
