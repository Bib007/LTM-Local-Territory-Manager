# Webdemo med opdigtede data

[Åbn demoen direkte](https://bib007.github.io/LTM-Local-Territory-Manager/) · ingen installation eller GitHub-konto. Brug rodadressen med afsluttende `/`; tilføj ikke `/demo/`.

Demoen er en selvstændig browserudgave med opdigtede kort og forkyndere. Dansk er standard, og engelsk kan vælges. Ændringer gemmes kun i den enkelte browser. Der er ingen privat import, rigtig Google-forbindelse eller adgang til en installeret app.

Den kan bygges med `python3 scripts/build_demo.py`. [Udgivelse via Pages](../docs/DEMO-HOSTING.md) er valgfrit og kræves ikke for HA-installation.

## Produktdesign og afgrænsning

Demoen bruger et kontrolleret snapshot af appens CSS, tema og logoer fra beta.68. Forside, nøgletal, genveje, lister, formularer og menu følger produktets design; demoen har også eksempelvisninger for Opfølgninger og Kort og adresser. Ikke alle produktfunktioner er med. Privat import, ægte nøgle-/Drive-forbindelser og rigtige printgodkendelser er ikke tilgængelige.

Udseende vælges i menuen: Mørkt, Lyst eller Følg enheden. Valget gælder kun den aktuelle browser. Demoens registreringer ligger i dens egen browserlagring og har ingen adgang til en installeret LTM.

Opdatér det fælles designsnapshot med `python scripts/sync_demo_design.py`. Betaens kontrol kræver, at det matcher de udtrykkeligt tilladte produktfiler. Den offentlige demo bygges alene fra demo-mappen og kontrollerer snapshot-filenes kontrolsummer. Serverkode, databaser, API-nøgler og private registreringer indgår aldrig i udgivelsen.
