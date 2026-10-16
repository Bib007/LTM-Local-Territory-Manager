# Udgiv webdemoen

[English](DEMO-HOSTING.en.md)

Demoen er en statisk browserapp med opdigtede data. Kun de udtrykkeligt tilladte demofiler offentliggøres. Den private Python/SQLite-server køres ikke online af demoen.

## Ejeropsætning på GitHub

Pages er valgfrit og er ikke nødvendigt for installation i Home Assistant.

1. Brug det gennemgåede offentlige repository med demofilerne. Gør ikke den private udviklingshistorik offentlig alene for Pages.
2. Under **Settings → Pages → Build and deployment** vælges **Source: GitHub Actions**.
3. Åbn **Actions → Demo checks and Pages → Run workflow**, vælg `main`, og start den.
4. Brug først den faktiske adresse som demolink, når GitHub viser en vellykket udgivelse, og siden kan åbnes uden GitHub-login.

Workflowet kontrollerer kode, men ændrer ikke selv synlighed eller Pages-indstillinger.

## Afgrænsning

Demoen må kun indeholde opdigtede data. Hver besøgendes ændringer gemmes i den pågældende browser. Nulstilling rydder kun denne demotilstand. Der er ingen privat import, rigtig Google-forbindelse eller adgang til en installeret LTM.

Dansk vises som standard, og engelsk kan vælges. OSM-fliser kræver internet og korrekt kildeangivelse. Faktisk hosting, netværksadgang og fysiske enheder er særskilte kontroller.

## Kilder

- [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Pages-workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
