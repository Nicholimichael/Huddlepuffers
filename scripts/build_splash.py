#!/usr/bin/env python3
"""
build_splash.py — render the iOS launch screens (apple-touch-startup-image) for
the home-screen install of the dashboard.

iOS only shows a startup image whose <link media="..."> matches the device's CSS
size AND pixel ratio exactly, so one PNG is rendered per device class:
  platform/assets/splash/<px_w>x<px_h>.png

The art mirrors the header crest (.hp-crest in redesign_template.html): the
mascot in a circle with the gold ring, centered on the dark broadcast background
with the body's faint gold glow — so the launch screen dissolves into the page.

Usage:
  python3 scripts/build_splash.py                  # render PNGs
  python3 scripts/build_splash.py --sync-template  # also rewrite the <link> block
                                                   # between the HP_SPLASH markers
                                                   # in platform/redesign_template.html
"""
import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "platform" / "assets" / "mascot.jpeg"
OUT = ROOT / "platform" / "assets" / "splash"
TEMPLATE = ROOT / "platform" / "redesign_template.html"

BG = (14, 11, 7)          # --bg      #0E0B07
GOLD = (216, 178, 85)     # --accent  #D8B255
GLOW = (184, 146, 62)     # body radial glow: rgba(184,146,62,.06)

# Portrait CSS size (pt) + device pixel ratio. iPhones launch portrait only —
# springboard doesn't rotate — so they get one image; iPads get both orientations.
IPHONES = [
    (440, 956, 3, "iPhone 16 Pro Max / 17 Pro Max"),
    (430, 932, 3, "iPhone 14 Pro Max / 15 Pro Max / 15 Plus / 16 Plus"),
    (428, 926, 3, "iPhone 12 Pro Max / 13 Pro Max / 14 Plus"),
    (420, 912, 3, "iPhone Air"),
    (414, 896, 3, "iPhone XS Max / 11 Pro Max"),
    (414, 896, 2, "iPhone XR / 11"),
    (414, 736, 3, "iPhone 6/7/8 Plus"),
    (402, 874, 3, "iPhone 16 Pro / 17 / 17 Pro"),
    (393, 852, 3, "iPhone 14 Pro / 15 / 15 Pro / 16"),
    (390, 844, 3, "iPhone 12 / 13 / 14 / 16e / 17e"),
    (375, 812, 3, "iPhone X / XS / 11 Pro / 12 mini / 13 mini"),
    (375, 667, 2, "iPhone 6/7/8 / SE 2 / SE 3"),
]
IPADS = [
    (1032, 1376, 2, "iPad Pro 13\" (M4+)"),
    (1024, 1366, 2, "iPad Pro 12.9\" / Air 13\""),
    (834, 1210, 2, "iPad Pro 11\" (M4+)"),
    (834, 1194, 2, "iPad Pro 11\" / Air 11\""),
    (820, 1180, 2, "iPad Air 10.9\" / iPad 10th–11th gen"),
    (834, 1112, 2, "iPad Pro 10.5\" / Air 3"),
    (810, 1080, 2, "iPad 10.2\""),
    (768, 1024, 2, "iPad 9.7\" / mini 5"),
    (744, 1133, 2, "iPad mini 6 / 7"),
]

CREST_FRACTION = 0.30     # crest diameter as a fraction of the short side
CREST_Y = 0.46            # optical center: a hair above the geometric middle
SUPERSAMPLE = 4           # anti-aliased circle edges


def crest(diameter: int) -> Image.Image:
    """The header crest at `diameter` px: gold ring, dark gap, mascot cover-cropped."""
    s = SUPERSAMPLE
    d = diameter * s
    ring = max(2 * s, round(d * 0.035))
    gap = max(1 * s, round(d * 0.030))

    layer = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((0, 0, d - 1, d - 1), fill=GOLD + (255,))
    draw.ellipse((ring, ring, d - 1 - ring, d - 1 - ring), fill=BG + (255,))

    # object-fit: cover; object-position: center 26% (matches .hp-crest img)
    src = Image.open(SRC).convert("RGB")
    side = min(src.size)
    top = round((src.height - side) * 0.26)
    left = (src.width - side) // 2
    inner = d - 2 * (ring + gap)
    photo = src.crop((left, top, left + side, top + side)).resize((inner, inner), Image.LANCZOS)
    mask = Image.new("L", (inner, inner), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, inner - 1, inner - 1), fill=255)
    layer.paste(photo, (ring + gap, ring + gap), mask)

    return layer.resize((diameter, diameter), Image.LANCZOS)


