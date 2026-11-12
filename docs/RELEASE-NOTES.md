# LTM 1.12.21 · Beta 1.12.19-beta.6 bliver til Stable

Denne udgave samler de 12 forbedringer fra Beta 1.12.19-beta.5 og rettelsen i beta.6. Den bevarer eksisterende Stable-installation og brugerdata på deres sædvanlige placering.

## Nyheder

- **Forkyndere og daglig brug:** korrekte optællinger efter menighedsgrupper, bekræftet sletning, massehandling til mappen og særskilte interne/offentlige distriktsnumre.
- **Historik og rapportering:** tydeligere gennemgange, KTM-vejledning, valgbare rapportperioder og tidslinje for seneste KTM-besøg.
- **Kort og formularer:** mobilvisning af S-13, robust OpenStreetMap-fallback, valgfri egen tekst ved DAR-vejlinjer, S-12-justering og forslag til opdeling af distrikter.
- **Opfølgning og Google Drive:** reversibel ignorering af enkelte opfølgninger samt arbejdsstatus, dobbeltklikværn og genprøvning ved upload.

## Opdatering og sikkerhed

Tag en **privat backup af distriktsdata** og, hvis profiler er aktiveret, en separat konto-backup før opdatering. Installer ny Stable på samme kanal; behold eksisterende data og login. Beta er fortsat separat og bruger sin egen datamappe og Home Assistant-port 8788 i stedet for Stable-port 8787. Brug kun fiktive data til nye prøveforløb.

Udgivelsesprocessen kræver grønne tests på den **endelige Stable-commit** og separat kontrolleret publicering pr. platform. macOS-server må ikke udgives, før den særskilte fysiske LAN/VPN/genstartstest er godkendt. Stable-assets og gamle betaudgivelser må ikke overskrives.

Se [den danske ændringslog](CHANGELOG.md), [den engelske ændringslog](CHANGELOG.en.md) og [betavejledningen](BETA.md).
