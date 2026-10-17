# LTM 1.12.0-beta.10

## Nyt siden beta.9

Første del af vejbaseret automatisk inddeling: lokalt hentede, gennemgående lige vejstykker kan bruges som skel, også på skrå. Algoritmen vælger blandt højst 256 lokale segmenter og prøver op til 32 relevante kandidater pr. deling. Der hentes ingen nye data under beregningen. Forhåndsvisningen viser vejnavnet og kræver stadig din godkendelse før oprettelse.

Et kort vejfragment forlænges ikke til en opdigtet gennemgående vej. Hvis et egnet vejstykke mangler, vises tydeligt, at delingen er geometrisk og skal rettes manuelt. Husenes lejligheder og alle adressepunkter kontrolleres samlet. Ændrede lokale vejdata gør en gammel forhåndsvisning ugyldig.

Dette afslutter **ikke W16**: kurvede veje, sammenhængende forløb af flere segmenter og naturlige skel kræver næste udviklingstrin. Grænser, adgangsforhold og besøgstal skal fortsat kontrolleres på kortet. Eksisterende kort ændres ikke af at beregne et forslag.

## Prøv især

1. Opdater **Distrikt Beta** og tag først privat backup af betadata.
2. Brug et lille prøveområde med lokalt hentede vejlinjer og adresser. Åbn Avanceret → Opsæt distrikter, og lav et forslag.
3. Find en gennemgående lige vej, også gerne skrå. Kontrollér, at et foreslået skel faktisk følger det viste vejstykke, og at alle adresser stadig har ét kort.
4. Kontrollér markeringen ved geometriske skel uden passende vejdata. Ret sådanne skel manuelt i forhåndsvisningen.
5. Kontrollér husenes lejligheder, besøgstal og fælles grænser før eventuel oprettelse. Annuller prøven, hvis den kun skal bruges til at se forslaget.

Automatiske prøver bruger fiktive vej- og adressegeometrier. De kontrollerer skrå og konkave skæringer, arealdækning uden overlap, ikke-forlængelse af korte vejstykker, lejligheder, deterministisk resultat, forældede forslag og eksisterende atomisk oprettelse. Virkelig HA/browser/kortvisning står særskilt.

Beta.9's lokale forkynderforslag og beta.8's DAR GraphQL bevares. Den ekstra KTM-opfølgningsliste er fortsat fjernet. Den faste køreplan står på 20 %.
