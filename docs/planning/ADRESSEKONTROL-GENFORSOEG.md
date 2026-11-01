# W111 · adressekontrol og genforsøg · under udvikling

Ejerens fejlmelding og fulde prioritet står i [udviklingsplanen](OENSKELISTE.md). Referencebilledet bliver i Google-planens Bilag og lokalt. Billedet viser venten, men beviser ikke den underliggende kildefejl. Denne rettelse er **ikke med i den udgivne beta.77**.

## Implementeret og prøvet lokalt

- De første tre afbrydelser uden ny fremdrift kan genprøves ved næste kontroltrin, normalt inden for cirka ti sekunder, frem for altid at vente mindst 15 minutter.
- Efter gentagne fejl øges pausen fra ét minut til højst én time. Ny færdig fremdrift nulstiller serien. En kendt numerisk ventetid fra kilden bevares, også når kildeadapteren stopper sin korte interne genforsøgsrunde.
- Adgangs-/valideringsproblemer og øvrige vedvarende kildefejl giver en længere pause. Kildebeskeden vises, så brugeren kan se forskel på netfejl, venten og et problem, som skal rettes.
- En arbejdsrunde kan bruge op til tre timer. Tidsgrænsen kontrolleres mellem opslag, og ufuldstændigt arbejde genoptages efter en kort pause på samme checkpoint og samme snapshot. Et igangværende netopslag afsluttes inden dets normale timeout.
- Ved målt vedvarende ressourcepres udsættes baggrundsarbejdet et minut; et igangværende baggrundsforløb kan også vige ved næste sikre kontrolpunkt. Færdige udsnit bevares. Manglende målinger kaldes ikke sund drift.
- Visningen viser seneste afbrydelse, faktiske færdige/planlagte udsnit, gentagne afbrydelser uden fremdrift og tidspunkt for næste forsøg. En første kontrol, som venter på ressourcepres, forbliver synlig på forsiden.
- Deaktivering stopper fortsat arbejdet efter det aktuelle opslag. Afbrudte eller ufuldstændige hentninger må ikke erklære adresser fjernet. Ændringer kræver fortsat særskilt godkendelse; ingen generel revisionsafvisning er indført.

Ressourcekontrollen bruger Linux-kernens lokale [PSI-målinger](https://cdn.kernel.org/doc/html/latest/accounting/psi.html). Den læser 60-sekunders gennemsnit for ventetid på CPU, hukommelse og I/O. Det er systemets ressourcepres, ikke LTM's CPU-forbrug. Grænserne er konservative appvalg for at vige med baggrundsarbejde: CPU `some` 80 %, hukommelse `full` 10 %, I/O `full` 20 %. Der ændres ingen systemindstillinger, og der sendes ingen målinger ud af systemet. Manglende/ugyldige målinger bevares som utilgængelige. Dette er et lokalt grundlag for W110, ikke den endnu manglende HA-statusintegration eller notifikationsautomation.

## Kontrol

579 Python-prøver består med én forventet overspringning. Målrettede forløb dækker hurtige genforsøg, gentagne fejl, kildens ventetid, nulstilling ved afslutning, genstart med samme checkpoint, tre timers arbejdsrunde, ressourcepres, ukendte målinger og fortsat beskyttelse mod at fjerne adresser efter delvise svar. Alle oplysninger og kildesvar er opdigtede; der er ingen prøve med ejerens nøgle eller installation.

JavaScript-suiten og 16 pakkeprøver består. Browserforløbet for adresseopgaven består på 320/390/768/1440 px, inklusive synlig kildebesked, faktiske deltal, escaped tekst og synlig første ressourcepause. GitHubs fulde kontrol af denne ændring mangler før frigivelse. W111 tæller derfor fortsat som åben. Senest verificerede offentlige beta er **1.12.2-beta.77**; stabil er **1.12.1**.
