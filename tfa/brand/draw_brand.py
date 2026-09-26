#!/usr/bin/env python3
"""Draw the Thinking Fish Assist brand artwork as clean SVG.

Source: Andrew's icon sheet v2 of 26 Sep 2026 19:07
(reference/andrew-icon-sheet-v2-2026-09-26.jpg; it supersedes his first sheet,
kept alongside for the record). The sheet is an AI-generated JPEG, so nothing
here is traced or upscaled from it: every shape is redrawn from measurements
taken off the sheet, and the colours were sampled from it (median of each
colour region) and then settled on clean values. See the PALETTE comments.

What Andrew drew, and what this script makes of it:
  * the MARK (his small tiles): a white headset with an orange mic dot at the
    end of the boom, centred on a navy, white or black tile. No swoosh. App
    icons use the mark only.
  * the FULL LOGO (his large tile and the medium white/black ones): the
    headset above the "thinkingfish" wordmark (thinking white or navy, fish
    orange), one blue swoosh sweeping from its lower left round the right of
    "fish" and back underneath, and "ASSIST" in spaced capitals. Used where
    there is room: About box, installer, website hero, guides.

Run from the repo root:  python3 tfa/brand/draw_brand.py   (then make_icons.py)
Needs: rsvg-convert, Pillow, fontTools. The two fonts are OFL subsets kept in
fonts/ (Open Sans ExtraBold Italic for the wordmark, Montserrat Medium for
ASSIST); the text is converted to outlines, so the SVGs need no fonts to render.

Geometry is written in the "mark grid": units of an 800px enlargement of
Andrew's small tiles. The headset is centred on x=400 there, with the band's
outer edge 216 either side. place() maps that grid into any target box,
centring the mark by its real rendered bounding box (not by eye), so every
icon has equal margins.
"""
import io
import subprocess
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

BRAND = Path(__file__).resolve().parent
FONTS = BRAND / "fonts"

# ---------------------------------------------------------------- palette
# Sampled from the sheet (median of each region), then settled on clean values.
ORANGE = "#EA692E"       # mic dot + "fish". Sheet median #F66B2D..#FA6D2C (JPEG highlights
                         # push it brighter); #EA692E is the Thinking Fish orange and sits
                         # inside the sheet's 25th percentile, so we use the brand value.
NAVY_INK = "#0A1F3F"     # headset + "thinking" on the white tile (sheet #021938 / #071A38)
BLACK_TILE = "#0C0C0C"   # black tile (sheet #0C0C0C)
# Tile gradient: bright blue rim at top-left (sheet #0A5CB0 top edge) down to deep navy
# (sheet centre #061D3D, bottom-right #01132C).
TILE_STOPS = [(0, "#0C4E9E"), (0.32, "#082A5C"), (0.7, "#051B3D"), (1, "#021129")]
# Swoosh on dark: bright at the top tail (sheet #1679EA..#208FF9), deeper at the bottom (#0452B4).
SWOOSH_DARK = [(0, "#3C9BF8"), (0.4, "#1471E0"), (1, "#0550B8")]
SWOOSH_LIGHT = [(0, "#1C6FD6"), (1, "#05449C")]      # white tile (sheet #0551A7)
HEADSET_WHITE = [(0, "#FFFFFF"), (1, "#DDE8F5")]    # the sheet's headset is shaded slightly blue at the foot


def grad(id_, stops, x1=0, y1=0, x2=0, y2=1, user=False):
    """Linear gradient. user=True spans absolute mark-grid coordinates instead of each
    shape's own box: the headset is several overlapping shapes, and per-shape
    gradients would show seams where the boom and legs run into the ear cups."""
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    u = ' gradientUnits="userSpaceOnUse"' if user else ""
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{u}>{s}</linearGradient>'


def headset_grad(id_):
    return grad(id_, HEADSET_WHITE, 0, 188, 0, 660, user=True)


