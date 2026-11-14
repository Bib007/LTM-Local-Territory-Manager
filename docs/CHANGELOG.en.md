# Changelog (English and original historical notes)

This preserves the complete changelog as it stood before the Danish-default migration. Older historical entries were originally written in Danish and have been preserved verbatim. New releases must be documented in both this file and the Danish changelog. The Home Assistant add-on reads the Danish `CHANGELOG.md`.

## 1.12.19-beta.12 · 2026-11-14

- **DAR street suggestions:** Identify the exact card, street name, confirmed postcode and original street-list number range when a DAR road lookup fails. Retain the source error and explain that the range is not evidence DAR rejected any particular house number.
- Keep the failure message visible for retry and report the street, postcode and range when an interval has no active DAR addresses or is invalid.
- Add fictional-data regression coverage for Danish/English, safe HTML rendering, mobile/desktop and no unintended card saves. Stable is unchanged.

## 1.12.19-beta.11 · 2026-11-14

- **Tasks and replies:** Replace the ambiguous round icon with a visible checkmark button labeled “Mark done or reply”, on desktop, tablet and mobile.
- Show a distinct “Reopen” button for completed tasks and “Not due yet” for future recurring tasks. Clicking the new button continues to open the existing optional reply/confirmation dialog; the task is not completed until the user confirms.
- Preserve task history, permissions, recurrence and card data. Extend browser tests for the Danish mobile button, English states and reply flow.

## 1.12.19-beta.10 · 2026-11-14

- **DAR street-list suggestions:** Revert beta.9's local-reuse optimization following feedback that it brought no noticeable speed improvement. Restore the original workflow that downloads every confirmed street from DAR before proposing address selection.
- Remove the refresh checkbox, local reuse count and related cache logic. Keep preview, conflict checks and explicit approval before saving the card. Other beta features and Stable remain unchanged.

## 1.12.19-beta.9 · 2026-11-14

- **DAR street-list suggestions:** Reuse complete streets previously downloaded locally without another source request. Fetch only missing streets automatically; a partial address import does not qualify as a complete street.
- Offer an explicit option to refresh all streets from DAR. Report how many streets were reused versus downloaded, while retaining postcode validation, active address-range selection and the review-before-save workflow.
- Expand fictional-data tests to cover partial and mixed downloads and responsive browser flows. This beta does not change Stable.

## 1.12.19-beta.8 · 2026-11-14

- **Tasks:** Add an optional reply when completing a task. The person who assigned the task can find it under Replies to me. Delete the reply from the completion history when needed.

## 1.12.19-beta.7 · 2026-11-14

- **Tasks:** Attach up to five PNG or JPEG images. View them in the task list and on the linked card. Images are stored locally and included in regular backups.
- **Do-not-call:** Review the whole card's Danish Address Register (DAR) suggestions in one table. Unambiguous changes are selected by default, and each address can be deselected.
- **Streets on the card front:** Show odd and even ranges and their total visits on one line per street. Streets with only one side keep the odd or even label.

## 1.12.19-beta.6 · 2026-11-12

- **DAR on the card front:** Add optional free text for the street name and house numbers. The card front keeps the DAR line and appends your text. Previously saved text is retained as a supplement.

## 1.12.19-beta.5 · 2026-11-12

- **Publishers:** Show accurate totals and filtered counts, group by service group and require confirmation for safe deletion while preserving permissions and assignment history.
- **Completions and history:** Improve history overview and safely edit known dates without overwriting original records.
- **KTM visits:** Clearly instruct users to choose Tuesday in the KTM week without removing historical notes elsewhere.
- **Mobile and basemaps:** Preview S-13 directly on phones/tablets and retry OpenStreetMap or generate reports without a basemap on error or timeout.
- **Bulk folder actions:** Place multiple explicitly selected territory cards into the folder with conflict checks, authorization, confirmation and consistent status.
- **Territory identifiers:** Separate public and internal territory numbers while preserving stable technical card IDs and linked data through validated renumbering.
- **Report printing:** Explicitly select calendar year, service year, rolling 12 months or all three, preserving the monthly timeline and last KTM visit highlight.
- **Follow-ups:** Reversibly dismiss individual follow-ups with an audit history, reactivation and access control without hiding critical errors.
- **Google Drive:** Show real card-generation and upload stages, prevent duplicate work and allow safe retries with renewed preview approval.
- **DAR front labels:** Override road and house-number display labels without modifying authoritative DAR addresses, maintaining consistent print and export layouts.
- **S-12 layout:** Make small bounded template-specific text and QR position adjustments with reset, preserving QR readability and A4/IB continuation pages.
- **Split suggestions:** Configure a local maximum number of visits per card and dismiss or restore individual proposals without automatic redistribution.
- Run synthetic security, access control, PDF, printing, responsive, desktop and backup regression tests. This is **Beta**; Stable is unchanged.

## 1.12.19-beta.4 · 2026-11-09

- Show the authenticated user's own currently actionable tasks next to the personal home welcome, with a shortcut opening the Open / Mine task filters.
- Keep the count private, permission-gated and automatically refreshed via the existing profile heartbeat, including changes made by other logged-in users.
- Preserve the original task listing and its historical notes, followups, due-date behavior and navigation counts; fix the JavaScript contract failure introduced by the new personal filter.
- Test fictional administrator/editor profiles, read permissions, zero/one counts, task completion, role reassignment and phone/desktop navigation. Stable 1.12.19 remains unchanged.

## 1.12.19-beta.3 · 2026-11-09

- Fix profile-mode settings silently reverting publisher card guidance to the default role counts after saving. Persisted values now pass through the authenticated settings snapshot and refresh correctly.
- Share the configured advisory counts with users allowed to view publishers, without granting permission to edit settings or exposing unrelated administration data.
- Add real authenticated HTTP save/refresh and responsive browser save/reload regression tests with fictional accounts; recommendations never block issuing extra cards.

## 1.12.19-beta.2 · 2026-11-09

- Fill the original 94 × 146 mm IB-card back more efficiently, retaining every entry and creating extra card pages only when necessary. A4 remains proof paper, never an enlarged card.
- Replace daily-use card-number creation with a search and explicit confirmation for placing an existing card in the carry folder. Preserve issue status, card identity and history; keep creation in Territory cards.
- Move “Longest since completion” from Daily use to an independently resettable sort in Territory cards. Unknown dates sort first; area, status and text filters remain selected.
- Show current / suggested active card counts for publishers based on locally adjustable publisher, pioneer, service-group assistant and overseer guidance. Combined roles use the highest suggestion; exceeding it never blocks an assignment.
- Test fictional IB lists, A4/cut PDFs, card searches and folder moves, territory ordering and combined filters, publisher assignments/settings and desktop/mobile layouts. Stable 1.12.19 remains unchanged.

## 1.12.19-beta.1

- Synchronize Beta with the verified Stable 1.12.19 feature set. Keep independent program/data directories, HA port 8788, logins and native installer identities. Future trials use Beta first.

## 1.12.19

- Local Chrome connection backups work with browser-side authenticated encryption, including private HTTP access; existing encrypted files remain compatible.
- Readable-archive fronts use the same measured print renderer as ordinary cards, including lettered house numbers and archived cards.
- Choose whether Drive maps show house numbers and leader lines; all red visit dots remain and changed images require fresh approval.
- Activity and 48-hour recovery identify the authenticated user and show a clearer timeline. Historical names are never invented.
- Backup uses Save as where supported and explains the browser download setting otherwise. Remove the old Tally menu link.
- Native Mac Intel/Apple Silicon DMG and Windows Setup installers preserve the existing data directory. Owner confirmed first-install/update tests on both systems on 8 November 2026.
- Home Assistant declares its independent Supervisor TCP watchdog. Mac-server remains pending its separate physical LAN/VPN test.
- Stable is the verified baseline. Beta is refreshed from the same feature set, with separate data/login; future trials use Beta before Stable.

## 1.12.18 · 2026-11-07

- Prevent the Home Assistant status worker and a saved overview from deadlocking while a print approval is being saved.
- Read print-validation data once per overview or batch instead of repeatedly loading all stored map images for every card.
- Disable single and batch approval buttons while saving and ignore rapid repeat clicks.
- Validate assignment deletion against the selected card's history, so unrelated background saves do not force repeated history reloads. Actual history changes still block stale deletion.
- Hide completed zero-result address checks from the dashboard and remove empty review actions; keep the schedule visible in settings.
- Publish crowded maps with all red dots even when some house numbers cannot be placed clearly.
- Cover 380 cards / 760 sides, concurrent HTTP approvals and page reads, unchanged print tokens, the status-worker lock conflict and repeat-click browser flows.

## 1.12.17 · 2026-11-07

- Render the Google Drive PDF front from the normal print template, browser layout and street grouping in Danish and English, replacing the separate approximation.
- Approve multiple printed fronts and backs together, with explicit review and confirmation. Changed print content rejects the complete batch; opening a preview or printing never approves cards automatically.
- Keep the accepted red dots, house numbers and two-page PDF structure.

## 1.12.16 · 2026-11-06

- Share one two-page Google Drive PDF with the digital map first and the full printable front second. Long road rows wrap in the printable front.
- Keep house numbers tied to their rendered dots, with leader lines in crowded areas.
- Give the internal report a congregation-name cover in print and rings for coverage and card placement.

## 1.12.15 · 2026-11-06

- Show all saved addresses with identical red dots and house numbers on the public Drive/QR image. Keep the do-not-call list on the physical card back.
- Add the bilingual guide link under Help and remove duplicate shortcuts to the setup guide and user administration.
- Report mapped visit points and do-not-call records across the saved district boundary, with the existing access controls.

## 1.12.14 · 2026-11-06

- Preserve ordinary red address and IB visit markers in private district maps, combined views and local PNG exports, including dense or coincident coordinates.
- On explicitly approved public Drive/QR map images, show saved IB locations as neutral address dots with approved house numbers, without private IB status or notes. Include these in saved-point totals but not in remaining visits.
- Validate the actual dated 2200 × 1560 PNG and approval flow. Keep existing Drive/QR links unchanged until a fresh reviewed image is explicitly approved. Clarify Danish and English privacy guidance.

## 1.12.13 · 2026-11-05

- Delete a single erroneous assignment from History after reviewing the card, publisher, dates and status. Choose the physical location when removing an active assignment. Existing completions and notes are kept, and the assignment is recoverable for 48 hours unless a newer assignment conflicts.

## 1.12.12 · 2026-11-05

- Keep close visit dots individually visible in digital district maps and their PNGs, including during export after a zoom. Previously shared images can be regenerated and approved on the same Google Drive file and QR link.

