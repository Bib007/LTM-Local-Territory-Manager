# Tjenestegrupper og lokal gruppeimport

[English](TJENESTEGRUPPER.en.md)

Åbn **Forkyndere**. Vælg **Tilføj forkynder** eller **Rediger forkynder** for at angive tjenestegruppe, gruppefunktion og pioner. Et gruppenavn kan skrives frit; kendte navne foreslås. Gruppen kan filtreres i oversigten, og oplysningerne vises på forkynderens kort- og historikvisning.

Gruppefunktion kan være **Gruppetilsynsmand**, **Assistent** eller ingen. Der kan vælges én tilsynsmand og én assistent pr. gruppe. Pioner er en særskilt markering, som også kan kombineres med en gruppefunktion. Skift først den tidligere funktion ved en almindelig enkeltrettelse; en godkendt gruppeimport kan bytte funktionerne samlet.

Tjenesteoplysningerne opretter ikke en brugerkonto og giver ingen rettigheder til appen. Administratoren styrer fortsat konti og roller under Brugere og roller. En forkynder kan allerede have flere forskellige kort; der indføres ingen ny personbegrænsning. Et enkelt kort kan fortsat kun have ét aktivt udlån.

## Importér en liste

1. Vælg **Importér gruppeliste**, og hent den tomme Excel- eller CSV-skabelon.
2. Brug én række pr. forkynder. Excel-fanen hedder **Forkyndere**. Behold skabelonens kolonneoverskrifter.
3. Vælg den udfyldte fil. LTM viser nye, ændrede og uændrede rækker. Eksisterende navne matches uden hensyn til store/små bogstaver og ekstra mellemrum. Hvis mere end én eksisterende person matcher, skal navnene rettes i registeret først; appen gætter ikke.
4. Kontrollér især før/efter-oplysninger for eksisterende navne. En tom celle rydder en oplysning; en helt udeladt kolonne bevarer den eksisterende værdi.
5. Ret alle fejl, vælg filen igen, og skriv **IMPORTÉR GRUPPER**. Først derefter gemmes hele listen samlet.

| Kolonne | Indhold |
| --- | --- |
| navn | Påkrævet. Eksisterende entydigt navn opdateres med samme id. Nye navne oprettes. |
| tjenestegruppe | Valgfrit navn, fx Gruppe 01. |
| gruppefunktion | Gruppetilsynsmand, Assistent eller tom. |
| pioner | Ja eller Nej. Tom celle betyder Nej. |

Højst 2 MB og 5.000 linjer. XLSX og CSV med komma eller semikolon understøttes. Brug værdier i regnearket, ikke formler. Filen behandles lokalt; ingen OCR eller ekstern navnetjeneste bruges.

Eksisterende udlån, kort, gennemgange og ikke nævnte forkyndere bevares. Samtidige almindelige rettelser sammenføjes, og forskellige rettelser til samme felt gemmes til gennemgang. Ændres forkynderlisten efter forhåndsvisningen, kræver netop importen en ny gennemgang. Uafhængige kortrettelser spærrer ikke gruppeimporten.

Gruppeoplysninger følger den private databackup og læsearkivets forkynder-CSV. Kontobackup er stadig en særskilt funktion. Rigtige navnelister skal blive lokalt; brug kun opdigtede navne i offentlig feedback.
