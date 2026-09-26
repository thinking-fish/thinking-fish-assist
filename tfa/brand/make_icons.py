#!/usr/bin/env python3
"""Render every Thinking Fish Assist icon/logo asset from the SVG sources here.

Run from the repo root:  python3 tfa/brand/make_icons.py
Needs: rsvg-convert (librsvg2-bin), Pillow, and the Geist font installed
(https://vercel.com/font, SIL OFL) for the wordmark.

It overwrites the upstream RustDesk artwork in place, so the rest of the build
(Flutter, WiX, cargo-bundle, Android) picks the new images up without any
other change. Re-run it after pulling a new upstream release.
"""
import io
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "tfa" / "brand"
ICON = BRAND / "icon.svg"            # full-bleed white tile (Windows, Android legacy, in-app)
ICON_MAC = BRAND / "icon-macos.svg"  # Big Sur grid: 824px tile + shadow in a 1024 canvas
MARK = BRAND / "mark.svg"            # the mark alone, transparent


def render(svg: Path, w: int, h: int | None = None) -> Image.Image:
    args = ["rsvg-convert", "-w", str(w)] + (["-h", str(h)] if h else []) + [str(svg)]
    return Image.open(io.BytesIO(subprocess.check_output(args))).convert("RGBA")


def save_png(img: Image.Image, rel: str):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p, optimize=True)
    print("wrote", rel, img.size)


def silhouette(img: Image.Image, colour=(255, 255, 255)) -> Image.Image:
    """Same shape, one colour - for tray templates and Android notification icons."""
    out = Image.new("RGBA", img.size, colour + (0,))
    out.putalpha(img.getchannel("A"))
    return out


def padded(img: Image.Image, canvas: int, inner: int) -> Image.Image:
    c = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    m = img.resize((inner, inner), Image.LANCZOS)
    c.alpha_composite(m, ((canvas - inner) // 2, (canvas - inner) // 2))
    return c


def main():
    big = render(ICON, 1024)
    mac = render(ICON_MAC, 1024)
    mark = render(MARK, 1024)

    # Desktop app icon sources
    save_png(big, "res/icon.png")
    save_png(mac, "res/mac-icon.png")
    save_png(big.resize((128, 128), Image.LANCZOS), "res/128x128.png")
    save_png(big.resize((256, 256), Image.LANCZOS), "res/128x128@2x.png")
    save_png(big.resize((32, 32), Image.LANCZOS), "res/32x32.png")
    save_png(big.resize((64, 64), Image.LANCZOS), "res/64x64.png")
    (ROOT / "res/scalable.svg").write_text(ICON.read_text())
    (ROOT / "res/icon.svg").write_text(ICON.read_text()) if (ROOT / "res/icon.svg").exists() else None

    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    big.save(ROOT / "res/icon.ico", sizes=ico_sizes)
    big.save(ROOT / "flutter/windows/runner/resources/app_icon.ico", sizes=ico_sizes)
    print("wrote res/icon.ico + flutter/windows/runner/resources/app_icon.ico")
    # Windows tray: the mark on its own reads better at 16px than a white tile
    mark.save(ROOT / "res/tray-icon.ico", sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (48, 48)])
    print("wrote res/tray-icon.ico")

    # macOS: app icon + menu-bar template (only the alpha matters for a template image)
    mac.save(ROOT / "flutter/macos/Runner/AppIcon.icns")
    print("wrote flutter/macos/Runner/AppIcon.icns")
    tpl = silhouette(padded(mark, 1024, 940), (0, 0, 0))
    save_png(tpl.resize((60, 60), Image.LANCZOS), "res/mac-tray-dark-x2.png")
    save_png(tpl.resize((48, 48), Image.LANCZOS), "res/mac-tray-light-x2.png")
    appiconset = ROOT / "flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset"
    if appiconset.exists():
        for f in appiconset.glob("*.png"):
            w = Image.open(f).size[0]
            mac.resize((w, w), Image.LANCZOS).save(f, optimize=True)
            print("wrote", f.relative_to(ROOT), (w, w))

    # Flutter in-app assets
    save_png(big.resize((256, 256), Image.LANCZOS), "flutter/assets/icon.png")
    (ROOT / "flutter/assets/icon.svg").write_text(ICON.read_text())
    for theme in ("light", "dark"):
        logo = render(BRAND / f"logo-{theme}.svg", 600)
        save_png(logo, f"flutter/assets/logo_{theme}.png")

    # Android: legacy + round launcher icons, adaptive foreground, notification icon
    dens = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
    for d, k in dens.items():
        base = f"flutter/android/app/src/main/res/mipmap-{d}"
        s = int(48 * k)
        save_png(big.resize((s, s), Image.LANCZOS), f"{base}/ic_launcher.png")
        rnd = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        mask = Image.new("L", (1024, 1024), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(mask).ellipse((0, 0, 1023, 1023), fill=255)
        white = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
        white.alpha_composite(padded(mark, 1024, 700))
        rnd.paste(white, (0, 0), mask)
        save_png(rnd.resize((s, s), Image.LANCZOS), f"{base}/ic_launcher_round.png")
        fg = int(108 * k)  # 108dp canvas, mark inside the 66dp safe zone
        save_png(padded(mark, 1024, 600).resize((fg, fg), Image.LANCZOS), f"{base}/ic_launcher_foreground.png")
        st = int(24 * k)
        save_png(silhouette(padded(mark, 1024, 920)).resize((st, st), Image.LANCZOS), f"{base}/ic_stat_logo.png")
    save_png(big.resize((256, 256), Image.LANCZOS), "fastlane/metadata/android/en-US/images/icon.png")


if __name__ == "__main__":
    main()
