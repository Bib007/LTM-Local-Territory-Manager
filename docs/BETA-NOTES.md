# LTM 1.12.2-beta.78 · Adressekontrol og driftsbeskeder

Adressekontrollen bevarer færdige udsnit og kan fortsætte hurtigt efter korte afbrydelser. Gentagne problemer, ventetid fra adressekilden og ressourcepres giver en passende pause. Visningen forklarer den seneste afbrydelse og næste forsøg. Længere arbejdsrunder kan genoptages.

I Home Assistant kan LTM nu vise driftsstatus. Under **Indstillinger → Backup og vedligeholdelse → Drift og beskeder** findes en klar beskedopskrift. Importér den, vælg beta og din telefon, tilføj eventuelle egne noter, og gem. **Send én prøvebesked** afprøver beskeden uden at skabe en fejl eller ændre data. Normale pauser giver ingen fejlbesked; opskriften kan også opdage manglende livstegn.

HA-appen får adgang til Home Assistants lokale API for at aflevere status og den udtrykkelige prøve. Forbindelsen har administrativ HA-adgang; LTM bruger kun faste lokale status- og prøveveje. Afleveringen kan slås fra med **drift_status** i HA-appens konfiguration. Det tilbagekalder ikke selve API-rettigheden. [Opsætning, måling og adgangens omfang](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/v1.12.2-beta.78/docs/HA-DRIFTSSTATUS.md).

Prøv kun den nye opsætning, én prøvebesked med din note og genoptagelse af en konkret afbrudt adressekontrol med opdigtede betaoplysninger. Fremkald ikke rigtig overbelastning. De allerede godkendte generelle HA-, Drive- og datagendannelsesprøver gentages ikke.

Alle tidligere profilrettelser og kontobackup er med. Datoer på onlinekort, vejintervaller, tjenestegrupper og IB fra Excel mangler stadig før næste stabile. OCR og automatisk kortinddeling er fortsat på pause. Stabil er fortsat 1.12.1.
