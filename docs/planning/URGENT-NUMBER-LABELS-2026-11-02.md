# Critical street-number labels, 2 November 2026

Owner priority: -1. Follow-up to existing street-line work; no extra completion credit.

Full request:
> hvorfor skriver dne det sådan her?
> der skal da ikke være et lige nummer i linje 2? hvad går der lige galt?
>
> den skriver heller ikke alle numre på og sårn!!!! FIX!

The original attached screenshot remains preserved in the private Drive source and local snapshot. It shows street labels with mixed endpoint parity and omitted intermediate house numbers. Do not publish owner location data as fixtures.

Cause: geographic rows grouped by street/postcode/property type and reduced membership to first/last labels. Fix: split parity, preserve gaps and suffixes, bound long rows, retain exact units/counts. Existing geographic cards regenerate labels from saved units and require front print review. Manual rows and original forms are preserved.

Targeted validation: 19 geographic tests and 9 street suggestion tests, including fictional mixed sides, gaps, suffixes, long rows and idempotent startup repair. Stable 1.12.6 was not published when this follow-up began: the main release Mac job had no runner and no steps, then was cancelled after approximately 15 minutes. No old release retry is started before this correction.
