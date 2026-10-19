# Readable archive without LTM

[Dansk](LAESEARKIV.md)

Open **Settings → Data → Export readable archive**. The ZIP contains four PDFs (card fronts, do-not-call backs, digital maps and tasks), original S-13 reports for all stored service years, and UTF-8 CSV tables. It includes private names, do-not-call records and tasks; keep it private. This archive does not replace the restorable backup.

View and include each OpenStreetMap map individually. The next map loads only after **Include map and continue**. Automatic bulk tile fetching is not used. Internet is needed to display the map; images are embedded in the finished PDF for offline reading. Digital maps omit do-not-call, ignored and retired addresses, as in the existing public map renderer. Cards without geography still appear in the fronts and CSV tables. Archived records are included.

Download starts only when every map is included. Cancellation, missing background tiles, changed data or expiry requires starting again. The export expires after one hour and accepts up to 100 MB of map images. Check browser downloads afterwards. The backup reminder date is unchanged.

CSV retains precise addresses, floors and doors; older street summaries are labelled as summaries. Formula-like user text receives a leading apostrophe. CSV preserves Unicode; unsupported standard-PDF font characters use their U+code in readable PDFs. No passwords, API keys, raw configuration or connection files are included. Print approvals and Google sharing remain unchanged.

The [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) permits normal interactive viewing and prohibits bulk downloading. Each visible map is therefore included explicitly by the user.
