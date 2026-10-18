# LTM 1.12.0-beta.32

Ét ønskepunkt: W50. Ændringerne fra beta.30 og beta.31 er med.

- Opgaver er nu den eneste funktion til opfølgning. Gamle noter bliver opgaver med bevaret tekst, datoer, kortreference og udført-status, både ved genstart og ved godkendt import af en gammel backup. En importforhåndsvisning ændrer intet.
- Navigationen viser kun antal åbne opgaver. Kort med åbne opgaver markeres i kortlisten/mappen, og udleveringsformularen viser en tydeligere advarsel med opgaveteksten. Udførte opgaver tælles ikke med. Ingen ny udleveringsspærring og ingen automatisk IB-ændring.
- Separate notefiltre og valg mellem note/opgave er fjernet. Opgaver kan være generelle eller knyttet til et kort; redigering bevarer også en eksisterende tilknytning til et arkiveret kort. ○ markerer udført, ✓ genåbner. Ved aflevering/gennemgang kan du stadig skrive en valgfri opgave.
- Gamle fil-/API-navne bevares, så eksisterende sikkerhedskopier stadig fungerer. Aktivitetshistorik konverteres ikke til opgaver. Tests bruger kun opdigtede poster; ingen private oplysninger er lagt i GitHub.

Tag fortsat en privat backup før opdatering. Ejerens faktiske API-hentning skal stadig prøves med rettelsen fra beta.30; grøn forbindelse alene er ikke nok. W61's GitHub-cache/PR-restoprydning og udgivelsesmetadata er stadig åbne. HA-sikkerhedsprofil og login er uændrede; W06 og den afhængige nøglebackup W56 er ikke færdigmeldt. Main er stabil 1.11.1.
