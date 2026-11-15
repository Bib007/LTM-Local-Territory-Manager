# LTM 1.12.19-beta.21 · Nye rummelige DAR-grænser

- **Grænseforslag:** En ny algoritme prøver brede, enkle polygoner før snævre forbindelser. Den giver mere plads omkring valgte adresser og færre unødvendige knæk, ligesom håndtegnede distrikter.
- **Ufarlige kortobjekter:** Kortlag, veje og bygninger uden kendt uvedkommende adresse er ikke længere automatisk forhindringer. Andre kendte adresser og deres bygninger beskyttes fortsat, og nabodistrikter giver afstand eller advarsel.
- **Test:** Kontroller både tætte villaveje og åbne landområder med fiktive adresser. Tegn manuelt, hvis der ikke findes et sikkert forslag. S-12's `(lige)`/`(ulige)` fra beta.20 er bevaret.

## English

- **DAR boundary proposal:** New generous, simpler outlines favor broad territories over thin corridors. Neutral mapped buildings and roads are not blockers, while other known addresses and neighboring territories remain protected or explicitly warned about.
- Review dense and rural examples before saving; draw manually when no safe suggestion exists. Beta.20's odd/even S-12 labels remain intact.
