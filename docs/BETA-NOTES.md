# LTM 1.12.0-beta.19

## Nyt siden beta.18

Fejl fra kort, udlån, IB, adresser, opsætning, administration og backup kan nu læses på dansk/engelsk. Parameteriserede beskeder bevarer brugerens præcise navne og talgrænser. Serverens oprindelige danske fejltekst bevares til diagnostik; ukendte beskeder ændres ikke eller gættes oversat.

Dato- og IB-linjefejl samt backupkontrol følger samme håndtering. Sprogskift opdaterer beskeden uden at erstatte felterne. Afviste ændringer udløser ikke beskeden om usikker gemning. Tidsgrænsen for JSON-læsning dækker også et svar, der stopper efter HTTP-headerne.

## Prøv især

1. Opdater Distrikt Beta, adskilt fra stabil, og brug opdigtede prøvedata.
2. Vælg engelsk og prøv at oprette et allerede brugt kortnummer eller område. Kontrollér fejlbeskeden og at felterne bevares. Skift til dansk og tilbage; brugerens eget navn og nummer skal være uændret.
3. I avanceret opsætning: prøv et ugyldigt besøgsantal. Kontrollér beskedens præcise grænser, og ret værdien. En afvist forhåndsvisning må ikke oprette noget.
4. Prøv en opdigtet IB-import med forkert dato. Kontrollér linjefejlen på begge sprog, og at import fortsat er spærret, indtil fejlen er rettet.
5. Kontrollér en ufølsom ugyldig backup lokalt. Beskeden må ikke påstå, at en import blev udført, og ingen eksisterende registreringer må ændres.

Udviklingsprøver bruger kun opdigtede data. Python kontrollerer det dækkede fejlkatalog mod programkoden og prøver rigtige HTTP-afvisninger uden ændret revision. UI-prøver kontrollerer rå brugerparametre, specialtegn, ukendte metadata og fallback. Offline Chromium dækker fejl, sprogskift og bevarede felter ved fire skærmbredder.

Fast køreplan: 50 % (5/10). Punkt 6 fortsætter med afsluttende kontrol af særskilte opsætnings-, kortimport- og delingsskrivninger, især en gennemført skrivning med fejlet efterfølgende læsning. Ønskelisten venter; egen HA/telefon og fysisk print er særskilte ejertrin.
