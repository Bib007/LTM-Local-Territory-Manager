# Contributing

[Dansk](../CONTRIBUTING.md)

**Documentation is Danish first.** Primary README/manual/setup paths contain Danish. English is an optional corresponding `.en.md` file. Keep both versions and language links current. A clean public installation repository receives only reviewed source, empty templates and fictional fixtures; it must not inherit private development history.

Small, understandable changes are welcome. Open an issue with a made-up reproduction, or a pull request explaining the changed behavior and verification.

Do not attach real databases, publisher names, do-not-call addresses, screenshots with personal information, access codes or Google credentials. Logs should contain no private payloads. Automated tests must use temporary directories and synthetic records; never open the default application data folder in a test.

Preserve the current separate SQLite files, unknown record fields, import previews, operation-specific approval checks and confirmed destructive actions. An ordinary program update must not replace existing databases. Avoid adding runtime dependencies for tasks already handled by Python's standard library and bundled assets.

Run the Python and JavaScript checks in README.md. Include meaningful verification for changes to persistence, geometry, access control or public export. For a UI-only tweak, inspect desktop and mobile behavior. Mention anything not verified on physical hardware.

Keep Danish primary documentation and optional English translations in step. Official JW terminology must be checked in public official sources before being presented as such. Do not request restricted documents or access to someone else's JW HUB account.

At the owner’s request, generic rejection of ordinary changes from other tabs or devices is paused in 1.12.1. Revisit concurrent editing with user profiles; do not restore that rejection as a routine fix.
