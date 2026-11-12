# DAR: Egen tekst til vejlinjer på S-12-forsiden

## Formål og datakilde

På geografisk tilknyttede kort kan en bruger med `cards.view` og `cards.edit` udfylde valgfri fritekst til vejnavn og husnumre på hver forsidelinje. `geo_addresses`, `addresses` og kortets besøgstal er fortsat autoritative og ændres aldrig af denne redigering. Manuelle kort uden DAR-adresser bruger fortsat den eksisterende vejlinjeredigering.

Den originale vej- og nummerværdi vises ved hvert tekstfelt. Forsiden samler DAR-vejlinjen og de udfyldte felter med tankestreger. **Ryd egen tekst på linjen** tømmer begge felter. Tekst gemt i tidligere betaer vises fremover som et supplement til DAR-vejlinjen. `front_revision` og `front_print_token` ændres, så en fysisk forside kræver ny godkendelse. Delte/publicerede kort får en ændret fingerprint og skal gennemgås og publiceres igen.

## Lagring og migration

Ingen SQL-schemaændring. I kortets eksisterende lokale JSON-payload lagres et valgfrit `front_line_overrides`-array med `source_ids` (DAR-adresse-id'er), `dar_road`/`dar_numbers` som kilde-snapshot og `road`/`numbers` som eventuelle manuelle værdier. Manglende felt betyder ren DAR-visning for eksisterende installationer. Synkronisering må aldrig fjerne arrayet. Ved entydigt overlap i adresse-ID'er bevares overstyringer ved nye intervaller eller omdøbt vej; ved splittede/sammenlagte, tvetydige grupper bevares overstyringen uden at blive vist på en forkert linje. Der vises en advarsel, og eksporten indeholder den til efterfølgende gennemgang. Brugeren kan eksplicit nulstille uafklarede gamle overstyringer til DAR uden at ændre aktuelle vejadresser.

`front_addresses`, `front_label_unmatched` og `front_labels_token` er afledte værdier i lokal API-state, ikke gemte DAR-felter. Den eksisterende kort-JSON i ZIP-backup indeholder overstyringerne, så import/gendannelse bevarer dem. Læseeksport inkluderer nu `CSV/forsidetekster.csv` med originale og viste værdier; uafklarede overstyringer mærkes særskilt.

## API, adgang og samtidighed

Ny mutationshandling `card.front_labels.save` kræver `cards.view` + `cards.edit` gennem den eksisterende profiltilladelsespolitik. Payload: `{card_id,expected_token,rows:[{source_ids,road,numbers}],clear_unmatched?:boolean}` hvor `null` betyder tomt fritekstfelt og en tekststreng er et supplement til DAR-værdien. Rækkernes adresse-ID'er kontrolleres mod serverens aktuelle forside. `expected_token` dækker både kortets geografiske grundlag og gemte overstyringer og afviser forældede redigeringsforsøg. Mutationen er atomisk i den eksisterende SQLite-transaktion og registreres i aktivitetsloggen; den kan fortrydes via den eksisterende korte undo-mekanisme.

Tekst normaliseres og længdevalideres. Kontroltegn, linjeskift og skjulte Unicode-formateringstegn afvises. HTML/SVG-output escapes; kortets fælles `frontRows` og `frontHTML` bruges af HTML- og PDF-print samt den rasteriserede S-12-PNG. Den digitale kortvisning læser de samme viste vejlinjer. Printens eksisterende layoutkontrol blokerer indhold, der ikke kan være på forsiden.

## Afhængigheder og parallelle branches

- **Database:** ingen migration; kort-payload får ét valgfrit felt. Undgå at andre funktioner erstatter hele kort-payloaden uden at bevare ukendte felter.
- **API:** `distrikt/app/store.py`, `front_labels.py`, `profile_policy.py`, `geography.py`.
- **Delte UI-/printfiler:** `app.js`, `map-export.js`, `index.html`, `server.py`, `sharing.py`, `readable_export.py`. Disse kan konflikte med parallelle PR'er om kortidentifikatorer, historik, massekort og mobilvisning.
- **Release:** PR mod `develop`; ingen direkte ændring i `main` og ingen Stable-release. Opdatér branchen efter fælles integration, genkør hele CI og foretag manuel print- og responsiv-test før merge.

## Test

Se `distrikt/tests/test_front_label_overrides.py` og `test_front_labels.cjs` for fiktive DAR-adresser, nulstilling, gentagen opstart, DAR-omdøbning, tvetydig opdeling, samtidighed, rettighedskontrol, backup/import, eksport og publiceringsfingerprint. Visuel kontrol af både original dansk/engelsk S-12, A4-PDF, PNG og lange tekster hører med til review; ingen rigtige adresser eller navne må benyttes.
