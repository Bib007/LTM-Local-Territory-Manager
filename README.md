<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/logo-dark.svg">
  <img alt="Local Territory Manager – JW" src="assets/brand/logo-light.svg" width="640">
</picture>

# Local Territory Manager – JW

**Distriktsadministration på din egen computer eller Home Assistant.** Et uofficielt værktøj til Jehovas Vidner, vibe coded med **OpenAI Codex** og udviklet med udgangspunkt i arbejdet ved distriktsdisken.

[English](README.en.md) · [Installation](docs/INSTALL.md) · [Kom i gang](docs/FIRST-STEPS.md) · [Privatliv](docs/PRIVACY.md) · [Udviklingsplan](ROADMAP.md) · [Manuelle punkter](Dette-skal-hjaelpes-manuelt.md)

## Kom i gang

**Kandidat til stabil grundudgave: 1.11.0.** Kilden afventer den originale, tomme `distrikt/templates/S-13-background.jpg`. Den ufuldstændige kandidat skal ikke installeres eller udgives. De oprindelige formular- og pakkekontroller skal bestå, før en stabil udgave tilbydes.

**1.11.0** er det stabile udgangspunkt. Den videre udvikling følger [udviklingsplanen](ROADMAP.md).

- **Home Assistant OS:** Når den komplette udgave er verificeret, tilføjes repositoryet én gang i HA. Programmet installeres og opdateres derefter i HA uden at kopiere programfiler. [Dansk installationsguide](docs/INSTALL.md).
- **Mac / Windows:** Når udgivelsen er klar, hentes den komplette ZIP fra [Releases](https://github.com/Bib007/LTM-Local-Territory-Manager/releases). Installer Python 3.9 eller nyere én gang, og åbn den relevante `Start-Distrikt`-fil i `Distrikt-lokal`. Docker og pip-pakker er ikke nødvendige.
- **Eksisterende installation:** Bevar den fungerende app og dens data. Følg [opdateringsvejledningen](docs/INSTALL.md), og tag en privat sikkerhedskopi først.

Home Assistant kan holde appen tændt hjemme, mens den samme installation åbnes fra telefon, iPad eller computer. Udefra forbindes enheden til **VPN på egen router**, hvorefter appens private adresse åbnes. Appen har eget login og egen port; den bruger ikke Ingress eller Nabu Casa.

## Funktioner

- Udleverede distriktskort, kort i mappen og kort i kassen.
- Forkyndere, udleverings- og gennemgangshistorik, opgaver og noter.
- Midlertidige kortnumre, som senere kan få adresser, grænser og print.
- OpenStreetMap, KML/GeoJSON-import, adressevalg og markering af adresser, der skal ses bort fra.
- IB opbevaret lokalt og udskrevet på kortets bagside.
- Print af forsider, bagsider, S-13 og rapporter efter tjenesteår: 1. september–31. august.
- Valgfri Google Drive-deling af et gennemgået PNG-kort med stabil QR-kode.

[Den særskilte webdemo](demo/README.md) bruger udelukkende opdigtede data. Der er endnu ingen offentlig demoadresse. Den kan ikke åbne eller importere installationens private data.

## Data bliver på eget system

Databaser med kort, forkyndere, IB, udleveringer og noter bliver på maskinen, der kører programmet. De medfølger ikke i kildekoden eller installationspakken. Programmet har ingen udviklerkonto, analyseindsamling eller AI-forbindelse.

Kortbaggrunde, offentlige adresseopslag og valgfri Google-deling bruger eksterne tjenester. Det er derfor ikke en app, der fungerer helt uden internet. Google-funktionen uploader et udtrykkeligt godkendt kortbillede; den uploader ikke databaser, forkyndere, IB-liste eller udlånsdata. Alle med billedets offentlige link kan se og videresende det.

Lokal drift giver kontrol over data og adgang. Den er ikke i sig selv en garanti for overholdelse af persondataregler eller gældende instruktioner. [Læs de konkrete datastrømme](docs/PRIVACY.md).

## KML fra JW HUB

Har du de rette tilladelser i JW HUB, kan du ifølge mine erfaringer hente en KML-fil over menighedens samlede distrikt. Brug eksportmuligheden med din egen autoriserede adgang, og kontrollér grænsen efter import. Den virkelige fil skal blive privat.

## Åbent projekt

Det hele er vibe coded med Codex. Jeg lover ikke, at alt virker; input og fejlmeldinger er velkomne. Brug opdigtede eksempler i issues. Vedhæft aldrig rigtige databaser, forkyndernavne, IB-adresser, adgangskoder, forbindelsesfiler eller sikkerhedskopier.

Projektet er ikke udgivet, godkendt eller understøttet af jw.org, JW HUB eller Home Assistant. Koden er MIT-licenseret; de tomme formularer og medfølgende tredjepartskode har særskilte rettigheder. Se [kendte begrænsninger](docs/LIMITATIONS.md) og [tredjepartsoplysninger](distrikt/THIRD-PARTY.md).

## Udvikling

```sh
python3 -m unittest discover -s distrikt/tests -v
TZ=Europe/Copenhagen node distrikt/tests/test_frontend.cjs
python3 scripts/test_build_release.py
python3 scripts/build_release.py
```

Python er programmets kørselskrav. Node bruges til udviklingskontroller. Prøver skal bruge isolerede, opdigtede data. Dokumentation og opsætningsguides skrives på dansk først, med engelsk som ekstra valg. [Bidrag og dokumentationsregler](CONTRIBUTING.md).
