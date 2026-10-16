# Known limitations

[Dansk](LIMITATIONS.md)

- The stable baseline interface is Danish. English is planned, not complete.
- Automated tests use fictional data. Real Google publication, physical card/printer alignment, Windows hardware and your HA installation need local verification.
- Automatically proposed territories are geographical suggestions, not walking routes or cadastral boundaries. Review access, roads, disconnected features and card membership before creation.
- Address imports are Danish. The existing DAR REST source is documented as scheduled for retirement on 15 January 2027. Its replacement requires a separate implementation; saved local data remains available.
- OSM tiles require internet access and service policy compliance. No offline tile pack, unrestricted bulk download or automatic mass image export is provided.
- Original form backgrounds are bundled separately from the application's MIT code. They do not imply affiliation or endorsement. The PDF renderer has limited font support; browser printing supports more Unicode.
- HA's own backups exclude app data. Export private backups within the app.
- The ZIP upgrade test skips if the previous private release ZIP is unavailable. CI reports skipped checks explicitly.
- GitHub Pages hosts static files; it cannot run this Python/SQLite backend. The separate browser-only demo is implemented with fictional data and Danish/English UI. Its automated checks pass. The public root URL and static assets have been verified without login; live browser/mobile/print layout verification remains separate. See [demo publication](DEMO-HOSTING.en.md).
