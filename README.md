<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/logo-dark.svg">
  <img alt="Local Territory Manager – JW" src="assets/brand/logo-light.svg" width="640">
</picture>

# Local Territory Manager – JW

**Distriktsadministration på din egen computer eller Home Assistant.** Et uofficielt værktøj til Jehovas Vidner, vibe coded med **OpenAI Codex** og udviklet med udgangspunkt i arbejdet ved distriktsdisken.

[English](README.en.md) · [Installation](docs/INSTALL.md) · [Kom i gang](docs/FIRST-STEPS.md) · [Privatliv](docs/PRIVACY.md) · [Udviklingsplan](ROADMAP.md) · [Manuelle punkter](Dette-skal-hjaelpes-manuelt.md)

## Ny opstart og kortimport på develop

Første start spørger til enkel udlevering eller kortfunktion, KML, eksisterende kortfordeling og IB. Svarene giver en personlig plan og en valgfri rundtur i appen. Guiden kan åbnes igen under Indstillinger.

Har du allerede fordelt adresser på kort og områder, kan du hente Excel-skabelonen i **Indstillinger → Avanceret → Importér eksisterende distriktskort**. XLSX og CSV kontrolleres lokalt; alle fejl skal rettes før samlet oprettelse. [Kortimport](docs/KORTIMPORT.md) og [nye ønsker](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/OENSKELISTE.md).

## Kom i gang

**Udviklingsudgave: 1.12.0-beta.9.** Denne gren klargør næste version. Brug [main](https://github.com/Bib007/LTM-Local-Territory-Manager/tree/main) til stabil installation. Den almindelige HA-knap nedenfor følger main. [Køreplan: 20 %](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/KOREPLAN.md).

[![Tilføj LTM til Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FBib007%2FLTM-Local-Territory-Manager)

**1.11.0** er det stabile udgangspunkt. Den videre udvikling følger [udviklingsplanen](ROADMAP.md).

- **Home Assistant OS:** Brug knappen ovenfor, og vælg **Distrikt → Installer** i HA. Senere programopdateringer hentes direkte i HA. [Dansk installationsguide](docs/INSTALL.md).
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

[Åbn webdemoen direkte](https://bib007.github.io/LTM-Local-Territory-Manager/) uden installation eller GitHub-login. Den bruger udelukkende opdigtede data og kan ikke åbne eller importere installationens private data. [Om demoen](demo/README.md).

## Data bliver på eget system

Databaser med kort, forkyndere, IB, udleveringer og noter bliver på maskinen, der kører programmet. De medfølger ikke i kildekoden eller installationspakken. Programmet har ingen udviklerkonto, analyseindsamling eller AI-forbindelse.

Kortbaggrunde, offentlige adresseopslag og valgfri Google-deling bruger eksterne tjenester. Det er derfor ikke en app, der fungerer helt uden internet. Google-funktionen uploader et udtrykkeligt godkendt kortbillede; den uploader ikke databaser, forkyndere, IB-liste eller udlånsdata. Alle med billedets offentlige link kan se og videresende det.

Lokal drift giver kontrol over data og adgang. Den er ikke i sig selv en garanti for overholdelse af persondataregler eller gældende instruktioner. [Læs de konkrete datastrømme](docs/PRIVACY.md).

## KML fra JW HUB

Har du de rette tilladelser i JW HUB, kan du ifølge mine erfaringer hente en KML-fil over menighedens samlede distrikt. Brug eksportmuligheden med din egen autoriserede adgang, og kontrollér grænsen efter import. Den virkelige fil skal blive privat.

## Idéer og feedback

Har du et forslag eller en kommentar til LTM? Åbn [Idéer og feedback på GitHub](https://github.com/Bib007/LTM-Local-Territory-Manager/issues/new?template=idea.yml). Forslag, billeder og kommentarer håndteres direkte af GitHub og gemmes ikke i LTM. GitHub kræver login for at oprette et issue. Alt indsendt er offentligt: brug kun opdigtede eller anonymiserede eksempler.

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
