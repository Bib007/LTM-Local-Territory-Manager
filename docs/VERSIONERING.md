# Fælles versionssystem for LTM

**Gældende fra næste Beta og næste Stable efter den eksisterende Stable 1.12.35.**
Historiske tags omdøbes eller overskrives aldrig: Stable 1.12.35 og den ældre
Beta 1.12.19-beta.37 er et overgangstilfælde. De efterfølgende udgaver følger
ét fælles versionsnummer.

## Format og eksempler

En Stable har formen **MAJOR.MINOR.PATCH**: `1.12.36`.

En Beta for samme kommende Stable har formen **MAJOR.MINOR.PATCH-beta.N**:
`1.12.36-beta.1`, `1.12.36-beta.2` og til sidst **Stable 1.12.36**.
Betaens `N` tæller kun afprøvninger af *netop den planlagte Stable*.
Nulstilles til 1, når grundversionen skifter.

| Ændring | Regel | Efter Stable 1.12.35 |
| --- | --- | --- |
| Fejlrettelse, forbedring uden nye funktioner | PATCH +1 | `1.12.36-beta.1` → `1.12.36` |
| Ny bagudkompatibel funktion | MINOR +1, PATCH=0 | `1.13.0-beta.1` → `1.13.0` |
| Uforenelig ændring i data, API eller forventet funktion | MAJOR +1, MINOR=PATCH=0 | `2.0.0-beta.1` → `2.0.0` |

En Stable-udgivelse **stiger ikke igen**, når den godkendte Beta bliver Stable;
kun `-beta.N` fjernes. De fem Stable-spor (HA, Mac-app/-server og
Windows-app/-server) bruger samme Stable-nummer, også hvis de publiceres på
forskellige tidspunkter. En opdatering på ét spor udløser ikke et nyt nummer.

## Daglig arbejdsgang

1. Vælg typen (fix, feature, breaking) fra **seneste Stable på `main`**.
   Den praktiske hjælper beregner første betanummer:
   `python scripts/version_policy.py next --stable 1.12.35 --change fix`
2. Sæt samme nummer i `distrikt/app/server.py`,
   `distrikt/config.yaml` og `demo/design.json`; beskriv ændringerne i
   danske/engelske `docs/CHANGELOG*` og identiske `distrikt/CHANGELOG*`,
   og opdater `docs/BETA-NOTES.md`.
3. Opret PR til `develop`. Merge altid den aktuelle `main` ind i
   `develop` før næste beta, også efter en kritisk Stable-rettelse.
   Løs kodekonflikter bevidst; en manglende Stable-ændring må ikke
   forsvinde i den følgende Beta.
4. GitHub-udgivelsen af Beta kræver grønne program-/sikkerhedstests,
   **aktuel Stable som forfader**, næste lovlige betanummer og et ubrugt tag.
   Fejl stopper udgivelsen – den springes ikke stiltiende over.
5. Justeringer i samme planlagte version får **-beta.2**, **-beta.3** osv.
   Ingen allerede publiceret Beta må redigeres under samme tag.
6. Ved promovering: kopier den udgivne, afprøvede Beta-kode til en
   Stable-PR på `main`. Fjern `-beta.N`, men behold de første tre tal.
   Synkroniser release notes og changelogs, og kør alle tests.
7. **Stable release tracks** startes fortsat manuelt på præcis
   `main`-commit. Hvert spor genkontrollerer at versionsnummeret er lovligt,
   at der findes en udgivet Beta med samme grundversion, og at appens faktiske
   kode svarer til **seneste Beta** (bortset fra versionsstrengen).
   Hvert tag og hver pakke er uforanderlig. Mac-serverens fysiske
   Apple Silicon/LAN/VPN/genstart-godkendelse er fortsat obligatorisk.
8. Før *næste* Beta efter en Stable skal den nye version have en højere
   grundversion end Stable. En Stable-hotfix må ikke glemmes i Beta. Nye
   funktioner kan godt fortsætte mod et højere MINOR-nummer, hvis de
   seneste Stable-rettelser er indarbejdet.

## Håndhævelse

- `scripts/version_policy.py` beregner næste version og validerer
  versionsformat, increments, udgivne Git-tags, commit-identitet,
  Stable/Beta-grundversion, Beta-sekvens og `main`-forfader.
- `.github/workflows/beta.yml` stopper før publicering ved en fejl.
- `scripts/publish_release_track.sh` stopper før **hver enkelt**
  Stable-publicering, hvis version eller kodeparitet er forkert.
- `.github/workflows/check.yml` kører regressionsprøverne
  `scripts/test_version_policy.py` på alle PR'er.
- `scripts/check_changelog.py` og `scripts/build_release.py` afviser
  uens versioner og usynkroniserede danske/engelske release-noter.

Tomme betaversioner laves ikke alene for at holde et nummer ajour:
`develop` må gerne stå med en historisk Beta-version imellem
udgivelserne; en *ny* udgivelse kan først ske, når en korrekt version
er valgt og hele koden er synkroniseret.
