# Your own Datafordeler API key

[Dansk](DATAFORDELER.md)

1. Open [Datafordeler Administration](https://portal.datafordeler.dk/) and sign in to your own account.
2. Create an IT system, for example “LTM local”. Open **API-Keys**, choose **Opret**, and create an API key for public data. LTM uses DAR and needs no access to personal registers.
3. Copy the key, which Datafordeler displays only once. Save it in your own password manager if needed.
4. In your local LTM, open **Kortdata → Datafordeleren · egen API-nøgle**, paste the key into the password field, and choose **Kontrollér og gem nøgle**. LTM checks the DAR v3 schema and connectivity before saving. A failed replacement preserves the previous key.

From beta.8, a saved key routes new road, postcode and boundary downloads through **DAR GraphQL**. Complete pages and local joins retain stable address IDs, floors and doors. Without a key, the existing source is used; DAR REST is scheduled to retire on 15 January 2027. Search suggestions still use the separate official Adressevælger service.

Development tests use fictional responses. First try one public road in your own installation and check house numbers and apartment units before downloading a larger area. Testing your real account and HA installation remains a separate owner step.

**Can I create a key after 15 January 2027? Yes.** The date closes the old REST access; it is not a deadline for creating API keys. API-key/OAuth access and GraphQL continue afterwards, and new users register in Datafordeler Administration. Connect the new access before the closure to avoid an interruption to new address downloads. An expired or lost key can be replaced in Administration and saved in LTM. See the [official transition description](https://datafordeler.dk/vejledning/transitionsnetvaerk/).

## Current status

DAR GraphQL import is implemented and uses your own API key. From beta.23, the setup plan links directly to the local key guide. Create an account, an IT system and an API key in Datafordeler Administration, then enter the key in your local LTM. There is no shared application key.

The official REST retirement date remains **15 January 2027**. The [authority announcement](https://www.klimadatastyrelsen.dk/om-klimadatastyrelsen/nyheder/nyhedsarkiv/2026/jun/paralleldrift-paa-datafordeleren-ophoerer-den-15-januar-2027) and [DAR GraphQL access guide](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/) were checked again on 17 October 2026. Address suggestion access is separate. Existing local records remain available; testing your own key with a public road and small area on your own HA is still an owner step.

## Resuming downloads

A checkpoint retains its source, schema fingerprint and fixed registration/effect time. Completed roads or tiles are skipped after pause/restart. Incomplete results cannot be saved as complete. Source failures stop at the current part and preserve local addresses.

A REST checkpoint cannot resume using GraphQL. A GraphQL checkpoint cannot resume without its connection. Choose a **new download/update** when switching sources or after a schema change, or restore the previous connection. Existing local addresses are preserved. Existing address-change review remains in place for postcode and boundary refreshes.

## Local storage and privacy

The key stays in the installation's private data folder, separate from SQLite. It is omitted from status, geographic data and portable backups, so configure it again on another installation. Beta data reset preserves the connection. **Kontrollér gemt forbindelse** rechecks it; **Fjern gemt nøgle** removes the credential while preserving local records.

Only the fixed official Datafordeler host receives the key for authentication. Connectivity checks send no local records. Downloads send public road/postcode/entity lookups or rectangular tiles. The exact territory boundary is filtered locally. Cards, publishers and do-not-call records are never sent. Do not send your key in chat, screenshots or GitHub feedback.

For rejected access, check that this is an API key for the right IT system, rather than an OAuth shared secret. For network failures, resume later. Replace expired or deactivated keys locally. [Official API-key instructions](https://confluence.kds.dk/pages/viewpage.action?pageId=187105503).
