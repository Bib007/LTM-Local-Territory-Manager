# LTM 1.12.0-beta.41

Ét fejlpunkt: W62. Denne beta retter brugen af aliaser i DAR-adressehentningen.

- Ejerens kontrol i beta.40 accepterede almindelige opslag for alle fem DAR-entiteter og afviste både ét alias og flere rodfelter.
- Hentning af vej, postnummer og samlet distriktsgrænse bruger nu ét almindeligt opslag ad gangen. Også opslag af ét enkelt ID er uden alias.
- Fælles tidspunkt, filtre, sidecursors, pause/genoptagelse og faste anmodnings-/resultatgrænser bevares. Ufuldstændige svar giver fortsat ingen delimport; eksisterende adresser og færdige udsnit bevares ved fejl.
- Flere separate opslag kan gøre en stor hentning langsommere. Grænserne afbryder med en tydelig fejl frem for at udelade adresser.
- Den læsende diagnosefunktion bevares. Dens alias-/batchprøver forventes fortsat afvist, fordi de undersøger leverandørens begrænsning; den almindelige hentning bruger dem ikke længere.

Efter opdatering: Prøv først én vej. Oplys kun antal hentede adresser eller den rensede fejltekst. Ved succes prøves derefter samlet distriktsgrænse med Hent/fortsæt. Der er ikke behov for at sende nøglen. Den konkrete aliasfejl er rettet og dækket af regressionstest; ejerens faktiske vej-/grænsehentning skal stadig bekræftes før W62 afsluttes. Main er stabil 1.11.1.