## 1.12.11 · 2026-11-05

- Keep visit markers at every saved map coordinate, including the focused map view, so distinct locations do not collapse into one red dot.
- Continue very long do-not-call backs onto clearly labelled extra print pages, with a compact readable layout. Find do-not-call entries by date or address and print a combined overview without inventing an exact date from month/year or year-only wording.
- Offer a reviewed local address suggestion for a manual do-not-call line. Nothing is linked automatically; the record ID and recorded date remain intact, and the line can stay manual.
- Keep connections separate from data and account backups. A connections administrator can create a browser-encrypted Google Drive/Datafordeler/Adressevælger backup with a personal passphrase, then explicitly restore it and check the connections again.
- Prepare five independently publishable tracks from one source/version: Home Assistant, macOS app, macOS server, Windows app and Windows server. The first desktop assets remain platform-labelled Python ZIPs, not DMG or EXE installers.

## 1.12.10 · 2026-11-04

- Review the exact card, date and assignment before deleting an erroneous completion. An active assignment remains in place, the card's latest completion is recalculated, and later history no longer reintroduces the deleted date.
- Show only the selected report period on screen for calendar year, service year or the last 12 months. Each period has matching totals, chart and map; calendar-year selection appears only for its own view.

## 1.12.9 · 2026-11-04

- Assign a card directly from the storage box, move selected cards between the box and folder beside the list, and see where each is kept.
- Add the supplied original English S-12 and S-13 PDFs without modifying them. English/Danish form selection is available for card printing and remembered per print side; report originals follow the interface language.
- Use a separate English S-13 field map/background for browser and PDF output. Danish S-13 PDF output remains byte-identical to 1.12.8 for the compatibility fixture. Dates, names, exact address membership and visit counts remain intact.
- Include original English downloads in the app and website. Preserve Danish forms and separate stable/beta data.

## 1.12.8 · 2026-11-02

- Show numeric street envelopes on physical fronts: internal letter variants no longer split a range. A missing numeric base creates a break, whether absent from the source or outside the card. Keep the final boundary suffix, e.g. 3–9B, and retain separate even/odd lines.
- Compute display summaries from saved membership, including after a cold reload. Exact selected units, visits, manual street text, public-map privacy and original forms are unchanged.

## 1.12.7 · 2026-11-02

- Restore compact, exact street intervals with `&` at gaps and separate even/odd lines per road. Consecutive lettered houses also form intervals. Physical fronts combine address types without changing visits or stored address membership.
- Prevent street text from overlapping the original form footer. Dense fronts are fitted in the bounded content area; an impossible layout is visibly flagged and print remains blocked.
- Add a real-browser regression for dense fronts at desktop/mobile widths and original-size print. Original S-12/S-13 assets remain unchanged.
- Use a new version so installations that already installed 1.12.6 receive a normal Home Assistant update.

## 1.12.6 · 2026-11-02

- Fix lossy street labels: separate number parity, preserve gaps/lettered houses, split long rows and repair saved geographic labels with print review.

- Understand whole-street wording, “kun lige/ulige” qualifiers and street-side ranges such as “23-25 & 24-26” in reviewed DAR suggestions. Preserve parity restrictions and include every apartment in the selected house numbers.
- Default the IB import screen to explicit manual lines without DAR. Import fronts and backs from separate Excel/CSV files, preserve dates and print both sides without geographic addresses.
- Link an imported manual IB entry to one explicit address on the same card later. Changing the import linking policy requires a new preview; existing records are not rebound silently.
- Clarify own-file column mapping and the optional role of DAR in the English import guide.

## 1.12.5 · 2026-11-02

- Preserve a known month/year, a year alone or literal date wording when importing or manually creating a do-not-call entry. No day or month is invented; wording survives editing, card backs, private export and backup.
- Suggest DAR addresses from a card's existing street names and number ranges after confirming each postcode. Download complete roads, review all units and the suggested boundary, then explicitly save. Stale street/address data, reserved units and unclear ranges block unsafe application.
- Mark the changed front for printing and preserve existing loans, completion history and do-not-call records.
- Carry the current Drive requests into the plan with original priorities; international address sources and English original forms remain subsequent work.

## 1.12.4 · Task responsibility and manual redistribution

- Optional responsible accounts, private self labels, task filters and linked follow-up tasks.
- Manual split/transfer suggestions, exact address-unit previews and atomic movement with coupled do-not-call records.
- Explicit latest-date scheduling reference or an interim-card issue/return/finalize workflow, retained history and reprint tasks.
- Complete declared English interface-label coverage, localized task/maintenance controls and readable conflict fields; original forms and stored user content retain their language.
- Preserve the restored home dashboard, existing roles, guides, imports and separate beta data.


## 1.12.3 · Restore the familiar home dashboard

- Restore the original home dashboard for profile users with the relevant record permissions, including its rings, shortcuts, metrics, monthly comparison and follow-ups.
- Give summary-only users the familiar home layout using aggregate totals, without exposing private records or changing report permissions.
- Keep the three-period report on the Reports page.

## 1.12.2 · Profiles, dependable saving and flexible imports

- Individual profiles and administrator-controlled roles; independent home/report summary permissions and permission-filtered personal guides.
- Sheet/header/column selection for supported card and IB spreadsheet imports with explicit preview/confirmation.
- Honest save acknowledgements, editor-owned bases, preserved conflict proposals and reliable tour completion.
- Clearer reports and safe approved manual street rows on online card fronts.
- English-first README, new-browser interface and documentation, plus a fictional demo with two role views. Original printed forms remain unchanged; translation is still partial.

## 1.12.2-beta.83 · Gemning, rundtur og manuelle onlinekort

- Uændrede formularer gemmes ikke igen; samtidige kladder beholder deres eget udgangspunkt og konfliktforslag.
- En gemt ændring kaldes ikke afvist ved efterfølgende læsefejl. Reelt udløb forklares med bevarede felter.
- Rundturens sidste trin fungerer også efter opsætningsdialogen.
- Onlineforsiden kan vise sikre manuelle vejlinjer uden gættet geografi eller besøgstal. Godkendelse og samme QR bevares.
- Rapporten viser tre perioder og aktuelle gennemgangs-/udleveringstal; original S-13 er bevaret.
- Flere profil-, backup- og konflikttekster er oversat. Engelsk er fortsat delvis.
- Rettigheder ved sammensatte handlinger, databackuppens afgrænsning og håndtering af ufuldstændige forespørgsler er strammet.

## 1.12.2-beta.82 · Læsbare rettelser og datoer på onlinekort

- Gennemgå samtidige rettelser som almindelige felter med vejnavn, numre, besøg og adressetype. Kortgrænser vises grafisk.
- Se seneste registrerede gennemgang og den aktuelle udleveringsdato på onlinekortet.
- Godkend kortbilledet og datoopdateringen én gang. Datoerne kan derefter ajourføres på samme Google-fil og QR-link.
- Adresse-, grænse- og IB-ændringer kræver stadig et nyt godkendt billede. Gendannelse genoptager ikke tidligere uploads.
- Fjern offentlig adgang stopper også datoopdateringen, mens en eventuel lukning hos Google afventer bekræftelse.

## 1.12.2-beta.81 · Tjenestegrupper og gruppeimport

- Angiv tjenestegruppe, tilsynsmand eller assistent og en særskilt pionermarkering på forkynderen.
- Filtrér forkyndere efter gruppe, og se gruppen sammen med deres kort og historik.
- Importér en gruppeliste fra Excel eller CSV. Se nye navne og før/efter-oplysninger før samlet godkendelse.
- Bevar eksisterende udlån, historik og identitet. Gruppefunktioner opretter ingen brugerkonti eller rettigheder.
- Samtidige uafhængige rettelser bevares; forskellige gruppevalg gemmes til gennemgang.

## 1.12.2-beta.80 · Vejintervaller og kortregister

- Importér kortnumre, manuelle vejlinjer og intervaller som 1–19 fra Excel eller CSV.
- Brug kortene uden geografiske adresser. Vælg adresser kort for kort senere med samme kortnummer, IB og historik.
- Manglende besøgstal vises som ukendt på kort, print og i totaler. Intervaller tælles ikke automatisk.
- Udfyld et kendt besøgstal senere. Tidligere gennemgange med ukendt antal bevares uændret.

## 1.12.2-beta.79 · IB fra Excel

- Hent Excel-skabelon, og upload XLSX eller CSV direkte i den lokale app.
- Gennemgå manglende oplysninger og manuelle linjer. Adresser uden sikkert match kan skrives på et valgt kort efter din bekræftelse.
- Se og ret et manglende postnummer bagefter. Dubletter og eksisterende IB bevares; kun bagsiden markeres til genprint.
- Samtidige dato- og postnummerrettelser bevares. Forskellige rettelser til samme postnummer gemmes til gennemgang.

## 1.12.2-beta.78 · Adressekontrol og driftsbeskeder

- Adressekontrollen prøver hurtigt igen efter korte afbrydelser og bevarer færdige udsnit. Gentagne fejl, kildeventetid og ressourcepres giver en passende pause.
- Se den seneste afbrydelse, fremdriften og tidspunktet for næste forsøg. Længere arbejdsrunder kan genoptages.
- Vis LTM-driftsstatus i Home Assistant. Importér en klar beskedopskrift, vælg din telefon og tilføj egne noter. En særskilt prøve sender én besked uden overbelastning eller dataændringer.
- HA-appen får adgang til Home Assistants lokale API for at aflevere status. Afleveringen kan slås fra i appens HA-indstillinger. Se vejledningen om adgangens omfang.

## 1.12.2-beta.77 · Profilrettelser og backup i appen

- Vælg den tidligere eller senere rettelse i en tydeligere konfliktvisning. Påmindelsen opdateres straks efter gennemgang.
- Hent og gendan en separat kontobackup under Backup og vedligeholdelse. Gendannelse kræver adgangskode, forhåndsvisning og bekræftelse.
- Vælg pr. rolle, om brugeren skal se påmindelsen om databackup. Det giver ikke adgang til selve sikkerhedskopien.
- Brugere og roller har egen indstillingsfane. Datafordeler og Google Drive er samlet under Forbindelser, som kan skjules efter rolle.
- Forsiden byder den indloggede bruger velkommen. Opfølgninger forklarer tydeligere næste handling.

## 1.12.2-beta.76 · Brugere og samtidige rettelser

