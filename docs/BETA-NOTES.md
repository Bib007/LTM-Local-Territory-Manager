# LTM 1.12.19-beta.36

- Rapporten viser nu **IB-registreringer i alt**, også manuelt skrevne IB-linjer, der ikke matcher en geografisk adresse.
- Tallet **Heraf kortlagt inden for grænsen** viser stadig kun IB-poster knyttet til kortlagte adresser inden for den gemte distriktsgrænse. Besøgstallet og tidligere IB-registreringer ændres ikke.
- Begge IB-tal følger rettigheden til at se IB og er også rettet i rapportens PDF.

## English

- The report now displays **all do-not-call entries**, including manually entered lines without a mapped address.
- **Of which mapped inside the boundary** remains the geographic subset within the saved territory boundary. Visit counts and existing do-not-call records are unchanged.
- Both totals require permission to view do-not-call records and are also shown in the report PDF.

## Afprøvning

- Åbn Rapporter og sammenlign IB-registreringer i alt med de aktive IB-linjer på distriktskortene, herunder manuelle linjer.
- Kontrollér, at **Heraf kortlagt inden for grænsen** kan være mindre end det samlede IB-tal, hvis nogle IB-poster ikke kan knyttes til en adresse inden for grænsen.
- Kontroller PDF-rapporten. Prøv eventuelt en bruger uden rettigheden til at se IB; ingen af IB-tallene må vises.
- DAR-preview-isoleringen i åbne PR #134 er ikke med i denne beta og er fortsat under særskilt kontrol. Stable er uændret.
