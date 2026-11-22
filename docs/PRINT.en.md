# Printing and original forms

[Dansk](PRINT.md) · [First steps](FIRST-STEPS.en.md)

These controls are prepared on develop from beta.22. Stable 1.11.1 is updated separately.

## Territory cards

Open a card and choose **Print front** or **Print do-not-call back**. **Cards and addresses → Reprint** can print changed sides as a batch. Front and back have separate local profiles.

1. Start with **A4 · actual-size test**. Choose headings/lines or data only for preprinted stock.
2. Open **Dimensions and alignment** if needed. Defaults are 146 × 94 mm landscape for fronts and 94 × 146 mm portrait for backs. Orientation swaps width/height. Alignment allows offsets of up to 10 mm in each direction.
3. Uncheck **Remember these settings** for a one-off test. **Use default dimensions** displays defaults; saving only happens on **Preview and print** with the remember box checked.
4. Allow the popup, wait for image checks, and choose **Print / save PDF**. Use **100%**, disable headers/footers and turn off fit-to-page scaling.
5. Check dimensions, every street line and any QR code on paper. Missing images or overflowing content disable printing. Adjust the card or reopen printing.
6. Use **Approve after printing** only after checking the physical side. Opening a preview, saving PDF or saving a profile never automatically approves a reprint.

Changing the app language preserves the current fields, selections and measurements. Popup controls use the language selected when opened. Original forms, Danish form text, names and stored data are preserved. An open print window is a snapshot; reopen after changing the card.

Do-not-call backs contain private records. Handle printed pages and PDFs locally as private information. QR sharing still uses only the separately approved map image.

## Reports and S-13

Under **Reports and history**, choose **Calendar year**, **Service year** or **Last 12 months**. You can also select the specific calendar year. **Print complete report / PDF** includes the figures, map and S-13 data for the chosen period (or all three when explicitly selected).

The service-year appendix and **Download original completed S-13** use the unchanged original S-13 form and downloadable local PDF. For calendar years and rolling 12-month periods, the screen and the complete report instead show a clearly labelled **S-13 period extract** with the actual assignments, known previous completions and period-specific completion totals. **Print S-13 period extract / PDF** opens a standalone print view for that period. This is not an official S-13 service-year form.

Reports use A4 with 15 mm margins; wide map views may use landscape pages. Check the selected boundaries, assignment dates, completed dates and continuation pages. OSM map tiles must load for map reports; standalone period extracts do not require map tiles.

Duplicate clicks do not start a second preparation. Navigation or changed source data cancel stale print preparation. If profile saving fails, check save status and use **Refresh** when requested before retrying. Automated tests use invented data; physical printer calibration remains an owner check.

## Original form language

Card print options include English or Danish original forms. The saved choice belongs to that print side; otherwise the interface language is used. S-13 browser/PDF originals follow the interface language. Download the unmodified English originals through the print options. Existing Danish forms and stored names/date wording remain available.
