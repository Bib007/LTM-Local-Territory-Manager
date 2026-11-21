# LTM 1.12.36-beta.1

Dette er den **første Beta i det fælles versionssystem**. Fra nu af deler Beta og Stable de første tre tal: `1.12.36-beta.1` bliver `1.12.36`, når den afprøvede kode promoveres til Stable. Ældre Beta-tags, herunder `1.12.19-beta.37`, er historik og ændres ikke.

## Hvad ændres?

- Nye releases kontrolleres automatisk mod seneste Stable, tidligere Beta-tags og den samme versionsstamme.
- Nummerfølgen bliver fortløbende (`-beta.1`, `-beta.2` osv.). Fejlrettelser hæver PATCH, nye kompatible funktioner hæver MINOR, og brydende ændringer hæver MAJOR.
- En ny Stable skal svare til seneste frigivne Beta-kode, med undtagelse af selve versionsstrengen. Ændringer på Stable skal med i `develop` før næste Beta.
- Gentagne `develop`-commits med et allerede publiceret betanummer udløser ikke en ny udgivelse; der kræves et nyt nummer og grønne kontroller. Gamle Git-tags/ZIP-filer må ikke overskrives.
- Denne Beta ændrer **ikke** appens brugerrettede funktioner eller dataskema sammenlignet med Stable 1.12.35, der allerede indeholder interne kortnavne, Menighedstilpasning, sikker samlet IB-adressegodkendelse og de rettede IB-tal.

## Afprøvning

1. Kontrollér i appen, at versionsnummeret er `1.12.36-beta.1`.
2. Kontrollér at Beta bruger eget navn, login, port **8788** og separat datamappe `Distrikt-beta`; Stable fortsætter uændret på port **8787**.
3. Prøv kortnavn, Menighedstilpasning og IB-funktionerne med opdigtede data, og sammenlign den almindelige brugerflade med Stable 1.12.35.
4. Kontrollér på GitHub at versionen har et nyt prerelease-tag og uforanderlige HA/program-ZIP-filer med SHA-256-kontrolsummer.

Læs [versionsreglerne](VERSIONERING.md) for hvordan kommende Beta- og Stable-udgivelser vælges. Uafsluttede PR'er, blandt andet DAR-preview-isoleringen #134, er stadig **ikke inkluderet**.

## English

The first Beta using one shared version train. `1.12.36-beta.1` will become Stable `1.12.36` with the same tested source. Versions are now validated for correct increments, unique immutable Git tags, latest Stable ancestry and matching Beta/Stable program code. This migration Beta adds no user-facing features or data migrations beyond Stable 1.12.35; old Beta tags remain intact. Test with fictional records and confirm Beta's isolated data, port 8788 and login.
