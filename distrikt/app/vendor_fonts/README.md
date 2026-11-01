# Fixed date glyphs

The raster date alphabet in date-glyphs.json is named **LTM Date Digits**, derived from Noto Sans. The glyph data is distributed under the SIL Open Font License 1.1; see NOTO-SANS-OFL.txt for copyright and terms. The application code retains its own license.

Only the twelve fixed characters used for dates are included. The original font is not shipped, and no font engine, extra Python package or external request is needed at runtime.

Source: https://github.com/google/fonts/tree/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/notosans

Original TTF SHA-256: bfb7bb691513f12e734dc346c03a03f784912432d7e3fa8e56efcf906fe86b3d

To rebuild with the pinned source TTF and a JSON object containing its commit and font_sha256, run the developer-only scripts/build_date_glyphs.cjs with those two local input paths. It uses the project's isolated Playwright tool; no browser is needed by LTM itself.