# ---------------------------------------------------------------- the mark
def headset(fill, dot=ORANGE, bold=False):
    """Headband, ear cups, boom and mic dot, in mark-grid units (v2 sheet, 26 Sep 19:07).

    Measured off an 800 px enlargement of Andrew's small tiles: the headset is
    centred on x=400; the band's outer edge is 216 either side and its top is at
    y=188; the left leg runs on below its ear cup and ends round; the boom leaves
    the bottom of the right cup and curls left into the orange mic dot, which sits
    just right of centre at the bottom.
    bold=True is the small-size master (16-32 px): heavier strokes, bigger dot,
    because at 16 px a 50-unit band is under a pixel and a half.
    """
    band = 72 if bold else 50            # headband stroke (sheet: ~50)
    boom = 56 if bold else 40            # boom stroke (sheet: ~0.8 of the band)
    HW = 216                             # outer half-width of the band
    cx, cy = 400, 360                    # centre of the arch; sides are vertical below it
    r = HW - band / 2                    # horizontal centreline radius
    ry = (cy - 188) - band / 2           # vertical centreline radius: outer top at y=188
    cw, ch = (104, 176) if bold else (93, 165)   # ear cup size
    cup_y = 364 if bold else 368
    over = 58                            # how far a cup sticks out beyond the band
    lx = cx - HW - over                  # left cup x
    rx_ = 2 * cx - lx - cw               # right cup, mirrored
    leg_end = cup_y + ch + 18            # the left leg shows below its cup (sheet: ~y550)
    dot_r = 70 if bold else 60
    dot = (f'<circle cx="{cx + 20}" cy="{cup_y + ch + 57}" r="{dot_r}" fill="{dot}"/>')
    # Cups are D-shaped on the sheet: large radius outside, small inside.
    def cup(x, outer_left):
        ro, ri = (50, 18) if bold else (44, 16)
        y, w, h = cup_y, cw, ch
        tl, tr, br, bl = (ro, ri, ri, ro) if outer_left else (ri, ro, ro, ri)
        return (f'<path d="M {x+tl} {y} H {x+w-tr} Q {x+w} {y} {x+w} {y+tr} V {y+h-br} '
                f'Q {x+w} {y+h} {x+w-br} {y+h} H {x+bl} Q {x} {y+h} {x} {y+h-bl} V {y+tl} '
                f'Q {x} {y} {x+tl} {y} Z" fill="{fill}"/>')
    by = cup_y + ch + 64                 # boom's horizontal run (just under the dot's centre)
    bx = rx_ + cw * 0.3                  # where the boom leaves the right cup
    return (
        # arch + legs. Round caps: the left leg's end shows under its cup, as drawn.
        f'<path d="M {cx-r} {leg_end} V {cy} A {r} {ry} 0 0 1 {cx+r} {cy} V {cup_y+ch-30}" '
        f'fill="none" stroke="{fill}" stroke-width="{band}" stroke-linecap="round"/>'
        + cup(lx, True) + cup(rx_, False)
        # boom: out of the bottom of the right cup, round the corner, left to the mic
        + f'<path d="M {bx:.0f} {cup_y+ch-40} V {cup_y+ch+6} C {bx:.0f} {by-10}, {bx-22:.0f} {by}, '
          f'{bx-60:.0f} {by} L {cx+40} {by}" fill="none" stroke="{fill}" stroke-width="{boom}" '
          f'stroke-linecap="round" stroke-linejoin="round"/>'
        + dot
    )


def mark(theme="dark", bold=False, ids="m"):
    """(defs, body) for the app-icon mark: the headset and mic dot only (v2: no swoosh).
    theme: dark (white headset, for navy/black tiles), light (navy headset, white tile),
    mono-white / mono-black (single colour: tray template, Android monochrome + notification)."""
    if theme == "dark":
        return headset_grad(f"{ids}hs"), headset(f"url(#{ids}hs)", ORANGE, bold)
    if theme == "light":
        return "", headset(NAVY_INK, ORANGE, bold)
    colour = "#FFFFFF" if theme == "mono-white" else "#000000"
    return "", headset(colour, colour, bold)



# ---------------------------------------------------------------- measuring + placing
_bbox_cache = {}


