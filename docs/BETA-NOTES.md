# LTM 1.12.19-beta.2 · IB-kort, mapper, sortering og vejledende kortantal

Denne beta samler forbedringerne fra PR #33–36. Stable 1.12.19 er uændret.

## Dette er nyt

- **IB-bagsider:** Kortene bliver fortsat trykt i det originale format 94 × 146 mm. Pladsen udnyttes bedre med automatisk sideopdeling og eventuelt to spalter, så intet klippes.
- **Læg specifikt kort i mappen:** Søg efter et eksisterende kort fra Daglig brug, vælg det og bekræft. Ingen nye kortnumre eller ændringer af udleveringshistorikken.
- **Senest gennemgået:** Sortér distriktskort efter længst tid siden gennemgang under Distriktskort. Kort uden dato kommer først, og nulstilling påvirker ikke andre filtre.
- **Vejledende antal pr. forkynder:** Fire redigerbare rolletal under Indstillinger (menighedsforkynder 1, pioner 2, assistent 2, gruppetilsynsmand 3). Visning af aktuelt / vejledende i lister og ved udlevering. **Aldrig en blokering.**

## Afprøv gerne

1. Prøv IB-kort med få, mellemstore og mange fiktive adresser på både forskåret kort og A4-prøveark, også som PDF.
2. Læg et eksisterende kort i mappen via søgning. Kontrollér at udleverede og allerede placerede kort ikke kan flyttes på denne måde.
3. Sortér Distriktskort efter gammel/ukendt gennemgang, vælg område og status, og nulstil kun sorteringen.
4. Justér vejledende antal for hver rolle; afprøv kombinerede roller, udlevering og aflevering og kontrollér at ekstra kort stadig kan udleveres.

Betaen anvender i Home Assistant **port 8788, egen datamappe og eget login**. Den almindelige Beta-opdatering bevarer Beta-prøvedata, men lav altid en privat sikkerhedskopi først. Stable påvirkes ikke.

Brug kun opdigtede kort og en særskilt testforbindelse til Google Drive. Betaens programmæssige pakker indeholder ingen brugerdata.

Se [betavejledningen](BETA.md) for installation og [Stable-noterne](RELEASE-NOTES.md) for den stabile udgave.
