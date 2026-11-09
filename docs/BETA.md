# Test LTM-beta i Home Assistant

Stable 1.12.20 indeholder nu de godkendte forbedringer fra Beta 1.12.19-beta.4. Betakanalen er fortsat en separat testinstallation; Beta 1.12.19-beta.4 indeholder personlige åbne opgaver på forsiden, forbedret IB-udskrivning, søgning efter eksisterende kort til mappen, sortering efter gennemgang og vejledende kortantal efter rolle. Fremover afprøves nye ændringer på Beta først. Betaer samler flere sammenhængende forbedringer, så nye funktioner kan prøves løbende. Den stabile udgave installeres fortsat fra den almindelige repositoryadresse. Beta erstatter ikke automatisk den stabile app.

## Installer betakanalen én gang

1. Åbn **Indstillinger → Apps / Tilføjelser → butik → ⋮ → Repositories**.
2. Tilføj hele denne adresse, inklusive `#beta`:

   `https://github.com/Bib007/LTM-Local-Territory-Manager#beta`

3. Vælg **Distrikt Beta → Installer**. Behold den stabile Distrikt-app installeret.
4. Sæt din HA-maskines private IP eller lokale værtsnavn under **Privat adresse**, og vælg en adgangskode på mindst 12 tegn.
5. Behold **8788 → 8788** under netværk. Start betaen manuelt, og vælg **Åbn webbrugerflade**. Adressen er `http://DIN_PRIVATE_IP:8788`.

Betakanalen har eget HA-appnavn, egen datamappe og eget login. Den stabile app fortsætter på port 8787. Beta starter med tomme data; en betaopdatering af samme installation bevarer dens testdata. Der skal ikke kopieres programfiler med Samba, og der skal ikke oprettes internetadgang til appen.

## Hver ny beta

Betaer samler flere sammenhængende brugerændringer i et overskueligt prøvesæt, frem for enten en stor bunke eller konsekvent kun 2–3 småting. Hver runde får et nyt nummer og en kort ændrings- og testliste på GitHub. Beta hentes fra en fast, kontrolleret version; almindelige mellemliggende ændringer på `develop` flytter ikke HA-betakanalen.

Vælg **Kontrollér for opdateringer** i HA's appbutik, og opdater **Distrikt Beta**. Hent en privat backup i betaens egne indstillinger, før du opdaterer. Også betaens data er udeladt af HA-backup. Hvis en beta giver problemer, kan den stoppes, mens den stabile app fortsætter.

Start med opdigtede prøveoplysninger. Brug en særskilt Google-konto til Drive-prøver: en beta med rigtige filnumre og den samme Google-konto kan ellers ændre delingen af de rigtige kortbilleder. Google-forbindelsen kopieres ikke fra den stabile app.

Se [betaudgivelserne](https://github.com/Bib007/LTM-Local-Territory-Manager/releases) for versionsnummer og de få ting, som skal prøves i netop den beta. Fejl og idéer beskrives på [hjemmesidens feedbackside](https://localterritorymanager.netlify.app/da/feedback/) med opdigtede eksempler.

## Til udvikling

`main` er stabil, `develop` er kildekoden under arbejde, og `beta` indeholder kun det genererede HA-snapshot fra en godkendt betaudgivelse. Der vedligeholdes én programkodebase.

Før hver ny beta opdateres versionsnummeret i serveren, HA-konfigurationen og tilhørende tilstands-/versionsprøver samt den korte betanote. Nummeret genbruges ikke til ændret kode. Workflowet kræver grøn programkontrol, Mac, Windows og bygning af HA-betapakken før offentliggørelse. En beta er en GitHub-prerelease og ændrer ikke den seneste stabile udgivelse.

HA understøtter en grengiven repositoryadresse: [officiel vejledning](https://contributors.home-assistant.io/apps/guides/repository/).

## Beta på Mac, Windows eller Linux

Hent Beta-versionens DMG eller Setup.exe direkte fra GitHub. Mac-programmet hedder **LTM Beta.app**; Windows-installationen hedder **LTM Beta** og har egen programmappe. Begge bruger **Distrikt-beta** som datamappe, separat fra Stable. Ingen separat Python er nødvendig for disse installationsfiler.

Til Linux eller privat server bruges fortsat den samlede LTM-v…zip og [Python-startguiden](SELF-HOSTING.md). Porten er 8788 og data/login holdes adskilt. Opdatér altid den samme kanal; gendan eller flyt kun rigtige data efter en bevidst beslutning og egen backup.
