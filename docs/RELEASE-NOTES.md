# LTM 1.12.1 · Udlever kort uden unødige afbrydelser

Du kan igen arbejde videre med kort og udleveringer uden beskeden om ændringer fra en anden fane eller enhed.

## Det er rettet

- Kort kan udleveres, afleveres og redigeres, selv om Google-forbindelsen ændrer status i baggrunden.
- Den generelle kontrol, der krævede genindlæsning efter ændringer andre steder, er fjernet indtil videre.
- Samtidig redigering bliver taget op igen sammen med brugerprofiler. Hvis flere redigerer samme oplysninger nu, bliver den senest gemte ændring stående.

Kontrollen af kort, datoer og allerede udleverede kort er bevaret. Problemer med Google vises stadig under deling; billeddeling og almindelig kortadministration er fortsat adskilte arbejdsgange.

## Sådan opdaterer du

**Home Assistant:** Hent en privat sikkerhedskopi i LTM, og opdatér **Distrikt** til **1.12.1**. Åbn appen på ny bagefter. Hvis opdateringen ikke vises med det samme, vælg **Kontrollér for opdateringer** i appbutikken.

**Mac og Windows:** Hent **LTM-v1.12.1.zip**, og følg [opdateringsvejledningen](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.md).

Dine gemte kort og din historik bevares ved en almindelig opdatering af samme installation.

[Prøv demoen](https://bib007.github.io/LTM-Local-Territory-Manager/) · [Kom i gang](https://github.com/Bib007/LTM-Local-Territory-Manager) · [Idéer og feedback](https://tally.so/r/KpY0ZV)