- Aktivér personligt login fra den eksisterende installation. Distriktsdata bevares.
- Opret brugere og egne roller, og vælg læse- og skriverettigheder i appen.
- Gem uafhængige rettelser samtidig. Ved uenighed bevares udgangspunktet og begge rettelser til gennemgang med påmindelse på forsiden.
- Se nylig aktivitet, og giv hver ny profil sin egen introduktion.
- Rolleændringer gælder også åbne sessioner. En mistet gemmekvittering kræver stadig kontrol før næste ændring.
- Separat lokal kontobackup og administratorgendannelse er beskrevet i brugervejledningen. Almindelig databackup indeholder ikke konti.
- Lokal stop/opdatering fungerer også med profiler. Udlevering til en eksisterende forkynder kræver ikke ret til at oprette nye forkyndere.

## 1.12.2-beta.75 · Privat server på valgt adresse

- Startguiden genfinder nu serveren på den private adresse, den faktisk lytter på.
- Serverens statuskontrol bruger den lokale forbindelse direkte.
- Beta.74s startguide og adskilte data er bevaret. W74 er fortsat åbent.

## 1.12.2-beta.74 · Startguide til egen computer og server

- Ny fælles startguide til Mac, Windows og Linux med valg af lokal brug eller privat server.
- Serveren får eget login og data, lytter på den valgte private adresse og åbner ingen browser.
- Udgivelsen har nu også en samlet programpakke til egen computer. Python skal fortsat installeres separat.
- W74 er delvist leveret; et separat appvindue og selvstændige installationer mangler. OCR-arbejdet er fortsat på pause.

## 1.12.2-beta.73 · Billedimport og opfølgninger

- IB-billeder i PNG, JPG og JPEG kan åbnes og læses lokalt. En fejl i appens billedregler er rettet.
- Tallet ved Opfølgninger indlæses fra start, uden at du skal åbne fanen først.
- Billedimport kræver stadig gennemgang af adresser og datoer samt din godkendelse.

## 1.12.2-beta.72 · IB-billeder og sikker afslutning

IB fra billeder omfatter nu også kontrolleret afslutning, når selve LTM lukkes under en billedlæsning. Den lokale OCR-proces stoppes og dens midlertidige filer ryddes op, før serveren lukker. Kø, kortvalg, redigerbar tekst, præcise adresser/datoer og godkendelse er som i beta.71. Ingen ekstern AI eller cloud-OCR. S-12-forsider er fortsat ikke med.

## 1.12.2-beta.71 · Lokal IB-import fra billeder

Indstillinger → Import har nu IB fra billeder. Vælg op til 20 PNG-/JPEG-billeder i kø. Hvert billede læses på det lokale LTM-system, får sit eget kortvalg og redigerbar tekst samt forslag. Hver linje skal have en adresse fra det valgte kort og en kontrolleret dato eller springes over ved dit valg. Forhåndsvisningen og IMPORTÉR IB kræves før gemning. Næste billede startes manuelt; tidligere godkendte filer bevares ved lukning eller fejl.

HA-pakken medtager lokal Tesseract med dansk og engelsk. På Mac og Windows kræves en separat lokal Tesseract-installation; appen viser, hvis den mangler. Ingen ekstern AI, cloud-OCR eller automatisk adresseoprettelse bruges. S-12-forsider, automatisk fortolkning af flere spalter og fuld W85 er fortsat åbne. Håndskrift og uklare billeder kan kræve manuel rettelse.

## 1.12.2-beta.70 · Overlappende kortgrænser

Opfølgninger advarer, når to gemte distriktskortgrænser dækker et fælles areal. Hver berørt kombination vises én gang med links til begge kort. Du kan søge på begge kortnumre og navne. Fælles kanter og hjørner udløser ingen advarsel; adresser valgt på flere kort vises fortsat som egne punkter.

Kontrollen bruger de lokalt gemte grænser og ændrer ingen kort eller adresser. Grænser skal rettes manuelt, hvis overlappet er utilsigtet. Dansk/engelsk og telefon/tablet understøttes. Foto- og IB-genkendelse er fortsat under udvikling.

## 1.12.2-beta.69 · Færdig, når ændringen er gemt

- Permanent sletning og almindelige ændringer får den opdaterede oversigt med, når gemningen bekræftes. Du skal derfor ikke vente på en ekstra hentning eller skifte menu for at se resultatet.
- Hvis forbindelsen afbrydes eller svaret ikke kan læses, bliver du stadig bedt om at kontrollere resultatet, før du prøver igen.
- Datafordelerens nøgle og forbindelseskontrol findes nu under Indstillinger → Forbindelser. Hent adresser har en genvej dertil. Din gemte nøgle bevares.
- Udseende, samlet Import og Opfølgninger samt filkøen fra de seneste betaer er med.

## 1.12.2-beta.68 · Vælg dit udseende og prøv det nye overblik

- Vælg Mørkt, Lyst eller Følg enheden nederst i menuen. Valget huskes i din browser og kan skiftes uden at miste åbne formularer.
- Demoen bruger appens fælles designfiler og viser den samme opbygning på forside, genveje og nøgletal. Den har eksempelvisninger for Opfølgninger og Kort og adresser; alle oplysninger er stadig opdigtede.
- Adressevejledningen er gennemgået på dansk og engelsk med aktuelle menuer, hentestatus, genoptagelse og gennemgang af adresseændringer. Gamle beskeder om en manglende afprøvning er fjernet.
- Filkøen fra beta.67 er med. Automatisk genkendelse af billeder er fortsat under planlægning.

## 1.12.2-beta.67 · Flere kortfiler i kø

- Vælg op til 20 Excel-/CSV-filer til kortimport. Hver fil får sin egen forhåndsvisning og godkendelse; næste fil importeres ikke automatisk.
- Se den aktuelle fil, importerede filer og filer, du har sprunget over. Allerede godkendte filer bevares ved lukning eller fejl.
- Grænsen er 2 MB pr. fil og 20 MB samlet. Filerne behandles fortsat på dit eget system.
- Dette er første trin mod lettere masseimport. Fotos og automatisk tekstgenkendelse er endnu ikke med.

## 1.12.2-beta.66 · Import og opfølgninger samlet

- Import af historik, distriktskort og IB findes nu under Indstillinger → Import. Du gennemgår og godkender stadig oplysningerne, før de gemmes.
- Den nye menu Opfølgninger samler kortkontrol, genprint, langvarige udleveringer og adresseændringer. Hvert forhold får sin egen linje og tæller; forside og bagside tæller hver for sig.
- Forsiden åbner det fælles overblik. Genprint og kortkontrol er flyttet fra Kort og adresser, så du har ét sted at følge op.
- Søgning, filtre og dansk/engelsk er med i det nye overblik. Åbning af import eller opfølgninger ændrer ingen registreringer.
- Forbedringerne fra beta.65 med tydelig adressehentning og mindre unødig dataoverførsel er med.

## 1.12.2-beta.65 · Mindre ventetid og tydelig adressehentning

Samler forbedringerne nedenfor og sikrer samtidig, at almindelig kortgemning ikke starter en ekstra hentning af kortdata.

## 1.12.2-beta.64 · Bedre overblik under adressehentning

- Adressehentning viser, hvad den arbejder med, og hvor mange adresser der er modtaget. Antallet tælles uden dubletter ved nye forsøg. Der vises ingen gættet resttid.
- Større adresseområder deles også i mindre udsnit, når ét opslag kræver for mange forespørgsler. Færdige udsnit bevares, hvis hentningen må fortsættes senere.
- Gemning viser tydeligt, når ændringen er gemt, mens oversigten opdateres. Sletning og gendannelse af oplysninger uden kortændringer henter ikke længere alle kortdata igen.
- Rettelsen fra stabil 1.12.1 er bevaret: almindelig gemning og udlevering kræver ikke unødig genindlæsning.

## 1.12.2-beta.63 · Flere små forbedringer i daglig brug

- Ugentlige opgaver tæller først fra den dag, de skal udføres. Når de markeres udført, fortsætter de til næste dato med bevaret historik.
- Digitale kort har en lysere baggrund, så røde besøgsprikker og husnumre er tydeligere. Tidligere delte billeder opdateres først, når et nyt billede godkendes.
- Tekster om lokal lagring og adressehentning passer nu også til Home Assistant, Windows og andre enheder.
- Gemte visninger vises ved den geografiske kortoversigt.
- GitHub-forsiden har fire løse filer. Engelsk introduktion, bidragsvejledning og Mac-hjælp ligger i mapper; den gamle danske dublet er fjernet.
- Rettelsen fra 1.12.1 er med: almindelig gemning og udlevering kræver ikke genindlæsning efter ændringer i baggrunden.

## 1.12.1 · Arbejd videre uden unødig genindlæsning

Fjerner den generelle afvisning af ændringer fra andre faner/enheder, indtil brugerprofiler og samtidig redigering bliver udviklet samlet. Kort kan fortsat udleveres og rettes, når Google-delingen skifter status i baggrunden. Kontrol af kort, datoer og dobbelte udleveringer er bevaret. [Læs nyheder og opdateringsråd](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/RELEASE-NOTES.md).


## 1.12.0 · Mere overblik over dine distriktskort

En samlet opstartsguide, import af eksisterende kort og udleveringer, bedre telefon-/tabletbetjening og et tydeligere overblik i det daglige. Arbejd med adresser og kort, gem opgaver, print oversigter, og vælg selv, om du vil dele kortbilleder med QR-koder.

Læs [nyhederne og opdateringsvejledningen](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/RELEASE-NOTES.md). Tag en privat sikkerhedskopi i appen før opdatering.

## 1.12.0-beta.62 · Sikkerhedskontrol før stabil

- Opdatér den lokale PDF-læser fra pypdf 6.10.0 til 6.21.2 med kendte rettelser til ressourceforbrug. Bevar separat importproces, tids-/hukommelsesgrænser og lokal behandling.
- Afvis DTD/XML-entiteter i XLSX-parseren uanset XML-kodning; almindelige UTF-16-ark fungerer fortsat.
- Udvid API-prøver for login, tokens, fremmed Origin og filstier. Tilføj afhængighedskontrol og kontrol af alvorlige statiske Python-fund før beta/stabil publicering.
- Forenkl menupunktet Idéer og feedback. Adressehentning og Drive/gendannelse er ejerbekræftet; løbende adressestatus (W82) ligger efter stabil.

## 1.12.0-beta.61 · Manuel kortinddeling og klargøring til stabil udgivelse

- W81: fjern automatiske grænse- og inddelingsforslag fra aktiv opsætning. Gamle personlige planer peger på manuel korttegning; IB-import og eksisterende data bevares.
- Afvis gamle forslags-/oprettelseskald på serveren. Bevar generator, tidligere vejledninger og isolerede prøver til senere udvikling.
- Opdatér kom-i-gang og begrænsninger, og saml udestående ejerprøver før stabil udgivelse. Overførte Google-ønsker er ryddet efter ejerens bekræftelse.

