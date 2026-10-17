# LTM 1.12.0-beta.11

## Nyt siden beta.10

Automatisk inddeling kan nu følge et lokalt gemt vejforløbs faktiske knæk og kurver. Vejstykker med samme navn forbindes kun ved præcist fælles endepunkt uden forgrening. Små huller lukkes ikke, og veje forlænges ikke kunstigt.

Skæringen kræver et enkelt forløb gennem området med to grænsekrydsninger. Tvetydige berøringer, løkker, selvkrydsning og komplekse krydsninger vælges ikke automatisk. Areal og overlap kontrolleres, og alle lejligheder i et hus skal stadig høre til samme kort. Forslaget kan rettes manuelt og kræver fortsat samlet godkendelse. Beregningen bruger kun lokale data og foretager ingen netkald.

## Prøv især

1. Opdater **Distrikt Beta**, og tag først privat backup af betadata. Stabil 1.11.1 fortsætter separat.
2. Brug et lille prøveområde med både lokale adresser og vejlinjer. OSM-baggrundsbilledet alene er ikke vejlinjer til beregningen.
3. Åbn **Indstillinger → Avanceret → Opsæt distrikter**, og lav et forslag. Kontrollér en gennemgående kurvet vej: fælles skel skal følge vejens faktiske knæk.
4. Kontrollér adressevalg, lejligheder og besøgstal. Prøv at rette et fælles hjørne og vælg **Kontrollér ændrede grænser og besøg**.
5. Kontrollér bemærkninger om geometrisk deling, hvor et egnet vejforløb mangler. Annullér en ren prøve; opret først kort efter at have gennemgået hele forslaget.

Se [trinvis vejledning](AUTOMATISK-INDDELING.md). Automatiske prøver bruger fiktive kurver, vejstykker og adresser. De dækker dækning uden huller/overlap, bevarede knæk, ikke-gættede forbindelser, forgreninger, husgrupper, manuel rettelse og faktisk oprettelse i midlertidige databaser. Visuel HA-/kortprøve står særskilt.

W16 er stadig i gang: naturlige skel og avancerede vejnet mangler. Den ekstra KTM-opfølgningsliste er fortsat fjernet. Den faste køreplan står på 20 %.
