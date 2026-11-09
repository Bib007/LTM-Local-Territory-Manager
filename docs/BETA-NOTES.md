# LTM 1.12.19-beta.3 · Rettelse af vejledende kortantal

Denne beta retter en fejl i den forrige beta (`1.12.19-beta.2`). Stable 1.12.19 er uændret.

## Rettet

- **Gem indstillinger fungerer nu for vejledende kortantal pr. forkynder.** Ændringer til de fire roller bliver vist efter gemning, når appen bruger brugerprofiler, og de samme værdier vises igen efter genindlæsning eller nyt login.
- **Samme vejledende antal for hele holdet.** Brugere med adgang til forkynderoversigten ser de gemte anbefalinger uden at få ret til at ændre indstillingerne.
- **Ingen udleveringsgrænse.** Anbefalingerne er stadig kun vejledende. En forkynder kan få flere distriktskort end det angivne antal.

De øvrige forbedringer fra 1.12.19-beta.2 er fortsat med: mere plads på IB-bagsider, søgning efter et eksisterende kort til mappen og sortering efter længst tid siden gennemgang.

## Afprøv med fiktive data

1. Gå til **Indstillinger → Menighed og mappe**, og ændr alle fire vejledende antal (f.eks. til 0, 4, 1 og 7).
2. Tryk **Gem indstillinger**. Kontrollér, at tallene forbliver uændrede efter gemning, sideopdatering og genåbning.
3. Gå til **Forkyndere** og prøv at udlevere og aflevere et kort. Kontrollér visningen *aktuelt / vejledende*, også når antal overskrides.

**Home Assistant Beta** beholder eget login, egen datamappe og port 8788. Tag en privat backup, før du opdaterer. Stable berøres ikke, og pakken indeholder ingen brugerdata.

Læs [betavejledningen](BETA.md) ved installation og [changeloggen](CHANGELOG.md) for ændringerne.
