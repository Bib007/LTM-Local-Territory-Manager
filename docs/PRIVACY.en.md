# Privacy and data flows

[Dansk](PRIVACY.md)

The machine running the Python app stores the private SQLite files. A desktop browser talks to loopback; the HA version uses its configured private host, app login and LAN/VPN. No developer cloud, telemetry or AI endpoint receives app records.

| Action | What leaves the machine | Destination |
| --- | --- | --- |
| Ordinary card, publisher, IB and loan editing | Nothing to the developer | Local server only |
| View OpenStreetMap | Tile coordinates and normal web connection details, revealing the viewed area | OpenStreetMap tile service |
| Online road suggestions | Public road/postcode fragments | Address service |
| Fetch addresses/buildings | Public road/postcode or geographical bounding rectangle | Official Danish address services / OSM service |
| Optional Google connection | OAuth authorization and Google API requests | Google |
| Approved public map | Reviewed PNG with card number/name, boundary and allowed visit points | Chosen Google Drive account |
| Private backup export | File downloaded to your browser/device | Wherever you subsequently choose to store it |

Shared card PDFs show all saved address points with identical red dots and house numbers. The do-not-call list is on the back of the physical card. The image omits do-not-call status, notes, publisher names, assignment history and database files.

An IB change requires a fresh browser-generated image and approval. The server can upload an approved image but does not independently generate a new OSM screenshot. Removal of obsolete public access depends on reaching Google; inspect the sharing status and resolve failures.

The browser demo uses fictional data and browser-local changes only. It has no private data import, Google publishing or connection to a real installation. The demo's static host still receives ordinary website requests; local demo state is not a shared hosted database.

Local-first design can reduce disclosure and give the operator control. It does not establish legal compliance. Follow applicable privacy law, congregation instructions and sensible access/retention practices; this document is a description of software behavior, not legal advice.

Private backups can outlive the app's 48-hour recovery window. Manage old backup copies yourself. Never post real records in GitHub issues or send them to AI for debugging.
