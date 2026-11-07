#!/usr/bin/env python3
"""Create LTM's bilingual, Retina-ready Finder installer presentation.

Only public assets are read; no local user database or credentials are used.
The finished Finder window is laid out by the free create-dmg tool.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse
import html

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://localterritorymanager.netlify.app/da/guide/#mac-first-open"
WIDTH, HEIGHT, SCALE = 900, 550, 2
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
    text(450, 185, "Træk appen til Programmer  /  Drag to Applications", 18, C["ink"], bold=True, anchor="mt")
    text(222, 238, "01   LTM", 15, C["muted"], bold=True, anchor="mt")
    text(687, 238, "02   APPLICATIONS", 15, C["muted"], bold=True, anchor="mt")
    # A gentle, generous directional arrow, kept clear of both icons.
    y=318
    d.line([(330*SCALE,y*SCALE),(547*SCALE,y*SCALE)], fill="#78a991", width=7*SCALE)
    d.polygon([(545*SCALE,(y-15)*SCALE),(567*SCALE,y*SCALE),(545*SCALE,(y+15)*SCALE)],fill=C["green"])
    text(449, 284, "TRÆK HERTIL  /  DRAG HERE", 12, C["green"], bold=True, anchor="mm")

    # The clickable Finder web location is overlaid at x450 y490.
    rect((27, 421, 873, 543), C["cream"], 17)
    text(58, 437, "FØRSTE ÅBNING  /  FIRST LAUNCH", 14, C["ink"], bold=True)
    text(58, 463, "Mac beder muligvis om en sikkerhedsgodkendelse.", 13, C["muted"])
    text(58, 485, "Need help approving LTM? Open the guide on the right.", 12, C["muted"])
    text(765, 438, "GUIDE  /  HJÆLP", 12, C["green"], bold=True, anchor="mt")
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
    help_link = create_webloc(folder / "Første åbning - Guide.webloc")
    return bg, help_link


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, default=ROOT / "dist-native" / "_dmg")
    args = parser.parse_args()
    background, guide = prepare(args.folder)
    print("Finder installer background:", background)
    print("Guide shortcut:", guide)
