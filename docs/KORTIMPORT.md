# Importér eksisterende distriktskort

[English](KORTIMPORT.en.md)

Brug importen, når adresser allerede er fordelt på kortnumre og områder. Den findes i spørgsmålsguiden og under **Indstillinger → Avanceret → Importér eksisterende distriktskort**. Den virker også, når du begynder uden kortfunktion.

1. Hent Excel-skabelonen i appen. Fanen **Distriktskort** er tom og klar til udfyldning; **Vejledning** forklarer felterne med opdigtede eksempler.
2. Udfyld én række pr. konkret adresse eller lejlighed. Gentag kortnummeret på hver række. Område, kortnavn og distriktstype kan udfyldes ved første adresse på kortet; gentagne oplysninger skal være ens.
3. Gem som `.xlsx`, og vælg filen i appen. Samme kolonner kan gemmes som CSV med semikolon eller komma. Gem gamle `.xls`-filer som `.xlsx` først. Brug værdier, ikke formler.
4. Kontrollér områder, kortnavne, adresser og besøg. Dubletter, kortnumre der findes i forvejen og andre fejl skal rettes i filen. Vælg derefter filen igen.
5. Skriv **IMPORTÉR KORT**, og godkend. Alle kort oprettes samlet i kassen og markeres til printkontrol. En fejl stopper hele importen.

| Kolonne | Indhold |
| --- | --- |
| Kortnummer | Påkrævet på hver række. Bogstaver og indledende nuller bevares, når feltet er tekst. |
| Område | Eksisterende område genbruges ved samme navn. Nye områdenavne oprettes ved godkendelse. |
| Kortnavn | Valgfrit navn på kortet. |
| Distriktstype | By, Land eller Ukendt. Tomt felt bliver Ukendt. |
| Vejnavn | Påkrævet, fx Fiktivvej. |
| Husnummer | Én konkret adresse, fx 12A. Intervaller som 1–19 skal fordeles på egne rækker først. |
| Etage og dør | Valgfrit. Én række pr. lejlighed bevarer præcis udvælgelse af IB. |
| Postnummer | Påkrævet, fire cifre. |
| Adressetype | En af skabelonens typer. Tomt felt bliver Hus. |
| Besøg | Helt tal fra 1 til 10.000. Tomt felt bliver 1. |

Importen læser højst 2 MB, 10.000 adresser, 500 kort og 300 adresser pr. kort. Den sender ingen adresseopslag til eksterne tjenester. Koordinater og grænser tilføjes senere i korteditoren. Eksisterende kort, udleveringer og historik overskrives ikke; reserverede kortnumre i Gendan ved fejl kan heller ikke genbruges.

De præcise adresser følger med i privat backup og kan matches ved lokal IB-import. Rettes vejlisten manuelt, følger adresseudvalget de rækker, der beholdes. Der tilføjes ikke automatisk IB ved kortimport, og IB reducerer ikke kortets samlede besøgstal.

Udfyldte filer med virkelige adresser skal blive på dit eget system. Brug opdigtede eksempler i fejlmeldinger.
