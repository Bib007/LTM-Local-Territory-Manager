# LTM 1.12.0-beta.13

## Nyt siden beta.12

Korteditor, samlet distriktsgrænse og KML/GeoJSON-import kan betjenes på dansk og engelsk. Sprogskift bevarer kortudsnit, adressevalg, ugemt tegning, formularindtastninger og valgt importfil. Kortnumre, vejnavne og gemte typer ændres ikke. Kortvælgeren er tilpasset smalle skærme.

Sene forhåndsvisninger og importsvar erstatter ikke en nyere kladde eller dialog. En gemning bruger det kontrollerede valg, og nyere ændringer under gemning bevares som ugemt tegning. Dobbeltgemning blokeres. En afsluttet kortdatahentning genopbygger ikke editorens formular.

## Prøv især

1. Opdater **Distrikt Beta**. Stabil 1.11.1 kører separat. Brug opdigtede oplysninger i betaen.
2. Åbn en kortgrænse, flyt et hjørne og udfyld vej-/nummerfelter. Skift dansk/engelsk; kontrollér at tegning, zoom, valg og felter bevares. Gem og genåbn.
3. Åbn samlet grænse. Ret et hjørne og skift sprog. Gem og kontrollér den genåbnede grænse.
4. Importér en ufølsom KML/GeoJSON med flere grænser. Vælg grænse, skift sprog, kontrollér previewet og annullér først. Importér igen, læg grænsen i tegningen, ret og gem den udtrykkeligt. Filvalg alene gemmer intet.
5. Prøv på telefonen, at kortvalg, tegneknapper og import kan betjenes uden afskåret indhold.

Program- og Chromium-prøver bruger fiktive data/svar og lokal Leaflet. Browserprøver dækker 320/390/768/1440 pixels, kort-/felt-/fokusbevaring og import; asynkrone programprøver dækker sene/ombyttede svar og redigering under gemning. Egen HA/telefon, Datafordeler, Google og fysisk print er særskilte ejerprøver.

Den faste køreplan er nu 30 % (3/10). Næste er avanceret opsætning og lokal IB-import. Ønskelisten er sat på pause efter ejerens aftale; KTM-opfølgningslisten er fortsat fjernet.
