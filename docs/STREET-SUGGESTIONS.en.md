# Suggest addresses from an existing street list

Available from LTM 1.12.5. This uses the existing Danish DAR download connection and the same geographic editing permissions. It does not divide the congregation territory automatically.

1. Open a card and choose **Draw and select addresses**.
2. Choose **Suggest DAR addresses from street lines**. Confirm the four-digit postcode for every displayed street line. A postcode is prefilled only when the card already has one unambiguous value for that street.
3. Choose **Suggest addresses**. Complete streets already downloaded locally are reused without a new DAR request; only missing streets are downloaded through the authenticated source. To update locally downloaded streets, check **Refresh all streets from DAR** before continuing. An individual address import or partial download is not considered a complete street. All apartments within each selected number range are included. Previewing and downloading do not modify the card.
4. Compare the selected units and visit total with the original street list. Inspect and adjust the proposed outline; an outline around addresses does not establish geographic continuity or physical boundaries.
5. Choose **Save addresses on card**, review the confirmation and save. The same card number, assignments, completions and do-not-call entries are retained. The front is marked for print review.

From 1.12.6, supported ranges include `1–19`, `2–20 (even)`, `1A–9B (odd)`, and comma/semicolon-separated ranges or single house numbers. Danish `(lige)`, `(ulige)`, `(kun lige)` and `(kun ulige)` are supported and retain their even/odd meaning. `hele vejen` / `whole street` selects the complete downloaded road, including every apartment. A qualifier can restrict that whole road to one side. With `&`, `og` or `and`, same-parity range endpoints describe a side: `23-29 & 24-26` selects odd 23–29 and even 24–26; it does not add even 28. An ordinary single unqualified range still includes both parities. All known apartment units at a selected house number stay together. Unclear wording is rejected; correct the street line or select addresses manually.

Every street line must produce active addresses from a complete road download. Reserved, ignored or retired units block the suggestion. Changed street lines or address data invalidate its approval. No address is guessed from a neighbouring street or an unspecified postcode. A source failure retains downloaded public data without silently applying a partial card.

For do-not-call dates, use the optional **Date as text** field for `March 2024`, `2024` or another wording when an exact day is unknown. In import, map the date column normally and review its warning. The wording is displayed on the back; no completion date is created. Original S-12/S-13 forms retain their language.