def bbox(body, defs=""):
    """Rendered bounding box of some mark-grid artwork (so centring is exact)."""
    key = body
    if key in _bbox_cache:
        return _bbox_cache[key]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-200 -200 1200 1200" width="1200" height="1200">'
           f'<defs>{defs}</defs>{body}</svg>')
    png = subprocess.run(["rsvg-convert"], input=svg.encode(), capture_output=True, check=True).stdout
    a = Image.open(io.BytesIO(png)).getchannel("A").point(lambda v: 255 if v > 8 else 0)
    x0, y0, x1, y1 = a.getbbox()
    _bbox_cache[key] = (x0 - 200, y0 - 200, x1 - 200, y1 - 200)
    return _bbox_cache[key]


def place(defs, body, box):
    """Scale + translate mark-grid artwork so its bbox is centred in box=(x, y, w, h),
    as large as fits."""
    x0, y0, x1, y1 = bbox(body, defs)
    bx, by, bw, bh = box
    s = min(bw / (x1 - x0), bh / (y1 - y0))
    tx = bx + (bw - (x1 - x0) * s) / 2 - x0 * s
    ty = by + (bh - (y1 - y0) * s) / 2 - y0 * s
    return f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s:.5f})">{body}</g>'


# ---------------------------------------------------------------- text as outlines
def text_path(fontfile, text, size, x, y, tracking=0.0):
    """Outline `text` (so no font is needed to render). tracking is in em."""
    f = TTFont(FONTS / fontfile)
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    s = size / upm
    pen, bp, adv = SVGPathPen(gs), BoundsPen(gs), 0.0
    for ch in text:
        g = cmap[ord(ch)]
        t = (s, 0, 0, -s, x + adv * s, y)
        gs[g].draw(TransformPen(pen, t))
        gs[g].draw(TransformPen(bp, t))
        adv += gs[g].width + tracking * upm
    return pen.getCommands(), bp.bounds


WORD_FONT = "OpenSans-ExtraBoldItalic-w90-subset.ttf"
CAPS_FONT = "Montserrat-Medium-subset.ttf"


def wordmark(x, baseline, width, thinking_fill, fish_fill, tracking=-0.035):
    """'thinking' + 'fish' set as one word, scaled so it spans exactly `width`."""
    _, b = text_path(WORD_FONT, "thinkingfish", 100, 0, 0, tracking)
    size = 100 * width / (b[2] - b[0])
    d1, b1 = text_path(WORD_FONT, "thinking", size, 0, 0, tracking)
    # 'fish' starts where 'thinking' would have continued
    f = TTFont(FONTS / WORD_FONT)
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    adv = sum(gs[cmap[ord(c)]].width + tracking * upm for c in "thinking") * size / upm
    dx = x - b1[0]
    d1, _ = text_path(WORD_FONT, "thinking", size, dx, baseline, tracking)
    d2, _ = text_path(WORD_FONT, "fish", size, dx + adv, baseline, tracking)
    return f'<path d="{d1}" fill="{thinking_fill}"/><path d="{d2}" fill="{fish_fill}"/>', size


def caps(text, cx, baseline, width, fill):
    """Wide-tracked capitals ('ASSIST'), centred on cx, spanning `width`."""
    tr = 0.62                                           # the sheet's very open tracking
    _, b = text_path(CAPS_FONT, text, 100, 0, 0, tr)
    size = 100 * width / (b[2] - b[0])
    _, b = text_path(CAPS_FONT, text, size, 0, 0, tr)
    d, _ = text_path(CAPS_FONT, text, size, cx - (b[0] + b[2]) / 2, baseline, tr)
    return f'<path d="{d}" fill="{fill}"/>'


# ---------------------------------------------------------------- documents
def svg(w, h, defs, body, comment):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'
            f'  <!-- {comment} Generated by tfa/brand/draw_brand.py; edit that, not this. -->\n'
            f'  <defs>{defs}</defs>\n  {body}\n</svg>\n')


