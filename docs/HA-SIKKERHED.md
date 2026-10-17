# HA-sikkerhed · afgrænset gennemgang

17.10.2026 · programkilde c0528c9 · [English](HA-SECURITY.en.md)

Gennemgangen omfatter appens HA-konfiguration, startscript, container og eksisterende adgangskontrol. Den er baseret på offentlig programkode og de beståede fiktive program-/LAN-prøver. Ejerens installerede Supervisor, netværk, konti og data er ikke åbnet. Dette er ikke en fuld sårbarhedsscanning.

## Faktisk konfiguration

| Område | Aktuel implementering | Betydning |
| --- | --- | --- |
| Vært og rettigheder | `host_network: false`; ingen privilegerede capabilities, Docker-socket, hardware eller ekstra hostmapper | Appen beder ikke om udvidet værtsadgang. |
| HA-API'er | `hassio_api: false`, `homeassistant_api: false`; ingen ekstra API-rolle | LTM bruger ikke administrative HA-API'er. |
| Browseradgang | Eksponeret privat port 8787; beta 8788; `ingress: false` | Eget LAN/VPN-login, ikke HA's ingress-login. HTTP-forbindelsen har ikke selv transportkryptering. |
| Beskyttelse | Ingen frakobling af AppArmor eller protection mode; ingen egen `apparmor.txt` | Standardbeskyttelsen anvendes; der er ingen app-specifik profil. Faktisk indlæsning er ikke aflæst i ejerens HA. |
| Login og lokale filer | Mindst 12 tegn ved ny HA-kode; PBKDF2/SHA-256 med salt; private filer med 0600; tidsbegrænsede sessioner | HA-optionen er et maskeret passwordfelt. Maskering betyder ikke, at optionsfilen er krypteret; HA-administratorer har fortsat adgang til konfigurationen. |
| HTTP-kontrol | Privat klientnet, Host/Origin-kontrol, session og separat token til API; HttpOnly/SameSite-cookie; CSP | Kontroller er dækket af `test_lan.py` og `test_http.py`. En privat IP er ikke alene brugerautentifikation. |
| Data og backup | Egen `/data`-mappe; brugerdata udeladt af HA-backup | Privat backup skal fortsat hentes i appen. Credentials følger ikke med portable backups. |

## Hvorfor vurderingen ikke automatisk er maksimal

Home Assistants aktuelle reference beskriver et grundtal på 5, med bonus for blandt andet ingress eller indlæst egen AppArmor-profil. LTM har eksponeret port, eget login og ingen egen profil. **Den beregnede vurdering for den gennemgåede konfiguration er derfor 5 efter den aktuelle formel.** Ejerens viste tal er ikke aflæst, og ældre Supervisor-versioner kan præsentere skalaen anderledes. Talberegningen er ikke en vurdering af samtlige mulige programfejl.

## Næste ændringer, der kan vurderes konkret

1. **Egen AppArmor-profil:** Bevar LAN/VPN-funktionen, men afgræns fil- og procesadgang. Profilen skal tillade Python, SQLite/WAL, læsning af program/formularer, skrivning i appens `/data` og midlertidige mapper samt nødvendige netforbindelser. Den skal afprøves med installation, backup/gendannelse, QR/PDF og Google/Datafordeler i en isoleret HA-beta. Ingen uprøvet profil er aktiveret her.
2. **Proces uden root:** Afklar særskilt startforløb og eksisterende dataejerskab før ændring. En rettighedsmigrering må ikke gøre gamle databaser eller backups utilgængelige.
3. **Ingress eller HA-auth:** Dette ændrer adgang, login, URL'er og blandt andet Origin/CSP- og OAuth-forløb. Det er en større arkitekturændring og skal aftales med ejeren, før den implementeres. Mac/Windows og det aftalte LAN/VPN-forløb skal stadig fungere.
4. **Transportkryptering:** Direkte HTTP forbliver den eksisterende LAN/VPN-løsning. En eventuel lokal HTTPS-/ingress-løsning vurderes sammen med adgangsarkitekturen; ingen interneteksponering er tilføjet.

Der er ikke givet nye privilegier, ændret loginarkitektur eller ændret datarettigheder i denne gennemgang. W06 er gennemgået indledende, men er ikke afsluttet med en afprøvet AppArmor-/adgangsændring. W15's forkynderforslag kan fortsætte uafhængigt af disse beslutninger.

## Primære kilder

- [Aktuel sikkerhedsvurdering, opdateret 12.10.2026](https://contributors.home-assistant.io/apps/reference/security-rating/).
- [HA's sikkerhedsvejledning](https://contributors.home-assistant.io/apps/guides/security/).
- [Konfiguration og standardværdier](https://contributors.home-assistant.io/apps/reference/configuration/).
