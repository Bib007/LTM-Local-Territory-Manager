# Address downloads with your own Datafordeler key

[Dansk](DATAFORDELER.md)

Updated 24 October 2026. Downloads with an individual API key are implemented. The owner has confirmed working Home Assistant downloads; the earlier general owner test is no longer pending. A new installation still needs its own connection.

## Connect

1. Sign in to [Datafordeler Administration](https://portal.datafordeler.dk/).
2. Create an IT system and an API key for public data. LTM uses DAR, not personal registers. An OAuth Shared Secret is a different credential and cannot replace the API key.
3. Keep the key private, for example in a password manager. Never send it in chat, feedback or GitHub.
4. Open **Settings → Connections → Datafordeleren · egen API-nøgle**. **Download addresses** also has a shortcut to the connection settings. Paste the key and choose **Kontrollér og gem nøgle**.
5. LTM checks access and its expected DAR schema. The input is cleared after submission; a rejected replacement preserves the previous key.

A green connection confirms the connection, not a number of downloaded addresses.

## Download and follow progress

Start with one road or a small area on a new installation. With a saved key, LTM uses DAR GraphQL independently of Adressevælger road suggestions. If suggestions fail, enter the exact official road name and postcode. OpenStreetMap background, buildings and road geometry are a separate source.

For the overall boundary, use **Samlet distriktsgrænse → Hent/fortsæt**. From beta.65, status shows the current stage and unique addresses received. These may differ from the final count inside the exact boundary. The final result states the count and whether the download is complete. There is no estimated remaining time.

Large requests can be split into smaller tiles within fixed limits. Completed parts survive a pause or connection failure. Resume with the same source and snapshot. An incomplete result remains incomplete; an empty result does not by itself mean existing addresses should be removed.

## Resume or refresh

A checkpoint retains its source, snapshot and schema fingerprint. Completed parts are skipped on resume. Source changes or a changed schema require a new download/update or restoration of the original connection; existing local addresses are preserved when resume is refused.

Review new, changed and retired addresses under **Follow-ups → Address changes**. Approved register changes still need incorporating into the relevant cards. Cards are not changed automatically, and approval of a printed physical card side is a separate action.

## Problems

- Rejected access: check the correct API key and IT system. For a new key, wait and retry the connection check deliberately. Share only the app's sanitized diagnostic, never a key or raw response.
- Network errors: completed parts remain saved. Resume when the connection works. A network error does not automatically mean the key is wrong.
- Request limits: bounded subdivision is attempted. If the final result is still incomplete, the download is not finished.
- Use **Kontrollér gemt forbindelse** to check again. Removing the saved key preserves cards and addresses.

Automated development tests use fictional provider responses. They do not verify a user's chosen real geographic area.

## Privacy and moving installations

The key is stored separately in the private data directory and is excluded from normal backups. Reconnect after moving installations. Resetting beta test data preserves the connection.

Datafordeler receives authentication and public address queries. The exact territory boundary is filtered locally; cards, publishers and do-not-call entries are not sent to the provider. Adressevælger is a separate suggestion service, normally using the recommended public token. Do not enter the Datafordeler key in the Adressevælger token field.

## January 2027 transition

The authority still states **15 January 2027** for retirement of non-modernized services, including old REST access. This is not a deadline for creating keys. Modernized API-key/OAuth and GraphQL access continues; new users register in Datafordeler Administration. The transition does not delete locally saved records.

Official sources checked 24 October 2026:

- [Authority retirement announcement](https://www.klimadatastyrelsen.dk/om-klimadatastyrelsen/nyheder/nyhedsarkiv/2026/jun/paralleldrift-paa-datafordeleren-ophoerer-den-15-januar-2027)
- [DAR GraphQL access requirements](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/)
- [Transition guidance](https://datafordeler.dk/vejledning/transitionsnetvaerk/)
