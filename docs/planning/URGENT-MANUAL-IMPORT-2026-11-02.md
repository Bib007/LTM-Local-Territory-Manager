# Priority −1 · manual Excel fronts/backs and street-line parsing

Source: owner's Drive Wishlist, 2 November 2026. Existing W131/W117/W127 follow-up; no new wish is counted.

Priority: **-1**.

## Full original request

> Foreslå adresser fra Dar udfra vejlinje, skal kunne se bort fra Noter som (kun ulige) osv
> skal kunne forstå at “hele vejen” betyder hele vejen ahha
> at der kan stå “23-25 & 24-26” og automatisk forstå hvad der er hvad ;)
> 
> 
> IB-import skal kunne lave manuel vejlinje, som så senere kan tilknyttes en rigtigt adresse….
> 
> 
> Man skal kunne uploade en forside og en bagside som excel, og få det ind i systemet uden at den skal være på en rigtig adresse fra dar systemet… forestil dig at man ikke gider bruge DAR systemet. så sjka man stadig ku lave for og bagsider ik?!

## Implementation for 1.12.6

- Whole-road wording, parity notes and joined street-side intervals are parsed into a reviewed suggestion. `kun ulige` retains its odd-only meaning; unknown restrictions are rejected.
- Manual do-not-call import is explicit and the default in the UI. Own-file column mapping and existing card numbering link fronts/backs without DAR or geographic addresses.
- Manual entries print normally and can be linked to one explicit address on the same card later, retaining record ID and date wording.
- Existing approvals, duplicate checks, permissions and original forms remain in place. The updated real-server browser scenario imports two Excel files, verifies no DAR download, renders both sides and performs later linking.
