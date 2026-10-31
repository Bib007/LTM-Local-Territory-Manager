# Importér eksisterende distriktskort

[English](KORTIMPORT.en.md)

Brug importen til kortnumre, manuelle vejlinjer eller præcise adresser. Den findes i spørgsmålsguiden og under **Indstillinger → Import → Åbn kortimport**. Den virker også, når du begynder uden kortfunktion.

1. Hent Excel-skabelonen i appen. Fanen **Distriktskort** er tom og klar til udfyldning; **Vejledning** forklarer felterne med opdigtede eksempler.
2. Udfyld én række pr. adresse eller manuel vejlinje. Et kortnummer alene kan også bruges; lad da alle adressefelter være tomme. Gentag kortnummeret på hver række. Område, kortnavn og distriktstype kan udfyldes ved første række på kortet; gentagne oplysninger skal være ens.
3. Gem som `.xlsx`, og vælg filen i appen. Samme kolonner kan gemmes som CSV med semikolon eller komma. Gem gamle `.xls`-filer som `.xlsx` først. Brug værdier, ikke formler.
4. Kontrollér områder, kortnavne, adresser og besøg. Dubletter, kortnumre der findes i forvejen og andre fejl skal rettes i filen. Vælg derefter filen igen.
5. Skriv **IMPORTÉR KORT**, og godkend. Alle kort oprettes samlet i kassen. Kort med vejlinjer markeres til printkontrol; rene registerkort afventer ikke print. En fejl stopper hele importen.

| Kolonne | Indhold |
| --- | --- |
| Kortnummer | Påkrævet på hver række. Bogstaver og indledende nuller bevares, når feltet er tekst. |
| Område | Eksisterende område genbruges ved samme navn. Nye områdenavne oprettes ved godkendelse. |
| Kortnavn | Valgfrit navn på kortet. |
| Distriktstype | By, Land eller Ukendt. Tomt felt bliver Ukendt. |
| Vejnavn | Fx Fiktivvej. Udfyld både vej og nummer/interval, eller lad alle adressefelter være tomme. |
| Husnummer | Fx 12A eller intervaltekst som 1–19. Et interval bevares som én manuel vejlinje på printforsiden. |
| Etage og dør | Valgfrit. Én række pr. lejlighed bevarer præcis udvælgelse af IB. |
| Postnummer | Fire cifre ved en præcis adresse. Valgfrit ved manuelle vejlinjer. |
| Adressetype | En af skabelonens typer. Tomt felt bliver Hus. |
| Besøg | Helt tal fra 1 til 10.000. Tomt felt betyder ukendt ved en manuel vejlinje; ved en præcis adresse bliver det 1. |

Importen læser højst 2 MB, 10.000 linjer, 500 kort og 300 vejlinjer eller adresser pr. kort. Den sender ingen adresseopslag til eksterne tjenester. Geografiske adresser og grænser kan vælges senere i korteditoren, ét kort ad gangen. Samme kortnummer, udleveringer, IB og historik bevares. Vejlisten følger derefter de valgte adresser; kontrollér og godkend printet igen. Eksisterende kort, udleveringer og historik overskrives ikke; reserverede kortnumre i Gendan ved fejl kan heller ikke genbruges.

De præcise adresser følger med i privat backup og kan matches ved lokal IB-import. Rettes vejlisten manuelt, følger adresseudvalget de rækker, der beholdes. Der tilføjes ikke automatisk IB ved kortimport, og IB reducerer ikke kortets samlede besøgstal.

Udfyldte filer med virkelige adresser skal blive på dit eget system. Brug opdigtede eksempler i fejlmeldinger.

## Ukendte besøgstal

Et interval tælles ikke automatisk. Manglende antal vises som ukendt på kort, print og i aktuelle totaler. Udfyld et kendt antal i kortets almindelige redigering, eller vælg præcise geografiske adresser senere. En gennemgang registreret med ukendt antal tæller stadig som en gennemgang; den bidrager ikke til besøgsskønnet. Senere ændringer af kortet omskriver ikke den tidligere gennemgang.

## Flere filer

Vælg op til 20 Excel-/CSV-filer, højst 2 MB pr. fil og 20 MB samlet. Godkend hver fil særskilt, og vælg derefter **Kontrollér næste fil**. En fil kan springes over. Tidligere godkendte filer bevares ved lukning eller fejl. Dette gælder kortfiler; billeder og IB-filer er endnu ikke med i køen.
