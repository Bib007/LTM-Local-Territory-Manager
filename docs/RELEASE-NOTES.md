# LTM 1.12.34

Målrettet Stable-rettelse af Læsearkivets IB-layout og knapplaceringen under Indstillinger. Ingen øvrige udviklingsændringer eller DAR-preview-rettelser er med.

- **IB-bagsider i læsearkivet:** PDF/02 anvender det almindelige IB-printlayout med kortnummer, "ØNSKER IKKE BESØG", vejoverskrifter, numre og datoer. Lange lister deles efter samme browseropmålte regler som print, så hver fortsættelsesside også kommer med.
- **Sikkerhed ved eksport:** Browseren danner IB-siderne lokalt. Serveren kræver alle sider og den samme dataversion, før ZIP-filen frigives. Siderne ligger som højopløste billeder i A4-portræt; private IB-data lægges ikke på nogen ekstern tjeneste.
- **Indstillinger → Data:** **Eksportér læsearkiv** er flyttet direkte ved siden af **Sikkerhedskopi**.

Revisionskontrol, øvrig backup og brugerrettigheder er uændrede. Regressionerne anvender kun fiktive data. macOS-serverens fysiske testgate gælder stadig.

## English

Focused Stable fix for the readable archive's IB-page layout and Settings button placement. No unrelated development or DAR preview changes are included.

- **IB backs in the readable archive:** PDF/02 now uses the normal IB print layout: territory number, do-not-call header, street groups, house numbers and dates. Long lists follow the same measured pagination and include continuation pages.
- **Safe export:** The browser renders IB pages locally; the server requires all pages and an unchanged data revision before releasing the ZIP. Pages are high-resolution images on portrait A4, with no external upload of private IB data.
- **Settings → Data:** **Export readable archive** sits immediately beside **Backup**.

Revision checks, restoration backups and permissions are unchanged. Tests use fictional records only. The physical macOS-server release gate remains in effect.
