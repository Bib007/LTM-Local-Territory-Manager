# Installer Distrikt på Home Assistant OS

[English guide](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.en.md)

## Installation fra repository

1. Tilføj `https://github.com/Bib007/LTM-Local-Territory-Manager` under HA → Indstillinger → Apps / Tilføjelser → butik → ⋮ → Repositories.
2. Vælg **Distrikt → Installer**. HA henter programfilerne og bygger installationen. Der skal ikke kopieres programfiler med Samba.
3. I konfigurationen sættes **Privat adresse** (`access_host`) til HA-maskinens faste private IP eller lokale værtsnavn, uden http://, port eller skråstreg.
4. Vælg **Appens adgangskode** (`password`) på mindst 12 tegn. Det er appens eget login.
5. Behold port **8787 → 8787**, slå start ved opstart til, og start appen.
6. Åbn `http://DIN_PRIVATE_IP:8787` i browseren, og log ind.

## Eksisterende lokal HA-app

Repositoryudgaven har en anden HA-identitet og sin egen datamappe. Første flytning kræver en privat backup/import:

1. Hent en frisk backup i den gamle app under Indstillinger → Backup og gendannelse.
2. Stop den gamle app, før den nye startes på samme port. Behold den gamle installation og backup.
3. Importér backup gennem den nye app. Import erstatter data og fletter ikke; gennemgå oversigten før bekræftelse.
4. Google-forbindelsen følger ikke med backup og skal tilsluttes igen, hvis den bruges.

Senere repository-opdateringer installeres direkte i HA. En normal opdatering i samme installation kræver ikke import af backup. Afinstallér ikke den fungerende app for at opdatere.

## Data og backup

Appen bruger sin vedvarende `/data/distrikt`-mappe og har ikke adgang til HA-API, Supervisor-API eller andre apps' data. De oprindelige tomme formularer følger med; egne registreringer bliver på systemet.

**Appdata er udeladt af HA-backup.** Tag private backups gennem appen, også før opdatering, flytning og afinstallation. En almindelig HA-backup alene indeholder ikke distriktsdatabaserne.

## Adgang udefra

Forbind telefon eller computer til VPN på egen router, og åbn samme private appadresse som hjemme. VPN-regler skal tillade HA-maskinen og port 8787. Ingress og Nabu Casa bruges ikke; åbn ikke en offentlig internetport til appen.

## Hvis appen ikke åbner

- Kontrollér at adgangskoden har mindst 12 tegn, og se appens log.
- Brug præcis den adresse, som står i `access_host`, og port 8787.
- Hvis VPN fejler, men hjemmets Wi-Fi virker, kontrolleres VPN-ruter/firewall. En fast privat IP er ofte lettere gennem VPN end `.local`.
- Adgangskoden kan ændres i HA-konfigurationen efterfulgt af genstart. Sessioner udløber efter 12 timer eller genstart.

[Fuld dansk installationsguide](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.md) · [Valgfri Google og QR](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/GOOGLE-DRIVE.md)
