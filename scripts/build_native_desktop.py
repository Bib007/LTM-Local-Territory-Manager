#!/usr/bin/env python3
"""Prepare a bundled, local-only desktop LTM app; never upload or publish it.

Use on the target OS. The GitHub Actions workflow packages the resulting app
as an unsigned Windows installer or an unsigned macOS disk image.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "distrikt" / "app"
TEMPLATES = ROOT / "distrikt" / "templates"


def version():
    match = re.search(r"^VERSION='([^']+)'", (APP / "server.py").read_text(), re.M)
    if not match:
        raise RuntimeError("LTM version not found")
    return match.group(1)


def command(output):
    output = Path(output).resolve()
    for folder in (APP, TEMPLATES):
        if not folder.is_dir():
            raise FileNotFoundError(folder)
    if sys.platform not in ("darwin", "win32"):
        raise RuntimeError("Build native LTM on macOS or Windows, not on Linux.")
    # Source tree is the public repository; no private user-data folder is read.
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onedir", "--name", "LTM",
        "--distpath", str(output),
        "--workpath", str(output / "_build"),
        "--specpath", str(output / "_spec"),
        "--paths", str(APP),
        "--paths", str(APP / "vendor_py"),
        "--add-data", str(APP) + os.pathsep + "app",
        "--add-data", str(TEMPLATES) + os.pathsep + "templates",
        "--hidden-import", "pypdf",
        "--hidden-import", "qrcode",
        "--hidden-import", "s13_reader",
        "--icon", str(ROOT / "distrikt" / "icon.png"),
    ]
    if sys.platform == "darwin":
        args += ["--windowed", "--osx-bundle-identifier", "org.localterritorymanager.ltm"]
    else:
        # Keep stdin/stdout pipes available for the isolated S-13 reader.
        # PyInstaller's hide-console support avoids a distracting command window.
        args += ["--console", "--hide-console", "hide-early"]
    args.append(str(APP / "desktop_entry.py"))
    return args


def build(output):
    args = command(output)
    subprocess.run(args, cwd=ROOT, check=True)
    if sys.platform == "win32":
        from PIL import Image
        with Image.open(ROOT / "distrikt" / "icon.png") as icon:
            icon.save(Path(output).resolve() / "ltm.ico", format="ICO", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128)])
    result = Path(output).resolve() / ("LTM.app" if sys.platform == "darwin" else "LTM/LTM.exe")
    if not result.exists():
        raise RuntimeError("Missing native application: " + str(result))
    print("Native LTM " + version() + ": " + str(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist-native")
    arguments = parser.parse_args()
    build(arguments.output)