## 1.12.0-beta.60 · Adressehentning, kortdata og læsbare fejlforklaringer

W78: DAR GraphQL genprøver midlertidige netfejl og HTTP 429/500/502/503 op til to gange på samme forespørgsel og kildetidspunkt. Ventestatus vises, serverens korte Retry-After respekteres, og pause kan afbryde ventetiden. Længere/ukendt cooldown stopper sikkert. Login-/skema-/certifikatfejl genprøves ikke automatisk; tids- og størrelsesgrænser bruger stadig mindre udsnit. NET-DNS, NET-RESET, NET-CONNECTION og NET-TLS skelner sikre fejlkategorier uden nøgler, URL eller leverandørtekst. Færdige udsnit og kontrollen før adresseændringer bevares. Ejerens konkrete hentning skal stadig genprøves.

W79: Hentning af veje, bygninger, vandløb og jernbaner kræver intet postnummer. Feltet vises og kræves kun, når man vælger adresser med den ældre kilde. Med Datafordeleren hentes alle postnumre i udsnittet. Et skjult felt sendes ikke og kan ikke blokere kortdatahentningen.

W80: Gemmestatus med en forklaring kan åbnes med tryk eller tastatur. Hele teksten står i et panel, der tilpasses skærmen og kan rulles. Den tidligere afkortning af årsagen på telefon er erstattet; åbne formularer og gemningskontroller bevares.

## 1.12.0-beta.59 · Feedback uden konto eller e-mail

W23: Menupunktet Idéer og feedback åbner nu den verificerede Tally-formular i en ny fane. Menuen forklarer tjenesten og håndtering af manuelt indsendt tekst/billeder. Ingen lokale data, nøglefiler eller logs overføres automatisk. Ejeren har bekræftet prøven uden login og med billede.

## 1.12.0-beta.58 · Bedre touchbetjening på telefon og tablet

W75: På touchskærme får knapper, formularfelter, menuer og kortets zoom større trykflader. Formulartekst er mindst 16 pixels, så felter på iPhone/iPad ikke alene udløser automatisk zoom på grund af lille tekst. Dialoger tilpasses også skærmens aktuelle højde i liggende visning og holder rulning inde i dialogen.

På smalle skærme vises hvert kortforslag som en samlet lodret række med nummer, navn, område, besøg og kontrol/advarsler. Alle felter kan gennemgås uden at rulle tabellen sidelæns. Tastatur- og skærmlæseroplysninger samt oprettelsesgodkendelsen bevares. Skrivebordsvisning og print ændres ikke.

## 1.12.0-beta.57 · Komplette adresseudsnit og kortforslag uden kort HTTP-tidsgrænse

W76: Med Datafordeleren hentes adresser nu direkte fra DAR-punkter indenfor det viste udsnit. Alle postnumre i udsnittet medtages, også veje der mangler i OpenStreetMap, og grænsen på 45 OSM-vejnavne bruges ikke til denne hentning. Store udsnit opdeles i små opslag med ét fælles tidspunkt; tids-/størrelsesfejl opdeler videre, og ufuldstændighed vises tydeligt. Færdige udsnit bevares ved fejl. Baggrundens OSM-hentning er særskilt og kan fejle uden at blokere DAR-adresser. Den ældre adressekilde bevarer sine begrænsninger. Samlet distriktsgrænse er fortsat valget til større, vedvarende hentninger.

W77: Forslag til distriktskort og kontrol af rettede grænser kan nu beregnes i baggrunden på den lokale server. Browseren følger med korte statuskald, så en beregning over 30 sekunder ikke alene afbrydes som en Wi-Fi-/VPN-fejl. Kun ét forslag beregnes ad gangen, og forladte eller forældede svar erstatter ikke en nyere redigering. Netfejl og udløbet forespørgsel har hver sin forklaring. Forslag er fortsat læsning; kort oprettes først efter kontrol og OPRET KORT. Det parkerede arbejde med nye vejnetfunktioner genoptages ikke.

## 1.12.0-beta.56 · Natlig adressekontrol på Home Assistant

W73: Under Opgaver kan du nu slå automatisk adressekontrol til, vælge hver 1–30 dage og et klokkeslæt i serverens lokale tid. Kontrollen bruger den gemte samlede distriktsgrænse og din Datafordeler-forbindelse. Appen skal køre i Home Assistant.

Forsiden viser seneste gennemførte kontrol samt antal nye, ændrede og foreslået fjernede adresser. Alle fund venter på gennemgang og udtrykkelig godkendelse. Eksisterende distriktskort ændres ikke automatisk. En ufuldstændig hentning giver aldrig forslag om fjernelser.

Ved fejl gemmes fremdriften, og opgaven prøver automatisk igen efter stigende ventetid. Genstart fortsætter samme udtræk. Manuelle hentninger, grænseændring, nulstilling og gendannelse venter, mens kontrollen arbejder eller afventer genprøve. Slå opgaven fra for at stoppe efter det aktuelle opslag.

## 1.12.0-beta.55 · Lille logo på Drive-kortet

W72: Det digitale distriktskort har nu et lille LTM-logo øverst til højre med “Local Territory Manager” under. Kortets lyse baggrund, husnumre, besøgsprikker og printforside bevares. Logoet dannes lokalt uden ekstra netkald eller persondata.

Eksisterende Drive-billeder ændres først via Opdater Google Drive-upload, ny forhåndsvisning og udtrykkelig godkendelse. Samme fil og QR-link bevares.

## 1.12.0-beta.54 · Enkel topbar og tydeligere Drive-kort

W70: Menighedsnavnet er fjernet fra topbaren. Logo, betamarkering og gemmestatus bevares, og det gemte navn bruges fortsat i indstillinger, sidepanel og rapporter.

W71: Det digitale kort til Google Drive viser nu OSM-baggrunden med 50 % styrke over hvidt. Farvet fyld inden for distriktsgrænsen er fjernet fra dette billede, så det ikke mørkner baggrunden igen. Besøgsprikker er kraftigere røde, og husnumre er mørkerøde med hvid kontur; begge vises uden dæmpning. Grænse, oplysninger og printforside bevares.

Eksisterende Drive-billeder ændres først, når du vælger Opdater Google Drive-upload, kontrollerer det nye billede og godkender publicering. Status viser, når kortbilledet bruger et ældre design. Samme fil og QR-link bevares. Der sker ingen automatisk genpublicering, og private IB, noter og forkyndere indgår fortsat ikke i billedet.

## 1.12.0-beta.53 · Vandløb og jernbaner som skel

W16, delopgave: Hentning af et kortudsnit medtager nu også offentlige vandløb og jernbaner fra OpenStreetMap. Distriktsforslag kan følge egnede gennemgående forløb før vejforslagene. Blå vandløb og grå stiplede jernbaner vises i editoren og i den lokale kortbaggrund; husnumre og besøgsprikker beholder deres styrke. Ældre kortdata skal opdateres ved at hente relevante udsnit igen.

Første beregning bruger sammenhængende forløb i lag 0 uden bro-/tunnelmærkning. Huller, navneskift, forgreninger og bro-/tunnelstykker forbindes ikke ved gæt. Alle adresser og lejligheder kontrolleres med de eksisterende geometriregler, og ændrede skel kræver ny forhåndsvisning. Forslag kan fortsat rettes og kræver OPRET KORT før oprettelse. Kontroltekster om skel følger dansk/engelsk og bevarer kildens navne. W16 er fortsat delvist åben for mere komplekse vejnet og yderligere skeltyper. [Vejledning om naturlige skel](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/docs/NATURLIGE-SKEL.md).

## 1.12.0-beta.52 · Forslag langs enkle vejforgreninger

W16, delopgave: Automatisk distriktsinddeling kan nu også afprøve gennemgående forløb i enkle forgrenede vejnet. Kun lokale vejstykker med samme navn og præcist fælles registrerede punkter forbindes; knæk og kurver bevares. Eksisterende uforgrenede forslag prøves først. Besøgstallet og de hidtidige geometrikontroller vælger mellem mulige faktiske vejforløb, før et geometrisk reserveforslag anvendes.

Navneskift, huller, sløjfer og uklare kryds gættes ikke, og søgningen har faste arbejdsgrænser. Lejligheder i samme hus holdes sammen; adresser, besøgstal og eksisterende kort bevares. Forslaget kan fortsat rettes og skal godkendes med OPRET KORT. Ingen nye netkald eller automatisk kortoprettelse. Dansk/engelsk vejledning forklarer begrænsningerne. W16 er ikke samlet afsluttet: vandløb, jernbaner og mere komplekse vejnet kræver fortsat manuelt arbejde.

## 1.12.0-beta.51 · Topbar og roligere digitale kort

W66: Menighedsnavnet i topbaren står nu ved logoets hovedtekst i stedet for midt mellem hovedtekst og undertekst. Tom plads i logoets højre side udnyttes, uden at ændre logoets 360 × 66 pixels. Lange navne afkortes fortsat visuelt med den fulde tekst i hjælpeteksten; mobilens kompakte identitet, betamarkering og gemmestatus bevares. Den private reference er ikke medtaget i kode eller kontrolbilleder.

W40: På digitale Drive-kort nedtones kun baggrundens vejkort, ikoner/skel og lokale vej-/bygningslag. Valgte husnumre, røde besøgsprikker, distriktsgrænse, miniature og kildeangivelse beholder deres styrke. Almindelige lokale korteksporter ændres ikke. Eksisterende Drive-filer, links og QR bevares; layoutopfølgning beder om ny lokal forhåndsvisning og udtrykkelig godkendelse, ikke automatisk upload eller genpublicering. Fiktive tætte/spredte kort og topbarer i stabil-/betavisning ved 320/390/768/1440 pixels indgår nu i browserkontrollen.

## 1.12.0-beta.50 · S-13 med navne og udleveringer

W69: Den lokale historikimport aflæser nu også forkyndernavne, udleveringer og indleveringer i understøttet digital S-13. Efter ejerens afklaring bliver en udlevering uden indleveringsdato et aktivt udlån; en indlevering afslutter udlånet og registrerer kortet som gennemgået. Forhåndsvisningen viser navnematch, nye forkyndere, aktive/afsluttede udlån og konflikter før udtrykkelig godkendelse. En ekstra femkolonners CSV-skabelon understøtter manuel overførsel fra scanninger og fotos; den eksisterende skabelon med kortnummer/dato bevares.

