# LTM 1.12.2 · Profiles, dependable saving and flexible imports

This stable release brings together the tested territory-workflow improvements from the beta series, including individual profiles and roles, preserved concurrent edits, flexible spreadsheet imports and clearer reports.

## What changes

- Manage accounts and your own roles in the application. Grant home/report summaries independently of detailed records; summaries do not reveal private names, IB, addresses or notes.
- Give each account a permission-filtered introduction and release news. Administrators can schedule a guide for the next login.
- Select the sheet, header row and columns for supported card/IB Excel or CSV imports, then review the normal preview before confirming. Leading zeros and safe numeric formats are preserved deliberately.
- Unchanged forms do not send redundant writes. Editors keep their own bases; independent changes can be combined, and conflicting saved proposals remain available for review.
- A confirmed write is not called rejected because the following overview failed. Unknown results still require checking before repetition.
- Finish the setup tour reliably. Review calendar-year, service-year and rolling-12-month reports with honest completion/assignment counts.
- Show safe manual street rows on approved online card fronts. Keep the same QR/file where supported; new content still requires approval. Only explicitly approved date updates run automatically.
- Explore administrator and territory-desk assistant examples in the fictional demo. English is the default for new users, with saved language choices preserved.

The main README and installation/account documentation are now English first. Translation remains partial: some interface/error text and the original S-12/S-13 forms remain Danish. English forms, OCR, automatic card division and native EXE/DMG installers are not included in this release.

## Update safely

Take a private territory-data backup and, if profiles are enabled, a separate account backup. Update the same installation while preserving its data directory. Review the visible role migration and current permissions after updating. Home Assistant stable keeps port 8787; the separate beta channel keeps its own port/data.

[Website](https://localterritorymanager.netlify.app) · [Demo](https://bib007.github.io/LTM-Local-Territory-Manager/) · [Installation](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.en.md) · [Accounts and roles](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/USERS.en.md)

The demo and website use fictional records and are separate from your installed system. Send only invented examples in feedback. Existing general HA, Drive and ordinary restore confirmations do not need to be repeated simply because this version was released.
