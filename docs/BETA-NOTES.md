# LTM 1.12.0-beta.12

## Nyt siden beta.11

Det digitale QR-kort har fået et nyt layout: tydelig blå overskrift med kortnummer/navn, stor kortflade, enkle oplysninger og en lille miniature af printforsiden i hjørnet. Miniaturen genbruger den blanke S-12-forside og den fysiske forsides vejlinjeformatering, men bygges kun af offentligt godkendte adresser. Den er ikke et skærmbillede af dit private kort. IB-oplysninger, noter og forkyndere er ikke med.

Eksisterende Drive-filer, QR-links og åbning/lukning efter udlevering bevares. Ældre billeder markeres til layoutopdatering. Der uploades ikke noget automatisk på grund af det nye design; du skal kontrollere og godkende et nyt preview.

## Prøv især

1. Opdater **Distrikt Beta**, og tag først privat backup af betadata. Stabil 1.11.1 fortsætter separat.
2. Brug et ufølsomt prøveområde på en særskilt Google-testkonto. Vælg **Opdater Google Drive-upload** for kortet.
3. Kontrollér det nye preview: kortnummer/navn, kortflade, besøgspunkter og den lille printforside. Kontrollér særligt, at miniaturen kun indeholder offentligt godkendte adresser og ingen IB-oplysninger.
4. Annullér først en prøve og kontrollér, at det gamle billede/link bevares. Dan derefter et nyt preview og godkend udtrykkeligt.
5. Kontrollér på telefonen, at samme trykte QR åbner det opdaterede billede. Prøv udlevering, aflevering og genudlevering som hidtil; kontrollér åbning/lukning i privat browser.

Programprøver bruger fiktive data. Standardkort, langt navn/kortnummer, tætte kort og tomme kort er renderet som SVG/PNG og kontrolleret visuelt. Privat indhold er bevidst lagt i fiktive lokale felter for at kontrollere, at det ikke kommer i billedet. PNG-format, lokal skabelon, afbrudt indlæsning, layoutmigration, manuel godkendelse og bevaret QR er prøvet. Fysisk HA/browser/telefon og egen Google-konto står særskilt; der er ikke uploadet til ejerens Drive.

Beta.11's kurvede vejskel bevares. W16's naturlige skel og avancerede vejnet mangler. Den ekstra KTM-opfølgningsliste er fortsat fjernet. Den faste køreplan står på 20 %.