Entydigt ens navne genbruges. Dubletter og allerede kendte kortcyklusser springes over; overlappende udlån, uklare navne, ugyldige datoer og gendannelige poster skal rettes før lagring. En kendt gennemgang uden udlån kan kobles til den importerede udlevering uden at tælle igen eller ændre dato/besøgstal. Eksisterende udlån overskrives ikke. Aktive udlån med ældre udleveringsdato medtages; afsluttet historik følger toårsgrænsen. Hele importen gemmes atomisk. Historiske besøgstal gættes ikke, og filer/navne videresendes ikke automatisk.

## 1.12.0-beta.49 · Forstå Adressevælger og token

W36: Kortdata forklarer nu Adressevælgerens online vejforslag, valgfriheden og forskellen fra Datafordelerens DAR GraphQL-forbindelse og API-key. Det fremgår, hvilke søgefelter der sendes ved online forslag, og hvordan forslag kan begrænses til lokalt gemte veje. Status viser standardtoken eller gemt egen token uden at vise værdien. Det valgfrie tokenfelt er flyttet under Avanceret, og det forklares, at et tomt felt og Gem tokenvalg gendanner standardtoken uden at ændre Datafordeler-nøglen. Dansk/engelsk vejledning og link til KDS’ officielle tokenvejledning følger med. Opslag, forbindelser og gemmehandlinger fungerer som før.

## 1.12.0-beta.48 · Sammenlign månedstal med sidste år

W32: Forsidens månedsgraf viser nu parvise søjler for det valgte tjenesteår og samme måneder sidste år. Tabellen viser de præcise datoperioder og registrerede antal. Indeværende måned tælles til i dag og til samme kalenderdato sidste år; afsluttede måneder sammenlignes som hele måneder, og skuddag tilpasses kalenderen. Fremtidige måneder er ikke begyndt. Manglende registreringer fra sidste år vises som ? / Ingen registreringer frem for et bekræftet nul. Der vises ingen misvisende procentændring ved ukendt historik. Gentagne gennemgange og arkiverede kort tælles fortsat med; personnavne og IB indgår ikke.

W31-opfølgning: Den manglende typing_extensions-afhængighed til pypdf på Python 3.9/3.10 følger nu med lokalt og med licens. PDF-processen bruger isoleret Python uden installerede tredjepartspakker, så aflæsningen afhænger af programmets egne filer. Beta.47’s Python 3.9-kontrol identificerede manglen. Udgivelsen kræver nu også fulde Python 3.9-/3.13-prøver direkte i betaforløbet. Historikimporten kræver fortsat grønne kontroller før afslutning.

## 1.12.0-beta.47 · Lokal historikimport

W31: Indstillinger → Data kan importere de seneste to års gennemgange fra CSV og understøttede digitale S-13-filer: den originale udfyldelige formular og LTM’s egen PDF-eksport. Filen aflæses lokalt; kortnummer og gennemgangsdato vises i en redigerbar kladde før udtrykkelig godkendelse. Navne og udleveringsdatoer importeres ikke. Dubletter og ældre datoer vises som fravalgte; ukendte/uklare kort, fremtidige datoer og gendannelige poster skal rettes før hele importen kan gemmes. Eksisterende udlån og historiske registreringer overskrives ikke. Aktuelle og arkiverede kort understøttes. En ændret database eller udløbet forhåndsvisning kræver ny kontrol.

Historiske besøgstal gættes ikke fra nutidens adresser: importerede gennemgange markeres med ukendt besøgstal, og rapporten forklarer deres udeladelse fra besøgsskønnet. Scanninger/fotos og andre PDF-layouts indtastes i CSV-skabelonen. Ekstern OCR er kun et frivilligt alternativ med tydelig oplysning om usikker privatlivssikkerhed; ingen fil videresendes automatisk. PDF-læsning sker i en tidsbegrænset lokal proces med medfølgende pypdf og licens.

Eksportforbedringerne fra den ikke udgivne beta.46-kandidat følger med. Dens pakkekontrol stoppede korrekt, fordi server- og HA-versionen var forskellige; begge versionsfelter er nu beta.47. Ingen offentliggjort beta overskrives.

## 1.12.0-beta.46 · Hurtigere læsearkiv

W57-opfølgning: PDF-dannelse holder ikke længere databaselåsen under hele arbejdet. Appen kan fortsat bruges, og dataversionen kontrolleres igen før download; ændrede data giver ingen delvis fil. Kortfiltreringen bruger ét frosset datasnapshot frem for gentagne databaseopslag pr. kort. Kortbilleder dannes med en uigennemsigtig baggrund for mindre billedbehandling. Ingen ændring af gemte data eller arkivets indhold.

407 Python-prøver består (én forventet overspringning), herunder ændring under eksport og optælling af databaseopslag. Eksisterende browser- og platformskontroller kræves før udgivelse.

## 1.12.0-beta.45 · Læsearkiv og forenklet forside

Tre sammenhængende ønskepunkter: W57, W68 og W48. Det fulde lokale læsearkiv fra eksportarbejdet i beta.44 følger med her: fire PDF'er, CSV og S-13 for hele historikken med indlejrede digitale OpenStreetMap-kort. Hvert kort vises og medtages af brugeren; ingen automatisk massehentning eller Google-upload.

W68: Ejerens nye feedback erstatter W44-løsningen: både datointervallet og den forklarende tekst under Dit lokale overblik er fjernet helt. Tjenesteårets overskrift og rapporternes egne perioder bevares.

W48: Forsidens gennemsnit viser hele måneder og dage i stedet for et decimaltal i måneder. Samme kendte intervaller for aktuelle og arkiverede kort anvendes. Gennemsnittet afrundes én gang til nærmeste hele dag og omregnes med 30 dage pr. måned, som oplyses ved tallet. Ental/flertal, 30-/60-dagesgrænser og manglende historik er kontrolleret på dansk/engelsk. Ingen datoer eller historik ændres.

## 1.12.0-beta.44 · Læsearkiv med PDF, CSV og fuld S-13

W57: Indstillinger → Data tilbyder en lokal ZIP, der kan læses uden LTM. Fire PDF'er indeholder alle forsider på den originale blanke formular, IB-bagsider pr. kort, digitale kort og alle opgaver. S-13 følger for hvert tjenesteår i den gemte historik. CSV dækker kort, præcise adresser og eksisterende vejlinjer, IB, udleveringer med forkyndere, gennemgange, områder, forkyndere, opgaver, besøg og menighed. Aktive og arkiverede registreringer bevares. Ingen nøgler, adgangskoder eller rå forbindelses-/indstillingsfiler kopieres.

Digitale kort bruger appens offentligt afgrænsede kortindhold og OpenStreetMap-baggrund. Hvert kort vises og medtages af brugeren før næste kort hentes; der er ingen automatisk massehentning. Den færdige PDF har indlejrede billeder og kræver ikke internet. Kort uden geografi fremgår af forsider og CSV. OSM-attribution bevares.

Eksporten bindes til én dataversion. Manglende billeder, ændrede data, udløbet forløb, annullering eller fejl giver ingen delvis download. ZIP'en har kontrolsummer og læsevejledning og ændrer hverken data, genprintgodkendelser, backupdato eller Google-adgang. CSV bevarer Unicode og beskytter mod fortolkning af brugerdata som regnearksformler; tegn uden for PDF-standardfonten vises med deres Unicode-kode i læse-PDF. Den eksisterende gendannelsesbackup er uændret.

## 1.12.0-beta.43 · Fælles rapportoversigt og forklaret datoperiode

W51: Rapporten samler tjenesteåret og de seneste 12 måneder med hver sin periode, gennemgange, anslåede besøg, dækning og månedsgraf på én fælles oversigt. Oversigten findes både digitalt og på den første printside. Kortene følger fortsat på to særskilte sider med tydelige periodeoverskrifter; original S-13 og distriktets oplysninger bevares. Rapportens to første faner vælger, hvilket periodekort der vises under oversigten. Målinger, historiske år og aktuelle kortbestande beregnes som før. Ingen IB-adresser indgår i oversigten.

W44: Datoerne under Dit lokale overblik forklarer nu udtrykkeligt perioden for gennemgange og anslåede besøg. Kort og opgaver viser aktuel status; datoerne er ikke en installationsdato. Hjælpen følger dansk/engelsk.

## 1.12.0-beta.42 · Ændringslog i Home Assistant

W64: Home Assistant-pakkens ændringslog var stoppet ved beta.29, selv om projektets ændringslog var opdateret. Appmappens CHANGELOG.md indeholder nu også beta.30–42 i samme rækkefølge som projektets ændringslog. Tidligere versionsnoter bevares; ældre udgivelser og tags ændres ikke.

Pakning af både komplet program og HA-beta afvises fremover, hvis de to ændringslogfiler er forskellige, eller den aktuelle version ikke står først. Prøver dækker den tidligere fejl, bevaret historik og den faktiske ZIP-fils ændringslog/kontrolsum. Der ændres ingen lokale data eller adressefunktioner. Visning på ejerens egen HA kontrolleres efter næste opdatering.

## 1.12.0-beta.41 · DAR-opslag uden aliaser

Ejerens læsende beta.40-kontrol accepterede almindelige opslag for alle fem DAR-entiteter, men afviste både ét alias og flere rodfelter. Adressehentningen bruger nu ét almindeligt opslag ad gangen, også ved mange ID'er. Samme tidspunkt, filtre, separate cursors, afbrydelse og fælles resultat-/anmodningsgrænser bevares. Ingen delvise svar frigives til import. Fiktive leverandørprøver afviser nu aliaser og flere rodfelter; vej- og grænseforløbet fejlede før rettelsen og består efter. En rigtig hentning efter opdateringen udestår; W62 er fortsat åben.

## 1.12.0-beta.40 · Læsende DAR-kontraktkontrol

W62 er fortsat åben. En ny kontrol i Kortdata → Datafordeleren prøver de samme projektioner og filtre som adressehentningen med fiktive søgeværdier. Den sammenligner enkeltopslag, ét alias og ti aliases uden at oprette hentningsjob, gemme adresser eller ændre checkpoints og forbindelsen. Kun faste fejlkategorier, genkendte fejlkoder og en afgrænset liste diagnoseord vises; ingen rå leverandørtekst, data, stier eller nøgler. Prøven er tidsbegrænset. Den eksisterende grønne forbindelseskontrol er ikke en prøve af de faktiske dataopslag. Der er endnu ikke dokumenteret en årsagsrettelse eller en vellykket livehentning.

## 1.12.0-beta.39 · Sikker GraphQL-diagnose og mindre opslag ved størrelsesfejl

