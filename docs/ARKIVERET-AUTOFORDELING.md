# Arkiveret autofordeling · W81

Fra beta.61 er automatiske forslag til distriktsgrænser og kortinddeling sat på pause efter ejerens afklaring 21.10.2026. Manuelle kort, samlet ydergrænse, adressehentning, kortimport og lokal IB-import er fortsat aktive. Der slettes ingen eksisterende distriktskort eller historik.

## Bevaret kode

- `distrikt/app/territory_partition.py` og tilhørende geometri: selve beregningen.
- `distrikt/app/setup_store.py`: forhåndsvisning, grænsejustering, signatur/token og atomisk kortoprettelse; IB-funktionerne bruges fortsat.
- `distrikt/app/setup_jobs.py`: den tidligere asynkrone beregning.
- `distrikt/app/setup-ui.js`: generatorens skærme og håndtering er bevaret bag `autoDivisionEnabled:false`. Det er ingen brugerindstilling. Aktiv opsætning åbner kun lokal IB-import.
- `docs/AUTOMATISK-INDDELING*.md` og `docs/NATURLIGE-SKEL.md`: tidligere vejledninger med tydelig arkivmarkering.

Serveren afviser `setup.preview`, `setup.adjust.preview`, `setup.apply` og `/api/setup/job` før beregning eller skrivning. En ændret browservariabel åbner derfor ikke serverfunktionen. Gamle onboarding-svar ændres ikke ved læsning; `auto` vises som manuel inddeling og normaliseres ved næste lagring.

## Prøver og senere genoptagelse

Direkte algoritme-/lagerprøver bevares. Generatorens isolerede JavaScript-/browserprøver aktiverer udtrykkeligt den arkiverede UI i deres fiktive testmiljø. Aktive standardindstillinger prøves særskilt: ingen generatorvalg eller trin, bevaret IB-/kortimport og afviste HTTP-kald uden dataændringer. Ingen netadgang eller private data kræves.

Genoptagelse kræver en ny udviklingsændring med ejerens aftalte omfang, gennemgang af W16 og test af både UI og serveradgang. Det er ikke nok at ændre browserflaget. Ingen nye vejnetalgoritmer er indført i beta.61.
