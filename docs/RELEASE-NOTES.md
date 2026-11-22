# LTM 1.12.37

Afgrænset Stable-rettelse oven på 1.12.36. Import af historik viser nu tydeligt, hvorfor godkendelse kan være blokeret, og lader brugeren skrive i bekræftelsesfeltet. Ingen andre Beta-funktioner er med.

## Rettelse

- Efter forhåndskontrol er feltet **Skriv IMPORTÉR HISTORIK** altid skrivbart, også hvis nogle rækker har fejl eller ingen nye poster kan tilføjes.
- Ved fejl vises en forklaring om at rette tabellens fejl og kontrollere igen. Når der ikke er nye poster, forklares det, at rækkerne kan være dubletter eller uden for den understøttede importperiode.
- **Tilføj den kontrollerede historik** kan fortsat kun bruges, når der er mindst én gyldig ny gennemgang eller ét nyt udlån, og ingen fejl. Serverens kontroller ændres ikke.
- Rettelsen af nyeste-/ældste-først-datoorden fra Stable 1.12.36 samt alle eksisterende registreringer og øvrige Stable-funktioner bevares.

## Kontrol og udgivelse

Alle PR- og releasekontroller skal være grønne på det præcise `main`-commit. Udgivelse af Home Assistant og andre Stable-spor kræver manuel igangsættelse af **Stable release tracks**. macOS-server udgives kun efter særskilt fysisk Apple Silicon/LAN/VPN/genstartstest. Eksisterende udgivelsestags og aktiver overskrives ikke.

## English

LTM 1.12.37 is a focused Stable hotfix on top of 1.12.36. The history confirmation input stays editable after every preview, with an actionable explanation when errors or no new records block approval. The apply button and server continue to reject invalid or no-op imports; all existing Stable features and stored records remain unchanged. Unfinished Beta changes are excluded, and each Stable track retains its manual release gate.
