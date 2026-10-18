# LTM 1.12.0-beta.40

Ét fejlpunkt: W62. Denne beta tilføjer en nødvendig læsende diagnose; adressehentningsfejlen er endnu ikke rettet.

- Åbn Kort og adresser → Hent adresser → Datafordeleren · egen API-nøgle → Kontrollér DAR-opslag.
- Kontrollen bruger fiktive søgeværdier, de faktiske feltprojektioner og samme transport. Den sammenligner almindelige opslag med ét og ti aliases. Den kan tage op til ét minut.
- Den gemmer ingen adresser og ændrer hverken checkpoints eller den gemte forbindelse. Nøglen bliver i installationen bortset fra den normale autentifikation hos Datafordeleren.
- Kun faste kategorier, kendte fejlkoder og udvalgte tekniske diagnoseord vises. Rå leverandørtekst og adresser vises ikke. ACCEPTED betyder kun, at den pågældende fiktive forespørgsel blev accepteret; det beviser ikke en komplet virkelig adressehentning.

Næste prøve er denne ene læsende kontrol i den eksisterende installation. Der er ikke behov for en ny privat nøgle eller gentagelse af adresseimporten. W62 er fortsat åben. Main er stabil 1.11.1.