W62: Beta.38-prøven fejlede både på grænsen og på en enkelt vej med en generisk GraphQL-afvisning. Den bagvedliggende afvisningsårsag er endnu ikke bekræftet. Fejlteksten viser nu en sikker kategori: GQL-SCHEMA, GQL-ACCESS, GQL-LIMIT, GQL-RESULT eller GQL-REJECTED, opslagets entitet og genkendte fejlkoder/feltnavne. Rå leverandørbeskeder, søgeværdier, URL'er, nøgler og fejlstier vises ikke. Dansk/engelsk bevarer de samme diagnostikkoder.

Kun genkendte størrelsesfejl udløser tilpasning: færre poster pr. side, enkeltopslag i stedet for alias-batches og derefter mindre grænseudsnit. Tidspunkt, filter, cursor og fuldstændighedskontrol bevares; vedvarende fejl stopper begrænset. Andre afvisninger genprøves ikke som størrelsesfejl. HTTP 400/422 med struktureret GraphQL-fejl behandles også. Ingen delvise resultater importeres. Ny faktisk ejerprøve er nødvendig; dette er ikke en færdigmelding af W62.

## 1.12.0-beta.38 · Ret tomme GraphQL-adressehentninger

W62: Punktstatus var fejlagtigt behandlet som adresse-/husnummerstatus 3. DAR-adressepunkter har en særskilt livscyklus med 8 = i brug, og tjenester kan udelade punktstatus. Punktopslag bruger nu entitets-ID/geometri og det fælles faste tidspunkt; husnumre, adresser, veje og postnumre kræver fortsat status 3. Punktsvar uden status og med status 8 accepteres; eksplicit ugyldige punktstatusser og brudte koordinater/relationer afvises. Hentning af vej, postnummer og grænse er dækket af realistiske, fiktive tests.

Gamle GraphQL-grænsecheckpoints genhentes automatisk med rettelsen, så et tidligere tomt udsnit ikke springes over som færdigt. Et reelt tomt resultat får en tydelig advarsel; et tomt GraphQL-svar kan ikke udgå områdets eksisterende lokale adresser. Ejerens prøve i beta.37 bekræftede fejlen; ny faktisk hentning i beta.38 mangler fortsat. Forbindelseskontrol alene er ikke bevis for adressehentning.

