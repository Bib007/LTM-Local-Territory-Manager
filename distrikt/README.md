# Distrikt · Local Territory Manager

Hold styr på distriktskort, udleveringer og gennemgange fra din egen Home Assistant. Start enkelt med kortnumre og udlevering, og tilføj adresser, kort, IB og print, når du har brug for det.

## Det kan du bruge appen til

- Se hvilke kort der er i mappen, udleveret eller klar til næste gennemgang.
- Udlevere og modtage kort samt følge historikken.
- Arbejde med OpenStreetMap, adresser og lokale IB-registreringer.
- Udskrive distriktskort og rapporter med de originale S-12- og S-13-formularer.
- Importere allerede fordelte kort fra Excel/CSV og komme i gang med opsætningsguiden.

## Første start

1. Åbn fanen **Dokumentation**, og følg installationsvejledningen.
2. Angiv HA-maskinens **private adresse** og en **adgangskode på mindst 12 tegn** i konfigurationen.
3. Start appen, vælg **Åbn webbrugerflade**, og log ind med appens egen adgangskode.
4. Følg opstartsguiden. Du kan vælge enkel udlevering eller arbejde med kort og adresser og åbne rundturen igen senere.

## Dine data og din adgang

Registreringer opbevares lokalt på din HA-maskine. Appen åbnes på hjemmenetværket eller via VPN på din egen router. Den bruger sin egen webside på port 8787 og sit eget login.

**Tag backup i selve appen.** Appdata er udeladt af Home Assistants backup. Hent en privat backup før opdatering, flytning eller afinstallation.

Google Drive er et frivilligt tilvalg til godkendte kortbilleder og QR-koder. IB, forkyndere og historik indgår ikke i kortdelingen.

Flytter du fra en eksisterende installation, skal du følge flyttevejledningen i **Dokumentation** og beholde din private backup.

[English installation guide](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.en.md)
