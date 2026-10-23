#!/usr/bin/env python3
"""Regenerate HA PNGs from maintained SVGs (developer-only: CairoSVG and Pillow)."""
from pathlib import Path
import io
import cairosvg
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    brand=ROOT/'assets'/'brand';target=ROOT/'distrikt'
    cairosvg.svg2png(url=str(brand/'mark.svg'),write_to=str(target/'icon.png'),output_width=128,output_height=128)
    svg=(brand/'logo-dark.svg').read_bytes().replace(b'system-ui,-apple-system,Segoe UI,sans-serif',b'DejaVu Sans,sans-serif')
    wordmark=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg,output_width=720,output_height=132)))
    logo=Image.new('RGBA',(720,132))
    ImageDraw.Draw(logo).rounded_rectangle((0,0,719,131),radius=14,fill='#25282b')
    logo.alpha_composite(wordmark);logo.save(target/'logo.png')
