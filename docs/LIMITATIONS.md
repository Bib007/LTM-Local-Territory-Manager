# Kendte begrænsninger

[English](LIMITATIONS.en.md)

- Dansk er standardsprog. Den videre engelske oversættelse følger [sprogoversigten](TRANSLATION.md).
- Automatiske prøver bruger opdigtede data. Egen Google-publicering, fysisk printtilpasning og den konkrete HA-/netværksinstallation kræver kontrol på stedet.
- Fra beta.11 kan lokale vejforløb med knæk og kurver indgå i forslaget. Samme-navn-forbindelser kræver præcist fælles endepunkt uden forgrening. Højst 512 punkter pr. forløb og 256 kandidater udvælges; op til 32 forløb prøves pr. deling med grænser for geometrisk arbejde. Tvetydige skæringer, løkker og mere end to grænsekrydsninger springes over. Naturlige skel er endnu ikke en særskilt kilde. Se [inddelingsvejledningen](AUTOMATISK-INDDELING.md).
- Automatisk foreslåede distrikter er geografiske forslag, ikke gangruter eller matrikelgrænser. Gennemgå adgang, veje, adskilte dele og kortenes adressevalg før oprettelse.
- Adresseimport er rettet mod Danmark. Fra beta.8 bruges DAR GraphQL med egen gemte nøgle; uden nøgle bruges den hidtidige kilde. DAR REST er varslet udfaset 15. januar 2027. Egen Datafordeler-/HA-prøve og Adressevælgerens særskilte adgangsændring står fortsat åbne. Gemte lokale data forbliver tilgængelige.
- OSM-kortfliser kræver internet og overholdelse af tjenestens vilkår. Der medfølger ikke en offline flisepakke eller ubegrænset massehentning/-eksport.
- De tomme formularer er adskilt fra kodens MIT-licens og angiver ikke godkendelse fra udgiveren. PDF-generatoren har begrænset skrifttypestøtte; browserprint understøtter flere Unicode-tegn.
- HA-backup udelader appdata. Brug appens private backup.
- ZIP-opgraderingsprøven springes eksplicit over, hvis den tidligere private ZIP ikke findes.
- Pages kan vise webdemoens statiske filer, men kører ikke den private Python/SQLite-app. [Demoudgivelse](DEMO-HOSTING.md).
