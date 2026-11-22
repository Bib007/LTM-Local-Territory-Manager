# LTM 1.12.36

Afgrænset Stable-hotfix på Stable 1.12.35. Denne udgave løser valideringen af rækkefølgen ved import af distriktskortenes historik. Andre uafsluttede Beta-funktioner er ikke med.

## Rettelse

- Historikskabelonen viser nyeste periode længst til venstre. Importen accepterer nu både ældste-først og nyeste-først, også for ældre eller manuelt udfyldte Excel-/CSV-filer.
- Perioder med samme udleveringsdato, blandet datoorden, overlappende udlån og ugyldige gennemgangsmarkeringer afvises stadig. De reelle datoer, forkyndere og gennemgange ændres ikke eller opfindes ikke.
- Alle øvrige funktioner og eksisterende registreringer fra Stable 1.12.35 bevares. Beta og Stable har fortsat adskilte installationer.

## Kontrol og udgivelse

Kandidaten kræver grønne fælles Python-, JavaScript-, browser-, sikkerheds- og pakkekontroller på det præcise main-commit. Hvert Stable-spor publiceres manuelt via **Stable release tracks**. macOS-server kræver desuden den særskilte fysiske Apple Silicon/LAN/VPN/genstartstest. Intet eksisterende release-tag eller aktiv installation overskrives.

## English

LTM 1.12.36 is a narrowly scoped Stable hotfix based on 1.12.35. Five-period history imports now accept consistently newest-first or oldest-first assignments, matching both the current workbook template and older files. Equal dates, mixed order, overlapping loans and unsupported completion flags remain invalid. All other Stable behaviour and stored data are preserved, with no unfinished Beta changes included. Each release track still requires its manual workflow and independent checks, including the separate macOS-server physical gate.
