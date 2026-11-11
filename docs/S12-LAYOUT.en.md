# S-12 layout adjustment (development feature)

[Dansk](S12-LAYOUT.md)

**Not released to Stable.** The existing local congregation print profile stores independent positions for Danish and English S-12 templates.

Open **Print front → Measurements and placement → S-12 · adjust text and QR**. Move territory name, card number, and street list by at most ±2 mm on either axis, scaling text only to 95–105%. The QR may move ±2 mm but retains its physical size for scan reliability. Reset S-12 fields restores original positions. Existing whole-card print offsets remain unchanged.

The A4 preview represents 210 × 297 mm paper and centers the card within an area with a nominal 10 mm margin. Print at **100%**, with browser headers/footers and fit-to-page disabled. Printing is blocked on detected clipping, overlapping variable fields, or missing QR. The original raster artwork's mandatory text must also be reviewed visually.

Legacy print profiles without `s12_layout` render as before. No new SQLite files or schema migrations are needed. Configuration remains part of existing private settings backups.

## Development dependencies

The `print.profile.save` contract validates `s12_layout.da|en`; modified files include `store.py`, `printing.js`, `s12-layout.js`, `server.py` and frontend tests. `store.py` is a shared merge hotspot. Synthetic automated tests cover limits and persistence; physical QR scans and Mac/Windows printer drivers remain acceptance gates.
