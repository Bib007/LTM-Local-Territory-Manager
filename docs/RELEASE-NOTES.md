# LTM 1.12.36

Denne Stable-kandidat er den direkte promovering af `1.12.36-beta.1`. Udgaven indfører fælles, automatisk versionskontrol for fremtidige Beta- og Stable-udgivelser. De brugerrettede funktioner, rettigheder og dataskema er de samme som i Stable 1.12.35, som allerede indeholder alle færdige Beta.36–37-ændringer (interne kortnavne, Menighedstilpasning og IB-forbedringer).

## Nyt

- **Én fælles version:** Beta `X.Y.Z-beta.1`, `-beta.2` osv. får samme grundversion som den senere Stable `X.Y.Z`. Fejlrettelser øger PATCH, bagudkompatible funktioner øger MINOR, og brydende ændringer øger MAJOR.
- **Automatiske udgivelses-gates:** GitHub kontrollerer lovlig versionsrækkefølge, ubeskadigede og uforanderlige tags, at næste Beta indeholder den seneste Stable, og at Stable-programkoden er identisk med seneste udgivne Beta bortset fra versionsstrengen.
- **Uændrede datakanaler:** Beta og Stable har stadig separate mapper, login, HA-appnavn og porte. Eksisterende brugerdata berøres ikke.
- **Særskilt publicering:** Home Assistant, Mac-app og Windows-app/-server publiceres fortsat manuelt og hver for sig, med tests på det præcise commit. macOS-serverens fysiske Apple Silicon/LAN/VPN/genstartskrav er uændret.

Denne udgave medfører ingen funktions- eller datamigrering. Den tidligere Stable 1.12.35 og alle historiske Beta-tags overskrives ikke. Åbne PR'er og andre ikke-frigivne funktioner følger ikke med.

Se [versionspolitikken](VERSIONERING.md) for konkrete eksempler og den obligatoriske udgivelsesproces.

## English

This Stable candidate promotes the tested source from `1.12.36-beta.1` to `1.12.36` without changing user-facing behaviour or stored data compared with Stable 1.12.35. Versioning is now shared across channels: `X.Y.Z-beta.N` promotes to `X.Y.Z`; fixes bump PATCH, compatible features bump MINOR, and breaking changes bump MAJOR. Each release is automatically gated against reused Git tags, skipped Beta numbers, missing Stable ancestry and mismatched Beta/Stable application code. Existing immutable releases and independent Stable-track controls are preserved; the physical macOS-server testing gate remains mandatory.
