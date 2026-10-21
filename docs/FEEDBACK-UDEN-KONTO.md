# Feedback uden GitHub-konto eller egen e-mail

W23 · Valgt retning 21.10.2026 efter ejerens ønske: en Tally-formular med bilag. Afsenderen skal hverken logge ind på GitHub/Tally eller angive en e-mailadresse. Den eksisterende GitHub-formular bevares, indtil den nye kanal faktisk er oprettet og afprøvet.

## Klart til opsætning

Formularens navn er **LTM · Idéer og feedback**. Introduktion: “Har du en idé eller fundet en fejl? Skriv den her. Du behøver ingen konto eller e-mailadresse. Uden kontaktoplysninger kan vi ikke svare dig personligt.”

| Felt | Indhold | Krav |
| --- | --- | --- |
| Hvad drejer det sig om? | Fejl, ny funktion, forbedring, design eller andet | Obligatorisk valg |
| Kort overskrift | Hvad ønsker du ændret? | Obligatorisk tekst |
| Din idé eller fejlbeskrivelse | Hvad sker der, og hvad havde du forventet? | Obligatorisk tekst |
| Sådan kan fejlen gentages | Trin med fiktive eksempler | Valgfri tekst |
| LTM-version | Kan kopieres fra appens versionsnummer | Valgfri tekst; ingen automatisk indsamling |
| Billeder eller tegninger | Op til tre PNG/JPEG/WebP, højst 10 MB pr. fil | Valgfrit; ingen database-, backup- eller nøglefiler |
| Kontrollér indholdet | “Jeg har kun brugt fiktive eksempler og kontrolleret, at tekst og bilag ikke indeholder IB, rigtige distriktskort, navne, adresser, adgangskoder eller andre personoplysninger.” | Obligatorisk bekræftelse |

Ingen felter til e-mail, navn, menighed eller telefon. Ingen automatisk vedhæftning, skærmoptagelse, driftslog eller udtræk af lokale data. Ingen automatisk kopiering af indsendelser eller filadresser til offentlige GitHub-issues.

Takside: “Tak! Din feedback er gemt. Vi gennemgår forslagene, men kan ikke svare personligt uden kontaktoplysninger.” Vis først dette efter en faktisk vellykket indsendelse.

## Ejerskab og aktivering

Formularen skal oprettes i projektejerens Tally-arbejdsrum, så ejeren modtager og administrerer svar og bilag dér. Afsenderne behøver ingen konto. Den konto, som ejer formularen, skal være tilgængelig ved opsætning; der er endnu ingen verificeret formular eller forbindelse. Tally blev søgt i pluginoversigten 21.10.2026 uden tilgængeligt resultat. En opdigtet formularadresse må ikke sættes i appen.

Når ejeren har forbindelse til arbejdsrummet: Opret først en kladde med ovenstående felter og begrænsninger. Kontrollér indstillinger og modtager, publicér formularen, og prøv den uden login med fiktiv tekst og et fiktivt billede. Bekræft, at svar og fil faktisk kan læses i ejerens arbejdsrum, at taksiden først vises ved succes, og at fil-/størrelsesgrænser fungerer. Fjern den fiktive prøve efter kontrollen. Først da kan appens menupunkt ændres til den verificerede offentlige formularadresse i en ny beta.

Appen indeholder alene det offentlige formularlink. API-nøgler eller adgang til formens svar må aldrig følge med programpakken eller GitHub. Tallys navn og behandling af manuelt indsendt tekst/bilag skal fremgå, før brugeren åbner formularen. Undlad at love anonymitet over for selve tjenesteudbyderen: “uden konto eller e-mail” beskriver afsenderens formularfelter og login, ikke fravær af tekniske netværksoplysninger.

W23 er fortsat åben, indtil ejerskab, formular og faktisk modtagelse er kontrolleret.

## Kontrollerede primære kilder

Læst 21.10.2026:

- [Tally: File uploads](https://tally.so/help/file-uploads): bilag uden respondentkonto, gratis op til 10 MB pr. fil, mulighed for antal-/filtypegrænser.
- [Tally: API](https://tally.so/help/api): formoprettelse kræver autoriseret adgang til et arbejdsrum.
- [Tally: MCP](https://tally.so/help/mcp): oprettelse og vedligeholdelse via en tilsluttet konto.
- [Tally: Self email notifications](https://tally.so/help/self-email-notifications): eventuelle ejerbeskeder konfigureres hos formularens ejer. Afsenderen behøver ikke angive e-mail. Ingen mailbesked er aktiveret her.
- [GitHub: Creating an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue) og [Configuring notifications](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications): GitHubs eksisterende issue-/svaradgang er knyttet til en GitHub-konto; notifications-reply-adresser er ikke en konto-fri indsendelseskanal, der må indbygges i appen.
