#!/usr/bin/env python3
"""Render every Thinking Fish Assist icon/logo asset from the SVG sources here.

Run from the repo root:
    python3 tfa/brand/draw_brand.py   # (re)draws the SVGs from Andrew's design
    python3 tfa/brand/make_icons.py   # renders them into the places the build reads
Needs: rsvg-convert (librsvg2-bin) and Pillow.

It overwrites the upstream RustDesk artwork in place, so the rest of the build
(Flutter, WiX, cargo-bundle, Android) picks the new images up without any
other change. Re-run it after pulling a new upstream release.

Which artwork goes where (Andrew, 26 Sep 2026: app icons use the MARK only, as
on his small tiles; the full logo with the wordmark only where there's room):
  icon.svg         mark on the navy tile: every app icon 48 px and up
  icon-small.svg   same, heavier strokes: 16/24/32 px (ICO frames, tray, tab icon)
  icon-macos.svg   Apple's grid: 824 px tile + shadow inside 1024
  mark-mono-*.svg  one-colour mark: macOS menu-bar template, Android notification
  android-*.svg    adaptive icon layers (foreground, background, monochrome)
  logo-*.svg       lockups + the full logo tile (About box, header, installer, web)
"""
import io
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "tfa" / "brand"


def render(name: str, w: int, h: int | None = None) -> Image.Image:
    """Render an SVG at the exact target size (never resize a bitmap down from 1024:
    rsvg anti-aliases at the real pixel grid, which keeps 16 px icons crisp)."""
    args = ["rsvg-convert", "-w", str(w)] + (["-h", str(h)] if h else []) + [str(BRAND / name)]
    return Image.open(io.BytesIO(subprocess.check_output(args))).convert("RGBA")


def app_icon(size: int) -> Image.Image:
    """The right master for a size: the bold one up to 32 px, the normal one above."""
    return render("icon-small.svg" if size <= 32 else "icon.svg", size)


def save_png(img: Image.Image, rel: str):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p, optimize=True)
    print("wrote", rel, img.size)


def save_ico(rel: str, sizes, pick=app_icon):
    """A Windows .ico with one hand-rendered frame per size (Pillow's own resize of a
    single image would blur the 16 px frame)."""
    frames = [pick(s) for s in sizes]
    frames[-1].save(ROOT / rel, format="ICO", sizes=[(s, s) for s in sizes], append_images=frames[:-1])
    print("wrote", rel, sizes)


def main():
    # ---- desktop icon sources (cargo-bundle, Linux, Flutter fallbacks)
    save_png(render("icon.svg", 1024), "res/icon.png")
    save_png(render("icon-macos.svg", 1024), "res/mac-icon.png")
    save_png(app_icon(128), "res/128x128.png")
    save_png(app_icon(256), "res/128x128@2x.png")
    save_png(app_icon(32), "res/32x32.png")
    save_png(app_icon(64), "res/64x64.png")
    (ROOT / "res/scalable.svg").write_text((BRAND / "icon.svg").read_text())
    if (ROOT / "res/icon.svg").exists():
        (ROOT / "res/icon.svg").write_text((BRAND / "icon.svg").read_text())

    # ---- Windows: exe/installer icon and tray (tray is 16-32 px, so the bold master)
    ico_sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    save_ico("res/icon.ico", ico_sizes)
    save_ico("flutter/windows/runner/resources/app_icon.ico", ico_sizes)
    save_ico("res/tray-icon.ico", [16, 20, 24, 32, 40, 48], pick=lambda s: render("icon-small.svg", s))

    # ---- macOS: .icns (Pillow writes every size an icns needs from the 1024 source)
    render("icon-macos.svg", 1024).save(ROOT / "flutter/macos/Runner/AppIcon.icns")
    print("wrote flutter/macos/Runner/AppIcon.icns")
    # Menu-bar template: only the alpha matters (macOS tints it). Upstream's two files
    # are the @2x sizes for the dark and light menu bar.
    save_png(render("mark-mono-black.svg", 60), "res/mac-tray-dark-x2.png")
    save_png(render("mark-mono-black.svg", 48), "res/mac-tray-light-x2.png")

    # ---- Flutter in-app assets
    # icon.png is shown at 16 px (tab bar) and 30 px (connection manager): bold master.
    save_png(render("icon-small.svg", 256), "flutter/assets/icon.png")
    (ROOT / "flutter/assets/icon.svg").write_text((BRAND / "icon-small.svg").read_text())
    # header lockups (the app shows them at most 300 x 60)
    save_png(render("logo-light.svg", 720), "flutter/assets/logo_light.png")
    save_png(render("logo-dark.svg", 720), "flutter/assets/logo_dark.png")
    # the full logo tile for the About box
    save_png(render("logo-tile.svg", 320), "flutter/assets/logo_full.png")

    # ---- Windows MSI installer artwork (WiX UI). CI copies these into
    # res/msi/Package/Resources before preprocess.py, which wires them in.
    #   banner 493x58: top strip of the inner dialogs; WiX writes the title on the
    #     left, so the lockup sits at the right.
    #   dialog 493x312: Welcome/Finish page; the left 164 px is artwork, the rest
    #     must stay white for WiX's text.
    msi = BRAND / "msi"
    msi.mkdir(exist_ok=True)
    banner = Image.new("RGBA", (493, 58), (255, 255, 255, 255))
    lock = render("logo-light.svg", 168)            # 168 x 42
    banner.alpha_composite(lock, (493 - 168 - 10, 8))
    banner.convert("RGB").save(msi / "WixUIBannerBmp.bmp")
    dialog = Image.new("RGBA", (493, 312), (255, 255, 255, 255))
    dialog.alpha_composite(render("android-background.svg", 164, 312).resize((164, 312)), (0, 0))
    tile = render("logo-tile.svg", 136)
    dialog.alpha_composite(tile, (14, 88))
    dialog.convert("RGB").save(msi / "WixUIDialogBmp.bmp")
    print("wrote tfa/brand/msi/WixUIBannerBmp.bmp + WixUIDialogBmp.bmp")

    # ---- Android
    dens = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
    for d, k in dens.items():
        base = f"flutter/android/app/src/main/res/mipmap-{d}"
        s = int(48 * k)
        # legacy launchers (pre-Android 8): the rounded tile, and a round version
        save_png(render("icon.svg", s), f"{base}/ic_launcher.png")
        big = render("android-background.svg", 1024)
        big.alpha_composite(render("android-foreground.svg", 1024))
        mask = Image.new("L", (1024, 1024), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 1023, 1023), fill=255)
        rnd = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        rnd.paste(big, (0, 0), mask)
        save_png(rnd.resize((s, s), Image.LANCZOS), f"{base}/ic_launcher_round.png")
        # adaptive layers: 108 dp canvases
        fg = int(108 * k)
        save_png(render("android-foreground.svg", fg), f"{base}/ic_launcher_foreground.png")
        save_png(render("android-background.svg", fg), f"{base}/ic_launcher_background.png")
        save_png(render("android-monochrome.svg", fg), f"{base}/ic_launcher_monochrome.png")
        # notification icon: white silhouette on transparent, as Android requires
        st = int(24 * k)
        save_png(render("mark-mono-white.svg", st), f"{base}/ic_stat_logo.png")
    save_png(render("icon.svg", 512), "fastlane/metadata/android/en-US/images/icon.png")


if __name__ == "__main__":
    main()
