# S-12 – finjustering af layout (udviklingsfunktion)

[English](S12-LAYOUT.en.md)

**Ikke udgivet i Stable.** Indstillingerne er knyttet til den lokale menigheds eksisterende printprofil for forsiden og gemmes separat for dansk og engelsk S-12.

Åbn **Print forside → Mål og placering → S-12 · justér tekst og QR**. Justér kortnavn, kortnummer og vejliste i X/Y, hver inden for ±2 mm. Tekst har skala 95–105 %. QR-koden må flyttes ±2 mm, men beholder den oprindelige fysiske størrelse af hensyn til læsbarhed. Nulstil S-12-felter fører felterne tilbage til skabelonens udgangspunkt. Den eksisterende indstilling for at forskyde hele kortet er uændret.

**A4 · prøve i rigtig størrelse** viser A4 (210 × 297 mm) med kortet centreret i den printbare flade og mindst 10 mm nominelt frirum. Udskriv ved **100 %**, uden sidehoved/-fod og uden printerens »tilpas til side«. Browseren blokerer udskrivning ved målt overlap, afskæring eller manglende QR. De originale formularfelter må kontrolleres visuelt, fordi det originale rastertryk kan variere med det valgte skabelonsprog.

Eksisterende profiler uden `s12_layout` beholder alle udgangskoordinater. Den eksisterende private settings-database, backup og eksport bevarer indstillingerne; der er ingen ny SQLite-fil eller automatisk migration.

## Udvikling og test

Berørte kontrakter: `print.profile.save` (validerer `s12_layout.da|en`), `printing.js`, `s12-layout.js`, `server.py` og print-/billedgenereringen. Delt ændringspunkt med andre PR'er: `store.py`. Test på fiktive data: `test_s12_layout.py`, `test_s12_layout.cjs` og den eksisterende frontend- og printbrowser-suite. Fysisk QR-scanning, papirtolerance og Mac-/Windows-printerdrivere kræver særskilt accept før merge.
