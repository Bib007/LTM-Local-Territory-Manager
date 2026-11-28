# Import fra Territory Helper

1. Åbn **Importér / Eksportér** i Territory Helper.
2. Under **Eksportér til CSV** henter du **Distrikter**, **Lokationer**, **IB**, **Forkyndere** og **Tildelinger → Altid**.
3. Hent **Distrikter** som **JSON** eller **KML** for at tilføje polygongrænser. JSON kan også bruges til at oprette kortlisten.
4. I LTM Beta åbner du **Opsætningsguidens første trin → Importér fra Territory Helper** og slipper de downloadede filer i importfeltet. LTM finder kategorierne. Behold de originale navne på Lokationer og IB, da deres kolonner er ens.
5. Tryk **Forhåndsvis kort**. Vælg et kort og kontrollér dets grænse, lokationer, IB og tildelinger. Brug **Godkend og gem dette kort** eller **Godkend alle kort**. Ved samlet godkendelse gemmes brugbare kortdata, og ugyldige importrækker gemmes til **Opfølgninger → Ret importerede rækker**, hvor du kan rette og gemme hver række. Kort med ugyldige eller optagede numre får et midlertidigt TH-nummer, som du kan rette samme sted.
6. Vælg **Fortsæt opsætningsguiden** for at fortsætte til den guidede rundtur, også under en delvis import. Du kan også vælge **Foreslå ydergrænse ud fra distriktskort**, kontrollere forslaget og gemme grænsen, før du henter DAR-adresser. Åbn derefter korteditoren og vælg **Foreslå DAR-adresser fra koordinater** for at matche importerede adresseprikker mod lokalt hentede DAR-adresser.

Importen er lokal. Rækker uden entydigt kort vises særskilt. Et eksisterende kort med samme nummer overskrives ikke. En afleveringsdato registreres kun som en gennemgang, hvis eksporten udtrykkeligt angiver en gennemgang. LTM’s indstillede historikperiode gælder også ved import. Forkyndernavne bruges til godkendte tildelinger. Kontaktfelter fra forkyndereksporten importeres ikke.

[KML-eksport i Territory Helper](https://www.territoryhelper.com/Help/TerritoryExport)
