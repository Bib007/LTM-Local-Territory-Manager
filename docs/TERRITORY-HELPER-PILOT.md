# Territory Helper i LTM Beta

Piloten henter ét dansk distriktskort ad gangen i den lokale desktop-beta. Den viser kortnummer, navn og geografisk grænse til kontrol. Bekræftelsen gemmer kortet som **Under opbygning**. Find kortet under **Distriktskort**, og kontrollér grænsen og vejlisterne, før du fjerner markeringen.

## Forbered live-testen

1. Få Territory Helper til at oprette en OAuth-klient til LTM Beta med **Authorization Code (PKCE)** og **S256**. Registrér `http://127.0.0.1:8787/territory-helper-return` eller den tilsvarende returadresse med den port, betaen bruger lokalt.
2. Sæt miljøvariablen `LTM_TERRITORY_HELPER_CLIENT_ID` til det tildelte klient-id, og start betaen lokalt. Åbn den på `127.0.0.1`.
3. Brug en Territory Helper-testmenighed og en bruger med adgang til distrikterne. Med LTM-profiler kræver piloten adgang til at administrere forbindelser og læse og redigere kort og geodata.
4. Åbn **Distriktskort → Kortværktøjer → Importér fra Territory Helper**. Indtast testmenighedens id og et entydigt kortnummer. Godkend login i Territory Helpers eget vindue, og sammenlign forhåndsvisningen med testkortet.
5. Gem kortet. Åbn det i LTM, kontrollér grænsen og prøv samme import igen for at kontrollere, at eksisterende kortnummer bevares.

Importen laver et enkelt opslag hos Territory Helper og beholder kun de tre kortfelter. OAuth-tokenet bruges under opslaget og gemmes hverken i backup eller browserlager. Betaen henter ikke adresser, forkyndere eller udleveringshistorik.

API-referencer:

- [Territory Helper REST API](https://territoryhelper.com/Help/GeneralApi)
- [Authorization Code (PKCE) og territorie-endpoints](https://territoryhelper.com/Api)
