# LTM 1.12.35

Samlet Stable-opdatering af de færdige, verificerede Beta-funktioner siden Stable 1.12.34 (1.12.19-beta.36–beta.37). Eksisterende Stable-rettelser for gemning, scrollposition og IB-læsearkiv er bevaret. DAR-preview-rettelsen i den åbne PR #134 og de øvrige uafsluttede PR'er er **ikke** med.

## Nyt i Stable

- **Korrekte IB-tal i rapporter:** Alle aktive IB-linjer tælles, også manuelt registrerede uden kortlagt DAR-adresse. Det geografiske delantal inden for grænsen vises separat. Begge tal kræver IB-læserettighed.
- **Godkend sikre IB-adresser samlet:** Se en forhåndsvisning af entydige DAR-match på tværs af distriktskort, og godkend dem samlet. Tvivlsomme match bliver til manuel gennemgang. Serveren genkontrollerer rettigheder og datagrundlag før den atomiske gemning, og handlingen kan fortrydes samlet. Besøgstal og eksisterende IB-datoer ændres ikke.
- **Menighedstilpasning:** Under Indstillinger kan man selv navngive hjemme/kasse, i mappen og udleveret. Mappen kan fravælges, hvis menigheden kun bruger hjemme og ude. Gemte kortplaceringer, historik og tekniske statuskoder ændres ikke. Eksisterende vejledende kortantal og fordeling kan stadig indstilles.
- **Interne distriktskortnavne:** Hvert kort kan få et valgfrit internt navn op til 160 tegn. Navnene kan søges og vises i administrationen og bevares ved import, læsbar eksport og backup. De vises **ikke** på officielle S-12/S-13, offentlige kort eller andre udadvendte udskrifter. Identitet, officielle numre og historik er uændrede.

## Bevarede rettelser

- Gem og vejliste bevarer dialogadfærd, fokus, tekstmarkør og scrollposition.
- Forældede DAR-fejl og -statusbeskeder fjernes ved nye ændringer i korteditoren.
- IB-bagsider i læsearkivet bruger det opmålte normale printlayout, inklusive fortsættelsessider; eksportknappen er placeret ved Sikkerhedskopi.
- Stable-brugere beholder deres normale datamappe, login og port. Beta er fortsat en særskilt installation og opdateres ikke til Stable automatisk.

## Kontrol og udgivelse

Kandidaten skal bestå fælles Python-/JavaScript-/browser-/sikkerheds-/pakkeprøver på det præcise `main`-commit. Hvert Stable-spor udgives derefter særskilt fra **Stable release tracks**. Home Assistant, macOS-app, Windows-app og Windows-server kræver deres egne kontroller; macOS-server må først udgives efter dokumenteret fysisk Apple Silicon, LAN/VPN og genstartstest. Versionspakker og checksums må ikke overskrives.

## English

LTM 1.12.35 promotes all completed, released Beta features since Stable 1.12.34 (beta.36–beta.37) without including unfinished pull requests.

- **Reports:** Count all active do-not-call entries, including unmapped manual entries, while separately displaying the mapped subset. Preserve access checks.
- **Bulk address matching:** Preview and approve only safe, unique DAR matches across all cards, with validation, atomic saving and undo.
- **Congregation customization:** Set local home/folder/issued labels, customize card guidance and optionally disable the folder workflow without modifying stored placements, history or internal status keys.
- **Private territory names:** Add a searchable optional name to each card and preserve it through backup/import/export without changing official names, numbering or public S-12/S-13/share output.
- Existing Stable save, scroll, DAR-feedback and readable-archive fixes remain included. Pending PR #134 and other unfinished work are excluded.
- Each Stable release track requires its own tests and manual selection. The macOS-server physical test gate remains in force.