def glow(width: int, height: int, dpr: int) -> Image.Image:
    """radial-gradient(1200px 640px at 50% -260px, rgba(184,146,62,.06), transparent 72%)."""
    rx, ry = 600 * dpr, 320 * dpr
    cx, cy = width // 2, -260 * dpr
    # Draw the falloff at 1/8 scale with concentric ellipses, then upscale — smooth
    # enough at 6% alpha that no banding survives.
    k = 8
    mask = Image.new("L", (max(1, width // k), max(1, height // k)), 0)
    md = ImageDraw.Draw(mask)
    steps = 48
    for i in range(steps):
        t = 1 - i / steps                      # 1 at the edge → ~0 at the center
        r = 0.72 * t
        a = round(255 * 0.06 * (1 - t))
        md.ellipse(((cx - rx * r) / k, (cy - ry * r) / k, (cx + rx * r) / k, (cy + ry * r) / k), fill=a)
    mask = mask.resize((width, height), Image.BILINEAR)
    color = Image.new("RGB", (width, height), GLOW)
    base = Image.new("RGB", (width, height), BG)
    base.paste(color, (0, 0), mask)
    return base


def render(css_w: int, css_h: int, dpr: int, landscape: bool) -> Image.Image:
    w, h = css_w * dpr, css_h * dpr
    if landscape:
        w, h = h, w
    img = glow(w, h, dpr)
    c = crest(round(min(w, h) * CREST_FRACTION))
    img.paste(c, ((w - c.width) // 2, round(h * CREST_Y) - c.height // 2), c)
    # Palette PNG: ~4x smaller than RGB for a mostly-flat image, no visible loss.
    return img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)


def specs():
    for css_w, css_h, dpr, label in IPHONES:
        yield css_w, css_h, dpr, False, label
    for css_w, css_h, dpr, label in IPADS:
        yield css_w, css_h, dpr, False, label
        yield css_w, css_h, dpr, True, label


def filename(css_w, css_h, dpr, landscape):
    w, h = css_w * dpr, css_h * dpr
    return f"{h}x{w}.png" if landscape else f"{w}x{h}.png"


def link_tags() -> str:
    lines = []
    for css_w, css_h, dpr, landscape, label in specs():
        media = (f"screen and (device-width: {css_w}px) and (device-height: {css_h}px) "
                 f"and (-webkit-device-pixel-ratio: {dpr}) "
                 f"and (orientation: {'landscape' if landscape else 'portrait'})")
        lines.append(f'<link rel="apple-touch-startup-image" media="{media}" '
                     f'href="assets/splash/{filename(css_w, css_h, dpr, landscape)}"/>')
    return "\n".join(lines)


def sync_template() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    start, end = "<!-- HP_SPLASH:start -->", "<!-- HP_SPLASH:end -->"
    if start not in html or end not in html:
        sys.exit(f"ERROR: {TEMPLATE.name} is missing the {start} / {end} markers")
    block = f"{start}\n{link_tags()}\n{end}"
    new = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, html, count=1, flags=re.S)
    TEMPLATE.write_text(new, encoding="utf-8")
    print(f"[build_splash] synced {sum(1 for _ in specs())} <link> tags into {TEMPLATE.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sync-template", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for css_w, css_h, dpr, landscape, label in specs():
        path = OUT / filename(css_w, css_h, dpr, landscape)
        render(css_w, css_h, dpr, landscape).save(path, optimize=True)
        size = path.stat().st_size
        total += size
        print(f"  {path.name:>14}  {size/1024:6.0f} KB  {label}{' (landscape)' if landscape else ''}")
    print(f"[build_splash] {sum(1 for _ in specs())} images, {total/1024/1024:.2f} MB -> {OUT.relative_to(ROOT)}")
    if args.sync_template:
        sync_template()


if __name__ == "__main__":
    main()
