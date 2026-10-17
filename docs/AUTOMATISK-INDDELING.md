# Forslag til distriktsinddeling

[English](AUTOMATISK-INDDELING.en.md)

På develop fra 1.12.0-beta.11 kan et forslag følge et lokalt gemt vejforløb med knæk og kurver. Vejstykker med samme navn forbindes kun, når deres endepunkter mødes præcist, og forbindelsen ikke er forgrenet. Der oprettes først kort, når du har gennemgået og godkendt hele forslaget.

## Klargør et lille prøveområde

1. Åbn **Indstillinger → Avanceret → Opsæt distrikter**. Kontrollér den samlede ydergrænse, og hent adresser til området.
2. Kontrollér også, at lokale vejlinjer er hentet. Et OpenStreetMap-baggrundsbillede er ikke i sig selv vejlinjer til beregningen. Under **Kortdata → Hent bygninger i det viste kortudsnit** kan et mindre vist udsnit hente både veje og bygninger. Brug et lille område ad gangen.
3. Vælg områder, nummerering og omtrentligt besøgstal. Hver lejlighed tæller fortsat som et besøg, og samme hus holdes sammen.
4. Vælg **Lav forslag til distriktskort**. Kontrollér på kortet, at de foreslåede skel følger de viste veje, og læs bemærkningerne ved hvert kort.

Beregningen bruger de allerede gemte adresser og vejlinjer. Den starter ikke nye netkald og sender ikke kort, forkyndere eller IB til en tjeneste.

## Gennemgå før oprettelse

- Et accepteret vejforløb følger sine faktiske knæk. Et hul mellem to vejstykker lukkes ikke ved at tegne en ny forbindelse.
- Forløbet skal gå gennem området og krydse grænsen to steder. Løkker, tvetydige krydsninger og kompliceret genindtræden i området vælges ikke automatisk. Ved manglende egnet forløb kan den hidtidige lige deling bruges, og geometrisk deling uden egnet vejskel markeres til manuel kontrol.
- Vælg **Ret grænser på kortet** for at flytte hjørner. Fælles hjørner flyttes sammen; vælg derefter **Kontrollér ændrede grænser og besøg**. Kontrollér stadig adgang, afskårne områder og besøgstal.
- Ret navne og numre efter behov. Skriv først **OPRET KORT**, når hele forslaget er gennemgået. Annullering af et forslag opretter ingen kort, og eksisterende kort og deres historik overskrives ikke.

Ændrede adresser eller vejdata gør en gammel forhåndsvisning ugyldig. Lav et nyt forslag efter en sådan ændring.

Naturlige skel som vandløb og jernbaner er endnu ikke et særskilt datagrundlag for inddelingen. Avancerede vejnet og komplekse skæringer kræver fortsat manuel rettelse. W16 er derfor ikke markeret færdig. Betakanalen og egne HA-/kortprøver beskrives i [betavejledningen](BETA.md).
