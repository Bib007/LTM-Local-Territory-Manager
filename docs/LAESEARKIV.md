# Læsearkiv uden LTM

[English](LAESEARKIV.en.md)

Åbn **Indstillinger → Data → Eksportér læsearkiv**. ZIP'en indeholder PDF'er og semikolonseparerede UTF-8-CSV-filer, der kan åbnes uden LTM. Den indeholder private navne, IB og opgaver og skal opbevares privat. Eksporten er adskilt fra den normale sikkerhedskopi til gendannelse.

De fire PDF'er samler forsider, IB-bagsider, digitale kort og alle opgaver. S-13-mappen indeholder hvert tjenesteår fra den ældste relevante gemte dato til den nyeste, også med arkiverede kort. Manglende historik opfindes ikke. CSV viser kortreferencer, præcise etager/døre og markerer gamle samlede vejlinjer som vejlinjer. Kort uden geografi findes stadig i forsider/CSV.

OpenStreetMap-kort vises ét ad gangen og medtages med **Medtag kort og fortsæt**. Næste kort hentes først efter dette valg; der er ingen automatisk massehentning. Visningen kræver internet, mens den færdige PDF er selvstændig. Digitale kort indeholder ikke IB, private opgaver eller udlånsnavne. OSM-attribution følger billederne.

Pakken hentes først, når alle kort er medtaget. Annullering, manglende kortbaggrund, ændrede data eller et udløbet forløb kræver en ny eksport. Der kan medtages op til 100 MB kortbilleder, og forløbet udløber efter en time. Kontrollér browserens download bagefter. Backupdatoen ændres ikke af et læsearkiv.

CSV beskytter brugerindtastninger, der kan ligne regnearksformler, med en indledende apostrof. Hele Unicode-teksten bevares i CSV; tegn som standard-PDF-fonten ikke kan vise angives med U+kode i læse-PDF'erne. Eksporten indeholder ingen adgangskoder, API-nøgler eller forbindelsesfiler og ændrer ingen genprintgodkendelser eller delte Google-kort.

[OpenStreetMaps kortserverpolitik](https://operations.osmfoundation.org/policies/tiles/) tillader normal interaktiv visning, men forbyder automatisk massehentning. Derfor medtager brugeren hvert vist kort eksplicit.
