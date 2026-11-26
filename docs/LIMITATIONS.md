# Kendte begrænsninger

[English](LIMITATIONS.en.md)

- Automatisk forslag til distriktsgrænser og kortinddeling er sat på pause fra beta.61 (W81). Koden er bevaret; brug den manuelle korteditor. Se [arkivet](AUTOMATISK-INDDELING.md).
- Dansk er standardsprog. Den videre engelske oversættelse følger [sprogoversigten](TRANSLATION.md).
- Automatiske prøver bruger opdigtede data. Egen Google-publicering, fysisk printtilpasning og den konkrete HA-/netværksinstallation kræver kontrol på stedet.
- Adresseimport er rettet mod Danmark. Fra beta.8 bruges DAR GraphQL med egen gemte nøgle; uden nøgle bruges den hidtidige kilde. DAR REST er varslet udfaset 15. januar 2027. Egen Datafordeler-/HA-prøve og Adressevælgerens særskilte adgangsændring står fortsat åbne. Gemte lokale data forbliver tilgængelige.
- OSM-kortfliser kræver internet og overholdelse af tjenestens vilkår. Der medfølger ikke en offline flisepakke eller ubegrænset massehentning/-eksport.
- De tomme formularer er adskilt fra kodens MIT-licens og angiver ikke godkendelse fra udgiveren. PDF-generatoren har begrænset skrifttypestøtte; browserprint understøtter flere Unicode-tegn.
- HA-backup udelader appdata. Brug appens private backup.
- ZIP-opgraderingsprøven springes eksplicit over, hvis den tidligere private ZIP ikke findes.
- Pages kan vise webdemoens statiske filer, men kører ikke den private Python/SQLite-app. [Demoudgivelse](DEMO-HOSTING.md).
