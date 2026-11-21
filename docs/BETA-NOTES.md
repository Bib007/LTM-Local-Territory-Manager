# LTM 1.12.19-beta.37

Denne Beta samler interne distriktskortnavne og de seneste Stable-rettelser, som allerede findes i Beta-koden. Stable ændres ikke.

- **Internt distriktskortnavn:** Tilføj et valgfrit navn (højst 160 tegn) på kortets redigeringsside. Det officielle navn og det offentlige distriktskortnummer bevares.
- **Administration og søgning:** Find kort efter både offentligt og internt navn samt numre. Vis det interne navn særskilt i distriktsoversigt, kortoplysninger og kortvælgere, også ved lange navne.
- **Kompatibilitet:** Tidligere kort virker uden feltet. Gemning, rettigheder, import (valgfri `internt_navn`-kolonne), læsbar eksport og backup bevarer oplysningerne. Udlån, IB og historik er stadig knyttet til det samme kort-ID.
- **Print og deling:** Interne navne må ikke fremgå af S-12/S-13 eller offentligt delte kort.
- **Stable-rettelser med i Beta:** Gem/vejliste-dialogen genåbnes ikke under baggrundsgemning. Fokus, tekstmarkør og scrollposition bevares ved autosave. Forældede DAR-fejl ryddes. IB-læsearkiv bruger det normale, opmålte IB-printlayout, og eksportknappen står ved siden af Sikkerhedskopi.
- **Ikke inkluderet:** DAR-preview-isoleringen fra den åbne PR #134 og øvrige uafsluttede PR'er.

## English

This Beta includes optional local-only territory names and the latest Stable editor and readable-archive fixes already present in the Beta code.

- Set an optional internal name per territory (up to 160 characters) without replacing its official name or number.
- Search and identify cards by either name or number in administrative lists and card pickers, including responsive layouts.
- Preserve old cards, record IDs, loans, do-not-call data, history, imports, exports and backups. The optional import column is `internt_navn`.
- S-12/S-13 and public shares continue using official labels only.
- Includes the Stable save-dialog, focus/scroll, stale-DAR-message and measured IB readable-archive corrections.
- Excludes pending DAR-preview isolation PR #134 and other unfinished pull requests.

## Afprøvning

1. Opret et fiktivt kort med offentligt navn og langt internt navn. Rediger, ryd og gem feltet; prøv på både mobil og computer.
2. Søg efter begge navne og numre, og vælg kortet ved udlevering, mappevalg og kortgrænser.
3. Importér en CSV med `internt_navn` og kontrollér læsbar eksport og en backup/gendannelse på fiktive data.
4. Kontrollér, at det interne navn **ikke** findes på udskrevet S-12/S-13 eller i offentlige kortbilleder/PDF'er.
5. Prøv at gemme en vejliste under indtastning. Kontrollér, at dialog, fokus, tekstmarkør og scroll ikke hopper, og at gamle DAR-fejl ikke bliver hængende.
6. Eksportér et læsearkiv med flere IB-bagsider og eventuelle fortsættelsessider. Sammenlign med almindeligt IB-print og kontrollér knappen ved Sikkerhedskopi.

Beta bruger fortsat særskilt datamappe, login og port 8788. Prøv altid med opdigtede data, og tag en backup før opdatering.
