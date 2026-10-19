# Your own Datafordeler API key

[Dansk](DATAFORDELER.md)

1. Open [Datafordeler Administration](https://portal.datafordeler.dk/) and sign in to your own account.
2. Create an IT system, for example “LTM local”. Open **API-Keys**, choose **Opret**, and create an API key for public data. LTM uses DAR and needs no access to personal registers.
3. Copy the key, which Datafordeler displays only once. Save it in your own password manager if needed.
4. In your local LTM, open **Kortdata → Datafordeleren · egen API-nøgle**, paste the key into the password field, and choose **Kontrollér og gem nøgle**. LTM checks the DAR v3 schema and connectivity before saving. A failed replacement preserves the previous key.

From beta.8, a saved key routes new road, postcode and boundary downloads through **DAR GraphQL**. Complete pages and local joins retain stable address IDs, floors and doors. Without a key, the existing source is used; DAR REST is scheduled to retire on 15 January 2027. Search suggestions still use the separate official Adressevælger service.

Development tests use fictional responses. First try one public road in your own installation and check house numbers and apartment units before downloading a larger area. Testing your real account and HA installation remains a separate owner step.

From beta.39, rejected queries show a sanitized GQL category for schema/filters, data access, size limits or another rejection. Only known codes and field names are shown. Recognized size errors trigger bounded smaller lookups; other failures stop. Try one road first and report only the app's GQL diagnostic if it fails. The beta.38 owner test failed for both a road and the boundary, so working live downloads remain unconfirmed.

Beta.38 corrects a point-lifecycle error that could return zero addresses with a valid saved key. Points use a different lifecycle from addresses/houses, and service responses may omit point status. Older GraphQL boundary checkpoints are fetched again automatically; you can also choose **Opdater hele området**. An empty result gives a clear warning and cannot retire all existing local addresses. A real road and area still need testing with your own key.

From beta.30, downloads with your own key no longer require the legacy suggestion service. If suggestions fail, enter the exact official road name and postcode and choose **Hent vej**. Suggestions remain optional help. A small map-area download still gets buildings/road names from OSM, then uses GraphQL for their addresses.

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

A newly created API key can take up to **15 minutes** to become active. This is only one possible reason for rejected access, not an explanation for every failure. After 15 minutes, explicitly retry **Kontrollér gemt forbindelse**. Network/server errors remain separate. [Official Administration guide](https://datafordeler.dk/media/lggned4a/20260219-datafordeler-administration.pdf).

## Read-only diagnostics in beta.40

Choose **Check DAR lookups** under the Datafordeler connection. It compares the actual projections and filters using fictional search values in plain and aliased queries. The check saves no addresses, changes no connection or checkpoints, and shows no raw provider messages. It takes up to one minute. An accepted fictional lookup does not confirm a real address download; W62 remains open.

## Address downloads from beta.41

The beta.40 check accepted plain requests and rejected aliases and multiple root fields. From beta.41, address downloads therefore use separate plain requests. The read-only check retains its alias/batch probes for diagnostics; rejection of those probes is expected and does not mean downloads still use aliases. After updating, try one road and then Fetch/continue for the combined territory boundary. Share only counts or sanitized errors, never the key. Large downloads may take longer; interrupted or incomplete requests are not stored as complete.

## Adressevælger and Datafordeler are separate connections

Adressevælger supplies online road suggestions as you type. Suggestions still use Adressevælger when Datafordeler is connected. Without a saved Datafordeler key, LTM also uses Adressevælger for address downloads; with a key, addresses are fetched through Datafordeler's DAR GraphQL service.

You normally do not need to enter an Adressevælger token. LTM automatically uses the default token recommended by KDS. Enter your separate Datafordeler API key under **Datafordeler · your API key**, never in the Adressevælger field.

Under **Map data → Road suggestions · Adressevælger**, the status shows whether the default or a custom token is used. The saved value is not displayed. **Advanced · change Adressevælger token** lets you replace it. Leave the field blank and choose **Save token choice** to restore the default; your Datafordeler key is kept.

Turn off online road suggestions beside the road field to use suggestions from locally saved roads only. Online suggestions send the search text and optional postcode to Adressevælger. Card selections, do-not-call records and publisher names are not part of the suggestion request. **Fetch road** remains a separate online action.

[The official KDS guide to Adressevælger tokens and planned user access management](https://confluence.kds.dk/display/ADV/Brugerstyring) was checked on 19 October 2026. Access arrangements may change; changing an Adressevælger token does not replace creating a Datafordeler key.