Grundlag: [DAR-livscyklus](https://danmarksadresser.dk/adressedata/kodelister/livscyklus) og [DAR GraphQL](https://confluence.kds.dk/pages/viewpage.action?pageId=187105632). Ingen lokale adresser eller nøgler er brugt som testdata.

## 1.12.0-beta.37 · Backuppåmindelse følger serverens kalender

W52-opfølgning: Sidste backupdato og appens i dag regnes nu i samme lokale serverkalender, også når UTC-datoen er dagen før. Dermed kommer 14-dagespåmindelsen ikke en dag for tidligt omkring midnat. Sommer-/vintertid dækkes af syntetiske tests. Det er en ren beregning ved læsning; tidsstempler, backupfiler, historik og udsættelser ændres ikke.

## 1.12.0-beta.36 · Ugentlige opgaver på forsiden

W53: En opgave kan gentages ugentligt på en valgt ugedag. Første forekomst er den valgte dag fra og med i dag. Forfaldne opgaver vises på forsiden og kan markeres udført derfra. Tekst, korttilknytning, opgaven og afslutningshistorikken bevares. Næste forekomst lægges på den valgte ugedag strengt efter udførelsesdagen. Forsinkede uger opretter ikke kopier eller opdigtede gennemførelser.

For tidlig eller gentagen udførelse af samme forekomst afvises; historik og næste dato gemmes atomisk og kan fortrydes sammen. Redigering bevarer historikken. Ingen gentagelse stopper fremtidige forekomster uden at slette opgaven/historikken. Ældre klienters almindelige tekstredigering fjerner ikke gentagelsen. Datoer/historik bevares ved genstart og gendannelse. Ingen automatisk kortflytning, upload eller ekstern påmindelse; dansk/engelsk skifter uden at miste formularens valg og tekst.

## 1.12.0-beta.35 · Lokal backuphistorik og påmindelse

W52: De seneste 100 manuelle backupforsøg vises under Indstillinger → Data med særskilt status for oprettet ZIP, startet browserdownload og afsluttet filskrivning via filvælgeren. Annullering registrerer ingen backup. Fejlet filskrivning beholder kun ZIP-oprettelsen; den udskyder ikke påmindelsen. Filstier, filnavne, nøgler og forbindelsesoplysninger gemmes ikke i denne historik. Eksisterende backupregistreringer bevares uden at blive omtalt som bekræftet filskrivning.

Forsiden påminder, hvis ingen overførsel er registreret, eller der er gået mindst 14 kalenderdage. Udsæt skjuler feltet til næste kalenderdag, ikke i 24 timer. Browserdownload betyder kun, at overførslen er startet; kontrollér filen i browseren. Historikken følger dataene ved gendannelse og indeholder kun registreringer fra før ZIP'ens oprettelse. Ingen automatisk backup, upload eller ekstern besked.

## 1.12.0-beta.34 · Opsætning følger gemte handlinger

W47: Relevante opsætningstrin afsluttes automatisk efter en gennemført gemning: menighed, mappeminimum, begge printprofiler, forkynder, kort, ydergrænse, IB-import og registreret backup. Fremdriften gemmes i samme transaktion som handlingen og følger med ved Fortryd. Åbning, forhåndsvisning og afvist gemning tæller ikke. Spring over og eksisterende fremdrift bevares. Forbindelser og den samlede gennemgang af udleveringer bekræftes fortsat manuelt; én registrering beviser ikke, at hele gennemgangen er færdig.

Nye installationer og en udtrykkeligt godkendt beta-nulstilling starter med mappeminimum 0, også for land. Eksisterende valg ændres ikke. Mappetrinnet afsluttes ved et ændret minimum eller et eksplicit indtastet og gemt 0; en uvedkommende indstillingsgemning godkender ikke standardværdien.

## 1.12.0-beta.33 · Hurtig oprettelse med inklusivt interval

W54: Hurtig oprettelse har et særskilt intervalvalg med start/slut inklusive, valgfrit antal cifre/nuludfyldning og ét valgfrit foranstillet bogstav. 0–300 med fire cifre giver 0000–0300, i alt 301 kort. Bogstavet og nuludfyldningen indgår i den synlige forhåndsvisning. Højst 500 kort oprettes ad gangen, og den eksisterende egen liste er uændret; her betyder 1–10 stadig ét bogstaveligt kortnummer.

Antal og alle endelige numre vises før godkendelse. Serveren efterprøver interval, længder og dubletter igen ved oprettelsen. Eksisterende, arkiverede og gendannelige kortnumre reserveres som før, uanset store/små bogstaver. Et ugyldigt interval eller én dublet stopper hele oprettelsen. Eksisterende kort overskrives ikke.

## 1.12.0-beta.32 · Én samlet opgavefunktion

W50: Noter og opgaver er samlet under Opgaver. Gamle noter bliver opgaver med uændret tekst, kortreference, datoer og udført-status, også efter import af ældre backup. Aktive og gendannelige poster konverteres i en transaktion; aktivitetshistorik ændres ikke til opgaver. Gamle data-/API-navne bevares for kompatibilitet. Redigering af udførte opgaver og tilknytning til arkiverede kort bevarer status og reference.

Navigationen tæller kun åbne opgaver. Kortlisten/mappen viser et tydeligt opgavemærke. Udleveringsformularen viser en stærkere advarsel med de åbne opgaver og opdaterer den ved kortvalg. Der er ingen ny obligatorisk spærring eller automatisk IB-ændring. Separate notefiltre, noteoprettelse og valg af note/opgave er fjernet fra opgavefunktionen. En valgfri opgave kan stadig tilføjes ved aflevering/gennemgang. KTM-besøgets selvstændige tekstfelt kaldes Bemærkning.

## 1.12.0-beta.31 · Logo i fuld størrelse og bevidst kortbetjening

W49: Det eksisterende desktoplogo bevarer 360 × 66 px, mens menighedsnavnet står på samme vandrette linje efter en tankestreg. Mobilikonet bevarer 34 × 34 px. Lange navne afkortes visuelt med hele titlen tilgængelig; beta-markering, navigation og gemmestatus er bevaret.

W59: Kortets interaktive detaljevisning kræver Ctrl/Command til panorering og hjulzoom, eller eksplicit aktivering til touch/tastatur. Normal rulning går til dialogen. Kortet kan låses igen uden at nulstille udsnittet. Lyttere fjernes ved lukning, og nyt kort starter låst. Medlemskab, gemte grænser, eksport og publiceringsgodkendelse ændres ikke.

Disse to ønskepunkter er afgrænset fra beta.30. Rigtig API-hentning og ekstern GitHub-cache/PR-oprydning er fortsat åbne ejer-/Support-trin. Main er stabil 1.11.1.

## 1.12.0-beta.30 · API-hentning og sikkerhedskopi

W62: Hentning af en vej med egen Datafordeler-nøgle afhænger ikke længere af det gamle systems vejforslag. Det gælder også vejene i et lille OSM-kortudsnit. Den nye kilde bruger det præcise officielle vejnavn og postnummer; der vælges ikke en tilfældig nabovej. Regler for komplette adresser, lejligheder, opdateringer og bevarelse af lokale data er uændrede. Rettelsen er testet med fiktive svar; ejerens rigtige API-hentning skal fortsat bekræftes.

W55: Ved HTTP 401/403 forklares på dansk/engelsk, at en ny nøgle kan være op til 15 minutter om at blive aktiv. Afvist adgang og nøglekontrol beskrives fortsat; andre net-/serverfejl forklares ikke som aktiveringstid. Prøv forbindelse er fortsat en bevidst handling.

W46: Indstillinger tilbyder Gem sikkerhedskopi som… i sikre browserkontekster med understøttet filvælger. Filnavn og placering vælges før hentningen. Annullering henter intet og registrerer ikke en backup. Først en afsluttet filskrivning registreres som gemt. Almindelig download og hjælp til browserens placering er bevaret, også i desktopudgaven; ingen automatisk upload.

W61: Udgivelsespakker og grene/tags er renset; GitHub-cache, gamle PR-henvisninger og resterende udgivelsesmetadata afventer ekstern oprydning. W63: Det brede eftersyn af faste eksempler er afsluttet med en ny test af tomme hentefelter. Main er fortsat stabil 1.11.1.

## 1.12.0-beta.29 · Neutrale felter i adressehentning

Faste vej-, postnummer- og husnummereksempler er fjernet fra Hent en vej og adressevalget. Felterne beskriver nu kun deres formål på dansk/engelsk. Den tidligere stedtekst er også fjernet fra oversættelser og erstattet med opdigtede testdata i prøverne. Gemte lokale adresser og den eksisterende vejnavnesøgning bevares.

W61 er fortsat kritisk og åben: rettelsen i denne beta er ikke en færdigmelding af oprydningen i tidligere udgivelser, betaer eller Git-historik. W62 om fejlslagen faktisk API-hentning er en særskilt, endnu ikke rettet fejl.

## 1.12.0-beta.28 · Kompakt opsætning og menighed i topbaren

Menighedsnavnet vises ved projektets logo i topbaren. Lange navne afkortes visuelt og kan læses i feltets titel; navn og gemmestatus holder sig inden for topbaren, også på mobil og i HA-betaen. Navnet gemmes fortsat kun lokalt.

Opgavelisten på forsiden fylder nu én sammenklappet linje med antal resterende trin. Listen har kompakte handlinger og genveje til menighedsnavn, mappeminimum, printvalg, valgfri Google Drive og første forkynder. Udført/overspringning og eksisterende fremdrift bevares. Listen spærrer ikke normal brug.

Indstillinger → Printprofiler kan nu gemme valg af blankt eller fortrykt papir særskilt for forside og IB-bagside, også før første kort. Eksisterende mål bevares. Gemning åbner ikke print og godkender ingen ændret kortside.

## 1.12.0-beta.27 · Daglig aflevering og tydelig opgavestatus

Kortstatus har nu tydelige farver for udleveret, i mappen og i kassen. Direkte udleverings-/afleveringsknapper åbner de normale kontrollerede formularer; den valgte kortmenu bevares. Ændrede kort kan fortsat være spærret for udlevering.

Daglig brug har fanen Aflever pr. forkynder: alle aktive udlån grupperes efter forkynder, flest kort først, med navnesøgning og aflevering fra hver kortlinje. Ens navne med forskellige registreringer holdes adskilt. Listen og sidemenuen fungerer på smalle skærme og på dansk/engelsk. Ingen udlåns- eller delingsregler ændres.

Cirkelknappen ved opgaver og noter er forklaret med synlig hjælp og tooltip: markér udført eller genåbn uden at slette teksten.

## 1.12.0-beta.26 · Opgavelisten kan afsluttes

Planen på forsiden er nu en liste med Udført, Spring over og Fortryd. Afsluttede trin streges ud. Listen forsvinder, når alle trin er udført eller sprunget over; gemt status huskes på installationen efter genindlæsning. At åbne et trin afslutter det ikke automatisk. Opsætningsplanen kan stadig åbnes fra Indstillinger. Dansk/engelsk og smalle skærme er kontrolleret med fiktive data.

## 1.12.0-beta.25 · Præcis forklaring af adressefristen

Januarfristen gælder lukningen af gammel DAR REST-adgang. API-nøgler til DAR GraphQL kan også oprettes bagefter. Nøglevejledningen og opsætningsplanen forklarer nu forskellen og anbefaler overgang i god tid for at undgå pause i nye hentninger. Gemte adresser bevares. Officielle kilder er kontrolleret 17.10.2026.

## 1.12.0-beta.24 · Læsbare lokale navneforslag

- Navneforslag ved udlevering har lys tekst på mørkegrå baggrund. Hover og tastaturmarkering har en lysere mørk tone og tydelig kant.
- Den fejlagtige hvide fallback er fjernet. Lokale navne, søgning, valg og udleveringspayload er uændrede.
- Browserkontrol bruger opdigtede navne, kontrollerer høj kontrast i den normale tilstand, tastaturmarkering/valg og smal/bred visning.


## 1.12.0-beta.23 · Samlet opsætning og obligatorisk rundtur

- Én normal opsætningsguide med introduktion til lokal drift, fælles HA-installation, backup og valgfri deling. Den parallelle detaljerede guide er samlet ind i forløbet.
- Svar gemmes først som uafsluttet. Rundturens sidste trin afslutter opsætningen og åbner forsiden med den personlige plan; guiden genåbnes ikke. Afbrydelse kan genoptages, og tidligere fuldførte installationer bevares.
- Sprogskift i rundturen bevarer trin og fokus. Afvist/sen afslutning og dobbeltklik håndteres uden ekstra skrivning eller lukning af nyere dialoger.
- Kortplanen har en direkte indgang til egen Datafordeler-nøgle. Officiel REST-frist 15.01.2027 er genkontrolleret; den eksisterende GraphQL-import bevares. Egen konto er et ejertrin.


## 1.12.0-beta.22 · Fast punkt 8–10: print, programpakke og slutkontrol

- Dansk/engelsk printdialog og printknapper med bevarede felter, profilværdier og uændrede originalformularer/rapportindhold.
- Printforberedelse beskytter mod dobbeltklik, ændrede felter/data, navigation og nyere dialoger. Fejlet billedafkodning spærrer print; profilgemning godkender ikke genprint.
- Appens versionsvisning følger den kørende server i begge kanaler; gammel API-etiket er rettet efter pakkestartprøven.
- Komplet programpakke med de linkede vejledninger, køreplan, lokal restliste og demovejledning. Pakningen stopper ved manglende original S-12-PDF eller brudte interne vejledningslinks.
- Printguide og slutkontrol på dansk/engelsk. Egen printer, HA/telefon/VPN, Google-/Datafordeler-konto og eventuel skærmlæser står tydeligt som ejerprøver.
- Fiktive JavaScript-, Python-, pakke- og Chromium-prøver kontrollerer både programforløb og faktiske front-/bagside-/rapport-PDF'er ved fire skærmbredder. Main er stabil 1.11.1.


## 1.12.0-beta.21 · Fast punkt 7: login, tastatur og fokus

- Login kan vælges på dansk/engelsk uden at genskabe felter. Indsendelse kræver én bekræftet anmodning, har timeout og blokerer dobbeltklik. Fejl bevarer indtastning og passende fokus; kun sprogvalget gemmes som præference.
- Loginets lille oversættelse ligger i den allerede offentlige loginfil. Generel app-sprogfil, øvrige programfiler og data kræver fortsat login; cookie, adgangskodekontrol, netværks-/oprindelseskontrol og rategrænse er uændrede.
- Dialoger får navngivning fra overskrift, sammenknyttede feltlabels og meningsfuldt startfokus. Tab/Shift+Tab bliver i dialogen, Escape bevarer den eksisterende gemmekontrol, og lukning returnerer til åbneren, også efter genoptegning.
- Fiktive login-/fokusprøver, LAN-grænser og offline Chromium dækker begge loginvarianter ved fire bredder samt appens native dialog- og Escape-forløb. Fast køreplan: 70 % (7/10). Næste er printbetjening med uændrede originalformularer.

## 1.12.0-beta.20 · Fast punkt 6 afsluttet

- Særskilte skrivninger i opsætning, IB-/kortimport, deling og førstegangsopsætning bruger nu samme tydelige faser: usikker kvittering, kendt afvisning eller bekræftet skrivning med behov for genindlæsning. En læsefejl udløser aldrig automatisk gentagelse.
- Nyere opsætningssessioner, imports, formularer og datasnapshots bevares ved sene svar. Delingshandlinger blokerer dobbeltklik og viser mislykket statuslæsning særskilt efter en accepteret handling.
- Supplerende kontroller beskytter lokale billedvalg, geodatahentninger, farve-/Se bort fra-opfølgning og nyere oprydningskontroller mod sene svar.
- Programprøver og offline Chromium dækker gennemført kortoprettelse med efterfølgende læsefejl, bevaret plan og eksplicit kontrol uden dobbeltskrivning. Fast køreplan: 60 % (6/10). Næste er login, tastatur og fokus; ønskelisten venter.

## 1.12.0-beta.19 · Forståelige domænefejl på dansk og engelsk

- Faste fejl fra kort, adresser, udlån, IB, opsætning, administration og backup følger valgt sprog. Ukendte diagnostikker vises fortsat uændret og HTML-escaped.
- Parameteriserede fejl får valgfrie skabelon-/parametermetadata. Den oprindelige danske fejltekst og ValueError-kontrakt bevares. Brugerens navne, kortnumre, interne filnavne og talgrænser ændres ikke.
- Dato-/IB-linjefejl og backupforhåndsvisning bruger samme sikre renderer. Sprogskift bevarer felter og opdaterer beskeden på stedet; ukendte eller ugyldige metadata falder tilbage til originalen.
- JSON-læsning har nu også tidsgrænse efter modtagne HTTP-headere. Nye kildekatalog-, HTTP-, fiktive UI- og Chromium-prøver dækker fejlforløbene. Fast punkt 6 er fortsat i gang; 50 %.

## 1.12.0-beta.18 · Sene svar bevarer nyere arbejde

- Opfølgning efter noter, IB og omstrukturering kan ikke åbne gamle dialoger eller skifte væk fra nyere arbejde. Sene formularfejl overskriver ikke en nyere fejlbesked.
- Omstruktureringens preview bindes til felter, adressevalg, side og revision. Nyeste kontrol vinder; bekræftelse kræver fortsat ÆNDR KORT og blokerer dobbeltklik. Den kontrollerede payload ændres ikke.
- En kvittering for en gammel baggrundsgrænse rydder ikke en nyere tegning. Områdesletning bevarer et nyere filtervalg.
- Fiktive hændelsesprøver og offline Chromium dækker ændrede felter og sen accepteret opdeling ved fire bredder. Fast punkt 6 er fortsat i gang; køreplan 50 %.

## 1.12.0-beta.17 · Gendannelse uden tab af nyere kladder

- Gendannelse og beta-nulstilling sender kun én anmodning ved dobbeltklik. Uændrede samtykke-, kontroltoken-, versions- og beta-begrænsninger bevares.
- En bekræftet import/nulstilling med fejlet genindlæsning markeres som gemt med behov for kontrol, ikke som en import der skal gentages. Nye skrivninger spærres indtil eksplicit genindlæsning.
- Sene svar eller datasnapshots erstatter ikke nyere dialoger eller navigation. Sikkerhedskopien fra en normal gennemført handling kan fortsat hentes lokalt.
- Nye fiktive transferprøver og offline Chromium ved fire bredder dækker sen accepteret import og bevaret nyere kladde. Fast punkt 6 er stadig i gang; 50 % er uændret.

## 1.12.0-beta.16 · Sikker gemmekvittering og bekræftelse

- Fælles dansk/engelsk fejlbeskeder skelner mellem læsefejl, afvist ændring, udløbet login, usikkert resultat og bekræftet gemning med fejlet genindlæsning.
- Usikkert resultat stopper kø og automatisk gemning. Forbindelsestjek gensender aldrig; eksplicit Opdater henter det gemte resultat før videre arbejde. Felterne bevares, indtil brugeren vælger at lukke uden gensendelse.
- Skrivepayload kopieres ved kølægning. Sene svar lukker ikke nyere dialoger. Administrative previews kræver samme formular, værdier og revision; dobbelt bekræftelse blokeres.
- Fiktive request-/bekræftelsesprøver og offline Chromium dækker tabt svar efter faktisk gemning ved fire bredder. Punkt 6 er fortsat i gang; domænefejl og de øvrige bekræftelsesforløb mangler. Fast køreplan uændret 50 %.

## 1.12.0-beta.15 · Google Drive- og QR-betjening

- Kortgemning skelner mellem serverens nye revisionsnummer og en ændret tegning. En vellykket gemning afsluttes korrekt, også ved oprettelse af et nyt kort; nyere kladder bevares. Prøvet gennem den rigtige API-håndtering.
- Dansk/engelsk i delingsstatus, Google-guide, preview/godkendelse og QR. Sprogskift bevarer billede, checkbox, URL og godkendelsesdata. Offentlige billeder og originale printformularer ændres ikke.
- Nyeste polling vinder. Sene preview-/QR-svar erstatter ikke nyere dialoger. Publicering blokerer dobbeltklik, kræver en uændret kontrolleret revision og bevarer nyere navigation efter svar.
- Forbindelsesfilens indlæsning beskyttes mod navigation og genopbygning under polling. Ugyldig JSON vises uden at citere filindhold. Program-/browserprøver bruger fiktive svar, et genereret prøve-PNG og ingen Google-konto. Fast køreplan: 50 %.

## 1.12.0-beta.14 · Opsætning og lokal IB-import

- Dansk/engelsk i opsætningens fire trin, områder, nummerering, kortforslag og lokal IB-import. Sprogskift bevarer kortinstans, kladdenavne/-numre, geometri og IB-kontrol. Dataværdier, CSV-kolonner og bekræftelsesord er uændrede.
- Ændret opsætning, dato, fil, revision eller navigation beskytter mod forældede forslag. Ombyttede filindlæsninger bruger kun den nyeste fil; fejlede filer kan ikke godkende et gammelt IB-token. Felter spærres under oprettelse.
- Nye kontrakt-/hændelsesprøver og udvidet offline Chromium ved fire skærmbredder. Den faste køreplans punkt 4 er afsluttet: 40 %.

## 1.12.0-beta.13 · Korteditor og grænser

- Dansk/engelsk betjening i geografisk korteditor, samlet grænse og KML/GeoJSON-import. Sprogskift bevarer kort, zoom, fokus, valgte adresser, tegning, formularer og importfil. Gemte typer og API-værdier ændres ikke.
- Forsinkede forhåndsvisninger, oprydning og import kan ikke erstatte nyere kladder/dialoger. Gemning bruger en fast kopi, afviser ændret/annulleret valg før skrivning og bevarer en nyere tegning under gemning. Dobbeltgemning og reference-deling af kortgrænser er rettet.
- Gentagelige fiktive Chromium-prøver ved 320/390/768/1440 pixels kræves før HA-betaudgivelse. Kortvælgeren holder sig inden for en smal skærm. Fast køreplans punkt 3 er afsluttet; planen er 30 %, og ønskelisten venter.

## 1.12.0-beta.12 · Digitalt QR-kort

- Delt kortbillede får et nyt blåt layout med stor kortflade, tydeligt kortnummer/navn og miniature af printforsiden i hjørnet. Den blanke S-12-forside og printets vejlinjeformatering genbruges.
- Miniaturen bygges kun af den offentlige opskrift, ikke af private kortdata. IB, noter og kortholdere indgår ikke. Lange navne og tætte/tomme kort er afprøvet i fiktive SVG/PNG-billeder.
- Eksisterende QR-links og adgangscyklus bevares. Ældre layout markeres til manuel opdatering; nyt billede kræver fortsat preview og udtrykkelig godkendelse.

## 1.12.0-beta.11 · Kurvede og sammenhængende vejskel

- Automatisk inddeling kan følge vejens faktiske knæk og kurver. Samme-navn-vejstykker forbindes kun ved præcist fælles endepunkt uden forgrening; huller lukkes ikke ved gæt.
- Tvetydige skæringer, løkker, selvkrydsning og komplekse grænsekrydsninger afvises. Areal, overlap, hvert adressepunkt og hele huse kontrolleres. Manuelle rettelser og eksplicit samlet oprettelse bevares.
- Dansk/engelsk inddelingsvejledning beskriver lokale vejdata, kontrol og begrænsninger. Naturlige skel er næste del af W16; ønsket er ikke markeret afsluttet.

## 1.12.0-beta.10 · Første vejbaserede skel

- Automatisk kortinddeling foretrækker nu egnede, lokalt hentede gennemgående lige vejstykker som skel, også på skrå. Ingen nye netkald og ingen automatisk kortoprettelse.
- Korte vejfragmenter forlænges ikke kunstigt. Husenes lejligheder og faktiske adressepunkter bevares samlet. Manglende egnede vejstykker giver en tydelig markering af geometrisk deling til manuel rettelse.
- Vejdata indgår i kontrollen af forældede forhåndsvisninger. Kurvede veje, sammensatte vejforløb og naturlige skel er fortsat udestående under W16.

## 1.12.0-beta.9 · Forkynderforslag

- Udlevering får en lokal søge- og forslagsliste med fornavn/efternavn, højst otte forslag, tastaturvalg og berøring. Søgetekst og navne forlader ikke appen.
- Nye navne kan fortsat skrives frit og oprettes først ved registrering. Escape/Tab vælger ikke et navn; Enter i en åben liste gemmer ikke ved et uheld. Dansk/engelsk og formularens data bevares.
- Programprøver dækker hændelser og gemmekontrakt; visuel mobil-/skærmlæserkontrol står særskilt.

## 1.12.0-beta.8 · DAR GraphQL

- Egen lokalt gemte Datafordeler-nøgle bruges til komplette vej-, postnummer- og grænsehentninger. Flade opslag sammenkobles lokalt med stabile adresse-ID'er og bevarede etage-/døroplysninger.
- Grupperede opslag reducerer antal netkald. Kilde og skemafingeraftryk følger checkpoints; ufuldstændige svar gemmes ikke som komplette veje/udsnit. Genstart fortsætter kun ufærdige dele af samme hentning.
- Uden nøgle fortsætter den hidtidige kilde. Ved kildeskift kræves en ny opdatering. Adresseforslag fra Adressevælger er fortsat en særskilt tjeneste. Egen Datafordeler-/HA-prøve står særskilt fra fiktiv programkontrol.

## 1.12.0-beta.7

- Kortdata får trinvis vejledning til egen Datafordeler-konto og API-key, lokal lagring og eksplicit forbindelseskontrol. Nøglen udelades fra portable sikkerhedskopier.
- Dette klargør DAR v3-forbindelsen; selve adresseimporten flyttes i et efterfølgende trin.

## 1.12.0-beta.6

- Den ekstra opfølgningsliste er fjernet fra KTM-rapporten og samlet PDF efter ejerens ønske. De øvrige rapportoversigter og original S-13 bevares.

## 1.12.0-beta.5

- Opsætningsguidens radioknapper arver ikke længere tekstfelters fulde bredde. Valgtekst og forklaring holdes inden for deres boks på smalle skærme.

## 1.12.0-beta.4

- Rapporten får en aktuel opfølgningsliste med manglende historik, gennemgange over 12 måneder og aktuelle udlån over fire måneder.
- Kort vises én gang med datoer og årsager; arkiverede kort udelades. Ingen personnavne, noter eller IB-adresser føjes til listen. Samme liste følger samlet PDF.

## 1.12.0-beta.3

- Fast topbar ved rulning på computer og mobil; logoet åbner forsiden med kontrol af ugemte ændringer.
- Fuldt projektlogo i topbaren på computer, kompakt mærke på mobil og tydelig beta-identitet.
- HA-ikon og logo følger nu både normal programpakke og betapakke.

## 1.12.0-beta.2

- Betaen kan nulstille testdata med bekræftelse, automatisk lokal sikkerhedskopi og kontrol af delte kort. Login og forbindelser bevares.

## 1.12.0-beta.1 · HA-beta under klargøring

- Separat HA-betakanal med port 8788, egne data og egen login-cookie. Små nummererede prereleases udgives først efter program-, Mac-, Windows- og HA-kontrol.

- Google Drive-billeder er private mellem udlån og åbnes automatisk ved udlevering. QR-linket bevares; afventende/fejlede adgangsændringer og nyt forsøg vises. Ingen udlåns- eller personoplysninger uploades.

- Selvstændigt link til idéer og feedback via GitHub med valgfrie bilag og tydelig oplysning om offentligt indhold; aktiveres med næste stabile udgivelse.
- HA-installationssiden forklarer funktioner, første start, lokal adgang og backup.
- KTM-kort får læsbare distriktnumre med forbindelsesstreger, når der er trangt. Kortets egen printside bliver automatisk stående eller liggende efter geografien; fiktive PDF-rapporter er kontrolleret visuelt.
- Det overflødige tal for midlertidige kort er fjernet fra distriktets oplysninger.

- Spørgsmål ved første start med personlig opsætningsplan og en valgfri rundtur i de rigtige sider.
- Lokal Excel-/CSV-import af allerede fordelte kort, områder, kortnavne og adresser med kontrol før oprettelse.
- Præcise importerede lejligheder kan bruges til lokal IB-import; besøgstal bevares.
- Regnearksskabelon med dansk vejledning og udfyldningsfelter.


- Blå identitet og valgfri velkomstguide.
- Dansk/engelsk navigation, centrale kort-/udleveringsformularer, forkyndere, opgaver, indstillinger, rapportskærme, kortoversigt og adresselister.
- Kladder bevares ved sprogskift og flere forsinkede forhåndsvisninger.
- Forbindelseskontrol bekræfter ikke en usikker gemning.
- Backupoversigten sammenligner synlige kort og noter korrekt og bevarer arkiverede poster.
- Originalt dansk print, gemte værdier og datastier bevares.

## 1.11.0 · første offentlige kildekodeudgave

- Lokal distriktsadministration til Mac, Windows og Home Assistant OS.
- Opstart på en fast lokal IP kræver ikke reverse DNS; det undgår forsinket Mac-start uden netværksopslag.
- Kort, forkyndere, udleveringer, gennemgange, IB, lokale backups og dansk print.
- Gennemgået programkode og tomme S-12/S-13-formularer; ingen brugerregistreringer eller private kørselsfiler.
- Dansk README og opsætningsguider med engelsk som ekstra valg.
- Installation og senere programopdateringer via HA-repository uden manuel kopiering af programfiler.
