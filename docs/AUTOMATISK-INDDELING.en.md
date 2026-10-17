# Territory division proposals

[Dansk](AUTOMATISK-INDDELING.md)

On develop from 1.12.0-beta.11, proposals can follow a locally saved road path with bends and curves. Same-name road records are joined only at exactly matching endpoints without a branch. Cards are created only after you review and confirm the complete proposal.

## Prepare a small trial area

1. Open **Indstillinger → Avanceret → Opsæt distrikter** (Settings → Advanced → Set up territories). Check the overall boundary and download addresses for the area.
2. Also check that local road geometry has been downloaded. An OpenStreetMap background image alone is not road geometry for the calculation. Under **Kortdata → Hent bygninger i det viste kortudsnit** (Map data → Download buildings in the visible map area), a small visible area can download both roads and buildings. Use a small area at a time.
3. Choose areas, numbering and an approximate visit target. Each apartment still counts as one visit, and units in the same house stay together.
4. Select **Lav forslag til distriktskort** (Create territory proposals). Check the proposed boundaries on the map and read each card's review notes.

The calculation uses saved addresses and road geometry. It makes no new network requests and sends no cards, publishers or DNC data to a service.

## Review before creating cards

- Accepted road paths retain their actual bends. Gaps between road records are not filled with invented connections.
- A path must pass through the area and cross its boundary twice. Loops, ambiguous crossings and complex re-entry are not selected automatically. When no suitable path exists, the previous straight splitting method may be used; geometric divisions without suitable road boundaries are marked for manual review.
- Use **Ret grænser på kortet** (Edit boundaries on the map) to move vertices. Shared vertices move together; then select **Kontrollér ændrede grænser og besøg** (Check edited boundaries and visits). Also review access, disconnected areas and visit counts.
- Edit names and numbers as needed. Type **OPRET KORT** only after reviewing the whole proposal. Cancelling creates no cards; existing cards and their history are not overwritten.

Changed addresses or road data invalidate an old preview. Generate a new proposal after such changes.

Natural boundaries such as waterways and railways are not yet a separate source for division. Advanced road networks and complex intersections still require manual editing. W16 therefore remains open. The [Danish beta guide](BETA.md) describes the separate beta channel and checks on your own HA installation.
