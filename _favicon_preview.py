"""Render side-by-side previews of the generated favicon assets (temp helper)."""
import os

from PIL import Image

OUT_IMG = "staticfiles/image"

# 1) enlarged view of the squarified emblem crop (rebuild it here for inspection)
from _make_favicon import masked, bbox, l, r, t, b  # reuse generation logic

region = masked.crop((max(l, 0), max(t, 0), min(r, 1631), min(b, 964)))
side = max(r - l, b - t)
sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
sq.paste(region, ((side - region.width) // 2, (side - region.height) // 2))
crop_big = sq.resize((300, 300), Image.LANCZOS)

# 2) the actual small assets, shown enlarged on a neutral + a dark card
cards = []
for name in ("favicon-32x32.png", "favicon-16x16.png"):
    p = os.path.join(OUT_IMG, name)
    im = Image.open(p).convert("RGBA")
    big = im.resize((128, 128), Image.NEAREST)
    cards.append(("light", name, big))

touch = Image.open(os.path.join(OUT_IMG, "apple-touch-icon.png")).convert("RGBA")
cards.append(("light", "apple-touch-icon.png", touch.resize((128, 128), Image.LANCZOS)))

sheet = Image.new("RGB", (3 * 160, 300 + 200), (238, 238, 238))
# row 1: crop on checker + on dark
checker = Image.new("RGB", (300, 300), (200, 200, 200))
sheet.paste(checker, (10, 10))
sheet.paste(crop_big, (10, 10), crop_big)
dark = Image.new("RGB", (300, 300), (20, 25, 30))
sheet.paste(dark, (330, 10))
sheet.paste(crop_big, (330, 10), crop_big)
# row 2: small assets
x = 10
for bg, name, img in cards:
    tile = Image.new("RGB", (img.width, img.height), (255, 255, 255))
    tile.paste(img, (0, 0), img)
    sheet.paste(tile, (x, 330))
    x += img.width + 32

sheet.save("_favicon_preview.png")
print("emblem bbox:", bbox, "| preview saved")
