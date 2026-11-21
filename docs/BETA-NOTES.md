# LTM 1.13.0-beta.2

Denne Beta forbedrer **KTM-rapporten** under Rapporter og historik. Beta og Stable har fortsat adskilte data, port og login. Stable ændres ikke.

## Det nye i rapporten

- **Besøgspunkter på aktuelle distriktskort:** Summen kommer fra de registrerede vejlinjer på de aktuelle kort, inklusive manuelle kort. Adresser, som kun findes i DAR eller inden for den samlede grænse uden at være på et kort, tæller ikke. Ukendte besøgstal markeres, så tallet ikke bliver misvisende.
- **Én IB-total:** Alle aktive IB indgår, både med og uden DAR-adressematch. Der vises ikke længere et ekstra felt for geografisk kortlagte IB.
- **Gennemgået / ikke gennemgået:** Én cirkelformet dækningsoversigt viser andelen af aktuelle kort, der har en registreret gennemgang i den valgte periode. Antal gennemgange tæller også gentagelser.
- **Tydelig opfølgningsliste:** Den detaljerede rapport og PDF angiver hvert aktuelt kort, der ikke er registreret gennemgået i perioden, med kortnummer, navn, område og seneste kendte gennemgangsdato.
- Fjernet fra KTM-hovedoversigten: unødvendig opdeling af kort i hjemme/udleveret samt ekstra geografisk IB-tal.

## Afgrænsning

Kalenderår, tjenesteår og rullende 12 måneder følger de eksisterende periodevalg. Aktuelle kort tælles én gang; arkiverede kort er ikke med i mangellisten, men deres historiske gennemgange kan stadig indgå i antallet af afslutninger. Manglende gennemgangsdato betyder ikke nødvendigvis, at distriktet aldrig er blevet gennemgået.

Rapportroller uden kortlæserettighed ser kun summer, ikke individuelle kort. IB-total kræver IB-læserettighed. Ingen ændringer i data eller den originale S-13-PDF.

## Test af beta

1. Kontrollér version 1.13.0-beta.2 på den separate beta-installation, port 8788.
2. Åbn Rapporter og historik og vælg Kalenderår, Tjenesteår og Seneste 12 måneder på skift. Kontrollér dækningsring, antal gennemgange og listen over manglende distriktskort.
3. Kontrollér, at manuelle korts besøgspunkter og alle aktive IB indgår, men at adresser uden et kort ikke gør.
4. Udskriv én periode og derefter alle tre. Kontrollér kortlister, områdebetegnelser, diagrammer og at den originale S-13 fortsat findes ved tjenesteår.
5. Kontrollér, at oversigtsroller ikke kan se kortnavne eller IB uden tilladelse.

## English

KTM reporting now uses visit points actually listed on current territory cards and a single authorized total of all active do-not-call records. A coverage donut and an explicit list of cards not completed in each selected reporting period appear on screen and in PDF. Counts-only roles receive no card details. Data and original S-13 remain unchanged.
