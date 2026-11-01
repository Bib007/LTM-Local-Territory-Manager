# Datoer på det godkendte onlinekort

Onlinekortet viser **Senest gennemgået** og **Udleveret d.** Den første dato er kortets seneste registrerede gennemgang. En aflevering, som registreres uden gennemgang, ændrer den ikke. Udleveringsdatoen kommer fra det aktuelle aktive udlån; den ryddes ved aflevering og skifter ved en ny udlevering. Der vises ingen kortholdernavne. Manglende gennemgang eller intet aktivt udlån vises med en streg.

## Godkend første gang

Vælg **Opdater Google Drive-upload** ved kortet. Det nye preview viser det præcise billede, som sendes. Godkend både billedet og automatisk opdatering af de to datoer. Eksisterende delinger opgraderes ikke automatisk fra et ældre layout; fil og QR-link kan bevares, mens et nyt billede afventer din godkendelse.

Publicering med datoer kræver læseadgang til kort, adresser, udlån og historik samt delingsret. Administratoren vælger rettighederne i appen. Gruppefunktioner giver ikke disse rettigheder.

## Efter godkendelse

LTM gemmer det godkendte billedgrundlag i en privat lokal cache. Når de registrerede datoer ændres, opdaterer serveren kun de to reserverede datofelter. Den bruger samme Google-fil og QR-link. Et gammelt dateret billede lukkes før erstatningen, når Google kan nås; offentlig adgang genåbnes kun med en bekræftet aktuel udlevering og aktuelle oplysninger.

Appen skal køre og have forbindelse til Google. Ved netfejl eller en mistet bekræftelse vises venten/fejl, og lukning eller upload forsøges begrænset igen. Et allerede offentligt billede kan forblive tilgængeligt, indtil Google bekræfter lukningen. **Fjern offentlig adgang** gemmer stoppet lokalt før Google-anmodningen, så en senere datoændring ikke genåbner billedet.

Adresse-, grænse-, navn-/område- og IB-ændringer bruger fortsat den almindelige billedkontrol. Cachen kan ikke bruges til at godkende et ændret kortgrundlag. Den gamle deling lukkes, og du skal danne og godkende et nyt billede.

## Backup og gendannelse

Billedcachen er et gendanneligt arbejdsgrundlag og indgår ikke i databackup eller kontobackup. Efter import/gendannelse genoptages tidligere uploads og datoopdateringer ikke; et nyt billede skal kontrolleres og godkendes. Hvis cachefilen mangler eller er beskadiget, lukkes gammel adgang, når Google kan nås, og appen beder om ny billedgodkendelse. Distriktsdata og fysisk kort går ikke tabt ved tab af denne cache.

Kun de to datoer tilføjes til det allerede godkendte offentlige kort. IB, navne, noter, brugerkonti og forbindelser uploades ikke. Reglerne om adgang under udlevering og om genbrug af QR-link er bevaret; der er ikke oprettet ny hosting eller en præsentationsside.