def tile_bg(x, y, size, rx, kind="navy", ids="t"):
    if kind == "navy":
        d = grad(f"{ids}bg", TILE_STOPS, 0.15, 0, 0.85, 1)
        # soft light from the top-left, as on the sheet's rim
        d += (f'<radialGradient id="{ids}gl" cx="0.22" cy="0.08" r="0.75">'
              f'<stop offset="0" stop-color="#2E8AF0" stop-opacity="0.28"/>'
              f'<stop offset="1" stop-color="#2E8AF0" stop-opacity="0"/></radialGradient>')
        b = (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{rx}" fill="url(#{ids}bg)"/>'
             f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{rx}" fill="url(#{ids}gl)"/>')
        return d, b
    fill = "#FFFFFF" if kind == "white" else BLACK_TILE
    b = f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{rx}" fill="{fill}"/>'
    if kind == "white":   # hairline so a white tile doesn't vanish on a white page
        b += (f'<rect x="{x+3}" y="{y+3}" width="{size-6}" height="{size-6}" rx="{rx-3}" '
              f'fill="none" stroke="#E2E6EE" stroke-width="6"/>')
    return "", b


# Mark size inside a tile: the headset's bbox takes 70% of the tile's width, as on
# Andrew's small tiles (0.70); the bold small-size master takes 78%.
MARK_IN_TILE = 0.70
MARK_IN_TILE_BOLD = 0.78


def app_tile(kind="navy", bold=False, size=1024, inset=0, rx_frac=0.2237):
    """A rounded tile with the mark centred. inset>0 leaves transparent margin (macOS grid)."""
    t = size - 2 * inset
    d, b = tile_bg(inset, inset, t, round(t * rx_frac), kind)
    theme = "light" if kind == "white" else "dark"
    md, mb = mark(theme, bold)
    f = MARK_IN_TILE_BOLD if bold else MARK_IN_TILE
    m = t * f
    return d + md, b + place(md, mb, (inset + (t - m) / 2, inset + (t - m) / 2, m, m))


def wordmark_block(dark=True, ids="W"):
    """'thinkingfish' with the blue swoosh sweeping from its lower left, round the
    right of 'fish' and back underneath, then ASSIST below. Laid out on the large
    tile's own 1000-unit grid (v2 sheet): wordmark x 100-830, baseline 728; swoosh
    tip at (470,566), out to x=945, tail under 'fish' to (590,782); ASSIST baseline 862.
    Returns (defs, body)."""
    sw = SWOOSH_DARK if dark else SWOOSH_LIGHT
    d = grad(f"{ids}sw", sw, 0, 0, 1, 1)
    ink = f"url(#{ids}wm)" if dark else NAVY_INK
    if dark:
        d += grad(f"{ids}wm", HEADSET_WHITE)
    b = ('<path d="M 470 566 C 700 546, 945 588, 945 650 C 945 716, 800 770, 590 783 '
         'C 782 762, 914 712, 914 655 C 914 604, 720 572, 470 566 Z" fill="url(#%ssw)"/>' % ids)
    wm, _ = wordmark(100, 728, 730, ink, ORANGE)
    b += wm
    b += caps("ASSIST", 500, 862, 590, "#FFFFFF" if dark else NAVY_INK)
    return d, b


def full_logo_tile(kind="navy"):
    """Andrew's large tile (v2): the headset above, then the wordmark block. Drawn on
    the sheet's 1000-unit grid into a 1024 canvas."""
    d, b = tile_bg(0, 0, 1000, 200, kind, ids="L")
    dark = kind != "white"
    ink = "url(#Lhs)" if dark else NAVY_INK
    d += headset_grad("Lhs")
    # headset: sheet centre x=501, band outer half-width 189 (ours is 216) -> scale 0.875,
    # band top at y=148 (ours at 188)
    s_ = 189 / 216
    b += f'<g transform="translate({501 - 400 * s_:.1f} {148 - 188 * s_:.1f}) scale({s_:.4f})">{headset(ink)}</g>'
    wd, wb = wordmark_block(dark, ids="L")
    return d + wd, f'<g transform="scale(1.024)">{b}{wb}</g>'


def lockup(theme="dark"):
    """Horizontal lockup for the app header, installer banner and web: the headset,
    then the wordmark block (thinkingfish + swoosh + ASSIST). 720 x 180 viewBox."""
    md, mb = mark(theme, ids="k")
    b = place(md, mb, (6, 18, 170, 144))
    wd, wb = wordmark_block(theme == "dark", ids="k")
    # the block spans x 95-948, y 546-866 on its grid: fit it into x 196-714, y 10-172
    s_ = min((714 - 196) / (948 - 95), (172 - 10) / (866 - 546))
    b += f'<g transform="translate({196 - 95 * s_:.1f} {10 - 546 * s_:.1f}) scale({s_:.4f})">{wb}</g>'
    return md + wd, b



def android_foreground(theme="dark"):
    """Adaptive icon foreground, 108dp canvas: keep the mark inside the 66dp safe circle.
    The headset's bbox diagonal must fit the safe circle, so it gets 56% of the width."""
    md, mb = mark(theme, ids="a")
    s = 1024 * 0.56
    return md, place(md, mb, ((1024 - s) / 2, (1024 - s) / 2, s, s))


def main():
    out = {}
    d, b = app_tile("navy"); out["icon.svg"] = svg(1024, 1024, d, b, "App icon: mark on the navy tile, full bleed (Windows, Android legacy, in-app).")
    d, b = app_tile("navy", bold=True); out["icon-small.svg"] = svg(1024, 1024, d, b, "Small-size master (16-32 px): heavier strokes so the mark survives.")
    d, b = app_tile("white"); out["icon-white.svg"] = svg(1024, 1024, d, b, "Mark on the white tile (Andrew's second variant).")
    d, b = app_tile("black"); out["icon-black.svg"] = svg(1024, 1024, d, b, "Mark on the black tile (Andrew's third variant).")
    # macOS Big Sur grid: 824 tile centred in 1024 with a soft shadow below
    d, b = app_tile("navy", inset=100, rx_frac=0.2237)
    d += ('<filter id="sh" x="-10%" y="-10%" width="120%" height="125%"><feDropShadow dx="0" dy="10" '
          'stdDeviation="12" flood-color="#000" flood-opacity="0.30"/></filter>')
    out["icon-macos.svg"] = svg(1024, 1024, d, f'<g filter="url(#sh)">{b}</g>', "macOS app icon: 824 px tile + shadow in a 1024 canvas.")
    for theme in ("dark", "light", "mono-white", "mono-black"):
        md, mb = mark(theme)
        out[f"mark-{theme}.svg"] = svg(1024, 1024, md, place(md, mb, (32, 32, 960, 960)), f"The mark alone ({theme}), centred, transparent.")
    md, mb = mark("dark"); out["mark.svg"] = out["mark-dark.svg"]
    d, b = full_logo_tile("navy"); out["logo-tile.svg"] = svg(1024, 1024, d, b, "Full logo: Andrew's large tile.")
    d, b = full_logo_tile("white"); out["logo-tile-white.svg"] = svg(1024, 1024, d, b, "Full logo on white.")
    d, b = lockup("dark"); out["logo-dark.svg"] = svg(720, 180, d, b, "Horizontal lockup for dark backgrounds.")
    d, b = lockup("light"); out["logo-light.svg"] = svg(720, 180, d, b, "Horizontal lockup for light backgrounds.")
    d, b = android_foreground("dark"); out["android-foreground.svg"] = svg(1024, 1024, d, b, "Android adaptive foreground (108dp canvas, 66dp safe zone).")
    md, mb = mark("mono-white", ids="a")
    s = 1024 * 0.56
    out["android-monochrome.svg"] = svg(1024, 1024, md, place(md, mb, ((1024 - s) / 2, (1024 - s) / 2, s, s)), "Android 13 themed-icon layer (alpha only).")
    d, b = tile_bg(0, 0, 1024, 0, "navy", ids="g")
    out["android-background.svg"] = svg(1024, 1024, d, b, "Android adaptive background: the navy tile, square (the launcher masks it).")
    for name, text in out.items():
        (BRAND / name).write_text(text)
        print("wrote tfa/brand/" + name)


if __name__ == "__main__":
    main()
