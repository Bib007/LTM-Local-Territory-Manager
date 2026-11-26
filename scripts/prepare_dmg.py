#!/usr/bin/env python3
"""Create LTM's bilingual Finder installer presentation at 1:1 dimensions.

Only public assets are read; no local user database or credentials are used.
The finished Finder window is laid out by the free create-dmg tool.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse
import html

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://localterritorymanager.netlify.app/da/guide/#mac-first-open"
# Finder uses the image's raw pixel dimensions, not logical Retina points.
# A 1800×1100 PNG inside a 900×550 window is cropped, not downscaled.
WIDTH, HEIGHT, SCALE = 900, 550, 1
C = {
    "ink": "#193e32", "dark": "#133c30", "green": "#2d7459",
    "mint": "#dce9d8", "pale": "#f5f8f2", "line": "#d9e5d9",
    "cream": "#eff4e9", "white": "#ffffff", "muted": "#60786b",
}


def font(size, bold=False):
    faces = (
        ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf"]
        if bold else
        ["/System/Library/Fonts/Supplemental/Arial.ttf",
         "/System/Library/Fonts/Supplemental/Helvetica.ttf"]
    )
    for face in faces:
        if Path(face).exists():
            return ImageFont.truetype(face, size * SCALE)
    return ImageFont.load_default()


def create_background(path):
    canvas = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), C["pale"])
    d = ImageDraw.Draw(canvas)
    def rect(box, color, radius=0, outline=None, width=1):
        bounds = tuple(int(i * SCALE) for i in box)
        d.rounded_rectangle(bounds, radius=radius * SCALE, fill=color, outline=outline, width=width * SCALE)
    def text(x, y, value, size, color, bold=False, anchor=None):
        d.text((x * SCALE, y * SCALE), value, font=font(size, bold),
               fill=color, anchor=anchor)
    # Brand header, matching the public LTM website's restrained greens.
    rect((0, 0, WIDTH, 142), C["dark"])
    rect((35, 27, 112, 108), "#f1f6e9", 20)
    with Image.open(ROOT / "distrikt" / "icon.png") as icon:
        icon = icon.convert("RGBA")
        icon.thumbnail((65*SCALE, 65*SCALE), Image.Resampling.LANCZOS)
        canvas.paste(icon, (int(41*SCALE), int(34*SCALE)), icon)
    text(136, 24, "LTM", 51, C["white"], bold=True)
    text(138, 92, "LOCAL TERRITORY MANAGER", 16, "#d8e9d7", bold=True)
    text(855, 66, "INSTALLATION  /  SETUP", 13, "#d0e4d3", anchor="ra")

    # Installation stage. Finder draws the actual draggable app and
    # Applications link icons at the marked coordinates.
    rect((27, 162, 873, 407), C["white"], 20, C["line"], 1)
    text(450, 185, "Træk LTM til Programmer  /  Drag LTM to Applications", 18, C["ink"], bold=True, anchor="mt")
    text(218, 228, "01  APP", 14, C["muted"], bold=True, anchor="mt")
    text(685, 228, "02  PROGRAMMER / APPLICATIONS", 13, C["muted"], bold=True, anchor="mt")
    # A gentle, generous directional arrow, kept clear of both icons.
    y=318
    d.line([(330*SCALE,y*SCALE),(547*SCALE,y*SCALE)], fill="#78a991", width=7*SCALE)
    d.polygon([(545*SCALE,(y-15)*SCALE),(567*SCALE,y*SCALE),(545*SCALE,(y+15)*SCALE)],fill=C["green"])
    text(449, 283, "TRÆK FOR AT INSTALLERE  /  DRAG TO INSTALL", 11, C["green"], bold=True, anchor="mm")

    # Finder will place a real clickable guide icon at x765, y465.
    # Leave room below it for Finder's file name, within the 550px canvas.
    rect((27, 421, 873, 543), C["cream"], 17)
    text(58, 437, "FØRSTE ÅBNING  /  FIRST LAUNCH", 14, C["ink"], bold=True)
    text(58, 463, "Mac beder muligvis om en sikkerhedsgodkendelse.", 13, C["muted"])
    text(58, 485, "Need help opening LTM? Use the guide icon to the right.", 12, C["muted"])
    # Do not draw text behind Finder's real link icon or its caption.
    canvas.save(path, "PNG", optimize=True)
    return path


def create_webloc(path):
    # A Finder internet location: clickable, with no executable shell script.
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict><key>URL</key>'
        '<string>' + html.escape(SITE, quote=False) + '</string>'
        '</dict></plist>\n', encoding="utf-8"
    )
    return path


def prepare(folder):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    bg = create_background(folder.parent / "LTM-DMG-background.png")
    help_link = create_webloc(folder / "Hjælp - Help.webloc")
    return bg, help_link


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, default=ROOT / "dist-native" / "_dmg")
    args = parser.parse_args()
    background, guide = prepare(args.folder)
    print("Finder installer background:", background)
    print("Guide shortcut:", guide)
