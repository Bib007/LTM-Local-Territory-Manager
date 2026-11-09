# LTM 1.12.20 · Samlet Stable efter beta.4

Den gennemtestede Beta 1.12.19-beta.4 er nu samlet i Stable 1.12.20. Eksisterende Stable-installationer kan opdateres uden at skifte til betakanalen. Luk programmet og tag en privat backup før opdatering.

## Nyheder og forbedringer

- **Personlige opgaver på forsiden.** Når du er logget ind med opgaveadgang, viser velkomsten antallet af egne, aktuelle, åbne opgaver samt knappen **Se mine opgaver**. Andre brugeres, afsluttede og ignorerede opgaver tæller ikke med. Antallet opdateres automatisk ved ændringer fra andre konti.
- **Vejledende distriktskort pr. forkynder.** Indstil anbefalede antal for forkyndere, pionerer, gruppeassistenter og tilsynsmænd. Tallene gemmes korrekt også med brugerprofiler og vises i forkynderoversigten. Flere roller bruger det højeste forslag; antal begrænser aldrig udlevering.
- **Hurtigere daglig brug.** Find og læg et allerede eksisterende distriktskort i mappen uden at oprette et nyt. Kortidentitet, udleveringer og historik bevares.
- **Bedre overblik.** Sortér distriktskort efter længst tid siden gennemgang, også når sidste dato er ukendt, og bevar dine øvrige filtre.
- **Korrekt IB-print.** IB-bagsiden udnytter det originale 94 × 146 mm kortformat bedre, og ekstra kortsider oprettes kun ved behov. A4 er stadig kontrolark, ikke et forstørret distriktskort.
- **Kompatibilitet og datasikkerhed.** Ældre opgaveposter bevares i almindelige lister; opgavetallet viser kun egne data og kræver de rette læserettigheder.

Alle automatiske Python-, JavaScript-, browser-, sikkerheds- og platformskontroller for den tilsvarende Beta-kode blev bestået inden Stable-forberedelsen. Der er anvendt fiktive konti og testdata.

## Installation og kanaler

**Home Assistant Stable:** Brug den almindelige repositoryadresse uden `#beta`. Stable beholder port 8787 og sin eksisterende datamappe. Beta er en separat installation med port 8788 og eget login og data; dens data overføres ikke automatisk til Stable.

**Mac og Windows:** Brug de særskilte, kontrollerede Stable-releasefiler for den relevante platform. Den native Mac-server med LAN/VPN kræver fortsat sin særskilte fysiske godkendelse. Installationsfiler er usignerede og kan kræve første-gangsgodkendelse. Luk programmet før en opdatering.

Ændringerne fra beta.2–beta.4 er samlet i [changeloggen](CHANGELOG.md). De tidligere betaudgivelser forbliver tilgængelige som prereleases.
