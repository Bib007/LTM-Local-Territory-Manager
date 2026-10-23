# Bidrag til LTM

[English](../docs/CONTRIBUTING.en.md)

Har du en idé eller feedback? Brug [feedbackformularen hos Tally](https://tally.so/r/KpY0ZV) uden konto eller e-mail. Indsendt tekst og billeder gemmes hos Tally; brug kun fiktive eksempler uden IB, rigtige distriktskort eller personoplysninger. Du kan også oprette eller kommentere [GitHub-issues](https://github.com/Bib007/LTM-Local-Territory-Manager/issues) med GitHub-login. Udviklere kan indsende kodeændringer som pull requests.

## Dansk først

README, almindelige manualer, installations- og opsætningsguides skrives på **dansk som hovedsprog**. Den almindelige filsti, fx `README.md` eller `docs/INSTALL.md`, skal vise den danske udgave. Engelsk er et ekstra valg i den tilsvarende `.en.md`-fil, med en synlig sproggenvej i begge udgaver. Efter ejerens ønske er den gamle danske dublet fjernet; `README.md` er den danske indgang.

Opdatér begge sprog ved ændringer i arbejdsgange. Filnavne, kodeeksempler, formularnavne og menuer skal svare til den faktiske version. Hvis noget endnu ikke er udgivet, skal det fremgå. Standardguiden må ikke give indtryk af, at en udviklingsbranch allerede kan installeres.

Appens standardsprog er dansk. Oversæt kun fast betjeningstekst; brugerens navne, noter, indtastede værdier og opbevarede protokolværdier må ikke oversættes. Officielle betegnelser skal kontrolleres i offentlige, officielle kilder, før de præsenteres som officielle.

## Private oplysninger

Vedhæft ikke rigtige databaser, forkyndernavne, IB-adresser, billeder med personoplysninger, adgangskoder eller Google-forbindelsesfiler. Logfiler må ikke indeholde private payloads. Automatiske prøver skal bruge midlertidige mapper og opdigtede registreringer og må aldrig åbne programmets normale datamappe.

Offentlig kildekode og programpakker må kun indeholde gennemgåede programfiler, tomme formularer og tydeligt opdigtede prøve-/demodata. En ny offentlig filsamling må ikke arve den private udviklingshistorik.

## Ændringer og kontrol

Bevar de separate SQLite-filer, ukendte felter, importforhåndsvisninger, konkrete godkendelseskontroller og udtrykkelige bekræftelser ved sletning/erstatning. En almindelig programopdatering må ikke erstatte eksisterende databaser. Undgå nye afhængigheder, hvis standardbiblioteket og de medfølgende filer kan løse opgaven.

Kør relevante Python- og JavaScript-kontroller. Ændringer i lagring, geometri, adgang eller offentlig eksport kræver meningsfuld kontrol. Ved ændringer i betjeningen gennemgås både bred og smal skærm. Oplys, hvad der ikke er kontrolleret på fysisk udstyr.

Bed ikke om begrænsede dokumenter, andres login eller adgang til andres JW HUB-konto.

Generel afvisning af almindelige ændringer på grund af andre faner/enheder er efter ejerens valg sat på pause i 1.12.1. Afklar samtidig redigering igen sammen med brugerprofiler; genindfør ikke kontrollen som en rutinerettelse.
