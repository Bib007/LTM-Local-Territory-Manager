# LTM 1.12.0-beta.46

Opfølgning på læsearkivet fra beta.44/45: PDF-dannelse frigiver databaselåsen, mens arkivet bygges. Ændres data undervejs, stoppes download med krav om et nyt forsøg. Adressefiltreringen genbruger ét frosset datasnapshot, og kortbilleder dannes med uigennemsigtig baggrund.

Prøv med opdigtede data: Dan et læsearkiv med flere kort, åbn de fire PDF’er og CSV-filerne. Kontrollér, at appen fortsat reagerer under eksport. Redigér data fra en anden fane under opbygningen og kontrollér, at det gamle arkiv ikke downloades. De samlede forsiderettelser fra beta.45 følger med. Main er stabil 1.11.1.
