# Known limitations

[Dansk](LIMITATIONS.md)

- Automatic boundary and card division proposals are paused from beta.61 (W81). The code is retained; use the manual map editor. See the [archive](AUTOMATISK-INDDELING.en.md).
- The stable baseline interface is Danish. English is planned, not complete.
- Automated tests use fictional data. Real Google publication, physical card/printer alignment, Windows hardware and your HA installation need local verification.
- Address imports are Danish. From beta.8, a saved personal key enables DAR GraphQL; without a key, the existing source is used. DAR REST is scheduled to retire on 15 January 2027. Testing a real Datafordeler account/HA installation and the separate Adressevælger access change remain outstanding. Saved local data remains available.
- OSM tiles require internet access and service policy compliance. No offline tile pack, unrestricted bulk download or automatic mass image export is provided.
- Original form backgrounds are bundled separately from the application's MIT code. They do not imply affiliation or endorsement. The PDF renderer has limited font support; browser printing supports more Unicode.
- HA's own backups exclude app data. Export private backups within the app.
- The ZIP upgrade test skips if the previous private release ZIP is unavailable. CI reports skipped checks explicitly.
- GitHub Pages hosts static files; it cannot run this Python/SQLite backend. The separate browser-only demo is implemented with fictional data and Danish/English UI. Its automated checks pass. The public root URL and static assets have been verified without login; live browser/mobile/print layout verification remains separate. See [demo publication](DEMO-HOSTING.en.md).
