# LTM 1.14.0-beta.2

- **Gemning:** Undgår unødvendig genberegning af distriktsgrænsens adressetal ved udlevering og aflevering. Tidligere prøve med 16.000 fiktive adresser: klik til bekræftelse 669 → 164 ms ved udlevering og 668 → 166 ms ved aflevering med gennemgang. Video fra den virkelige installation før rettelsen viste ca. 3,3 og 3,5 sekunder; forbedringen på den installation er endnu ikke verificeret.
- **Synkronisering:** Særskilte forklaringer ved forbindelsesfejl, udløbet login, ubekræftet gemning og bekræftet gemning med forældet oversigt. Forbindelsesprøver gentager ikke skrivninger. Manuel opdatering/genåbning afviser at overskrive åbne kladder.
- **Daglig brug:** Genbrug kortvælgeren ved samlet udlevering af højst fem kort, med synlige valg og fjernelse. Større centreret gemmeindikator, venstrestillede knapper med kant og op til fem hyppigt valgte forkyndere.
- **Kort, filtre og mobil:** Større Kortoversigt med samlet betjening og direkte adgang til hele distriktet. Aktive filtre og nulstilling, sjældne valg under … Mere og et sammenklappeligt filterpanel med resultatantal på smalle skærme. Ombrydning af betjening og dialoger.
- **Forside:** Ens tekststørrelse for gennemgangstallene og tydelig gul målmarkering med matchende forklaring.
- **Rapportprint:** Undgår unødvendige netfliser ved direkte offlineprint, når rapportkortet ikke er åbnet. Fysisk iPad fra hjemmeskærmen og reel installationshastighed er fortsat uverificeret.

## English

- **Save latency:** Avoid unnecessary district boundary address-count recalculation when issuing and returning territories. Earlier test with 16,000 fictional addresses: click to confirmation 669 → 164 ms for issue and 668 → 166 ms for return with completion. A video from the real installation before the fix showed about 3.3 and 3.5 seconds; improvement on that installation remains unverified.
- **Synchronization:** Distinct guidance for connection failures, expired sessions, unconfirmed saves and confirmed saves with a stale overview. Connectivity checks do not replay writes. Manual refresh/reopening refuses to overwrite open drafts.
- **Daily work:** Reuse the card picker for batch issue of up to five cards, with visible selections and removal. Larger centered save indicator, left-aligned bordered actions and up to five frequently selected publishers.
- **Maps, filters and mobile:** Larger overview map with consolidated controls and direct access to the entire district. Active filters and reset, rare choices under More, and a collapsible filter panel with result count on narrow screens. Wrapping controls and dialogs.
- **Dashboard:** Consistent completion metric typography and a prominent yellow target marker with a matching legend.
- **Report printing:** Avoid unnecessary online tiles for direct offline printing when the report map has not been opened. Physical iPad home-screen use and real installation latency remain unverified.
