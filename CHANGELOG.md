# Ændringsliste

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
