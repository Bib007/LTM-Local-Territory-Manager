# LTM 1.12.19-beta.13 · Afvis adresseændringer uden for distriktsgrænsen

Under **Opfølgninger → Adresseændringer** findes en ny knap: **Afvis alle adresser uden for distriktsgrænsen**. Den er tilgængelig, når menighedens samlede distriktsgrænse er gemt.

Knappen åbner en **forhåndsvisning**, der viser antallet af afventende adresseændringer, som med sikkerhed ligger uden for grænsen, en liste over de første 30 afvisninger og antal ændringer, der kræver manuel kontrol. Kun adresseændringer med brugbare koordinater, som er uden for den **præcise gemte polygon**, udvælges – ikke alle adresser på en vej. Adresser på selve grænsen regnes som indenfor.

Ændringer, hvor den tidligere adresse lå indenfor grænsen, eller hvor koordinater mangler, afvises ikke automatisk. Bekræft ved at skrive **AFVIS UDENFOR**. Ved ændret grænse eller afventende adresseændringer siden forhåndsvisningen skal du gennemføre kontrollen igen.

Handlingen **fjerner kun afventende adresseændringer**, ikke de allerede downloadede adresser, eksisterende kort, IB, udleveringer eller historik. Den optræder i den lokale ændringshistorik. Automatisk adressekontrol og sideløbende adressehentning blokerer den samlede afvisning, så der ikke behandles halvfærdige resultater. Funktionens rettigheder følger den almindelige kontrol af geografiske data.

## English

Under **Follow-ups → Address changes**, the new **Reject all addresses outside the territory boundary** action previews a server-calculated set of pending DAR changes strictly outside the saved overall polygon. Addresses on the boundary remain in scope; unknown coordinates and moves from inside to outside remain for manual review. Type **AFVIS UDENFOR** to confirm. A stale preview is rejected. Only pending review records are dismissed; downloaded addresses, existing cards, do-not-call records, assignments and history are preserved. Stable is unchanged.
