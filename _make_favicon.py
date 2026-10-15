"""Generate favicon assets from the site logo (temp helper — safe to delete).

Extracts the circular globe emblem (top of the logo) — the wordmark banner
below it would be illegible at 16/32px — squares it, and writes:
  image/favicon.ico            (16, 32, 48 px layers)
  image/favicon-16x16.png
  image/favicon-32x32.png
  image/apple-touch-icon.png   (180x180, opaque white background)
"""
import os
from PIL import Image, ImageChops

SRC = "staticfiles/image/logo.png"
OUT = "staticfiles/image"

im = Image.open(SRC).convert("RGBA")
w, h = im.size
alpha = im.getchannel("A")
# The banner has a faint top glow (alpha <= ~32) that reaches across the full
# width — threshold it away for DETECTION, and drop it from the OUTPUT too,
# while keeping soft anti-aliased edges above the threshold.
strong = alpha.point(lambda v: 255 if v > 32 else 0)
masked = im.copy()
masked.putalpha(ImageChops.multiply(alpha, strong))

# Banner detection uses row SPAN (not pixel count): row 519 already reaches
# 1085px wide but its semi-transparent gradient holds few countable pixels.
def _row_span(y):
    bb = strong.crop((0, y, w, y + 1)).getbbox()
    return (bb[2] - bb[0]) if bb else 0

banner_top = next((y for y in range(h) if _row_span(y) > 0.5 * w), h)

# Emblem = strong content of everything above the banner.
bbox = strong.crop((0, 0, w, banner_top)).getbbox()
print("logo %dx%d  banner_top=%s  emblem bbox=%s" % (w, h, banner_top, bbox))

l, t, r, b = bbox
pad = int(0.04 * max(r - l, b - t))  # small breathing room
l, t, r, b = l - pad, t - pad, r + pad, b + pad

# Square the emblem on a transparent canvas (centered).
ew, eh = r - l, b - t
side = max(ew, eh)
canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
region = masked.crop((max(l, 0), max(t, 0), min(r, w), min(b, h)))
canvas.paste(region, ((side - region.width) // 2, (side - region.height) // 2))
print("squared emblem: %dpx" % side)

# PNG sizes
canvas.resize((16, 16), Image.LANCZOS).save(os.path.join(OUT, "favicon-16x16.png"))
canvas.resize((32, 32), Image.LANCZOS).save(os.path.join(OUT, "favicon-32x32.png"))

# Multi-size .ico (browsers that still auto-request it / older clients)
canvas.resize((48, 48), Image.LANCZOS).save(
    os.path.join(OUT, "favicon.ico"),
    sizes=[(16, 16), (32, 32), (48, 48)],
)

# Apple touch icon — must be opaque; white matches the site navbar background.
touch = Image.new("RGBA", (180, 180), (255, 255, 255, 255))
globe = canvas.resize((156, 156), Image.LANCZOS)
touch.paste(globe, (12, 12), globe)
touch.convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"))

for f in ("favicon.ico", "favicon-16x16.png", "favicon-32x32.png", "apple-touch-icon.png"):
    p = os.path.join(OUT, f)
    print("%-24s %6d bytes" % (f, os.path.getsize(p)))
print("done")
