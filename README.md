<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/logo-dark.svg">
  <img alt="LTM · Local Territory Manager" src="assets/brand/logo-light.svg" width="580">
</picture>

# Dine distriktskort. Ét samlet overblik.

**Hold styr på kort, udleveringer og gennemgange — med dine registreringer på dit eget system.**

LTM er et gratis, uofficielt værktøj til distriktsarbejdet i Jehovas Vidners menigheder. Se, hvilke kort der er ude, find et ledigt kort, og registrer en aflevering samme sted. Du kan begynde med de papirkort, du allerede har, og tilføje adresser og korttegning senere.

**[Prøv demoen](https://bib007.github.io/LTM-Local-Territory-Manager/) · [Kom i gang](docs/INSTALL.md) · [Idéer og feedback](https://tally.so/r/KpY0ZV)**

Demoen åbner uden installation eller konto og viser opdigtede eksempler.

## Mere overblik i det daglige

- **Find det rigtige kort.** Se kort i mappen, kort i kassen og kort, som er udleveret.
- **Registrer udlevering og aflevering.** Find en forkynder, vælg et kort, og behold historikken samlet.
- **Kom i gang med dine eksisterende kort.** Start med kortnumrene, eller indlæs en liste fra Excel. Guiden hjælper dig videre.
- **Arbejd med adresser og kort.** Tegn grænser, vælg adresser, og få overblik på et samlet kort.
- **Print, når du har brug for det.** Lav kortforsider, IB-bagsider, S-13 og oversigter.
- **Husk næste opgave.** Gem noter og opfølgning ved kortene, og følg med i gennemgangene.

## Se LTM i brug

Skærmbillederne viser programmet med opdigtede eksempler.

**Overblik over kortene og de næste opgaver**

![LTM-forsiden med kortstatus, gennemgange og opgaver](assets/screenshots/overblik.png)

**En enkel arbejdsgang til udlevering og aflevering**

![Daglig brug i LTM med valg af kort og forkynder](assets/screenshots/udlevering.png)

**Kortets oplysninger samlet ét sted**

![Et opdigtet distriktskort med oplysninger og adresser](assets/screenshots/distriktskort.png)

## Vælg, hvordan du vil bruge LTM

**Seneste stabile udgave: 1.12.0**

| Brug LTM på | Sådan kommer du i gang |
| --- | --- |
| **Home Assistant** | Tilføj LTM, og installer appen **Distrikt**. Du kan derefter åbne den samme installation fra din computer, telefon eller iPad derhjemme. |
| **Mac eller Windows** | Hent programpakken, pak den ud, og følg startvejledningen. Du skal installere Python én gang, hvis det ikke allerede er på computeren. |

[![Tilføj LTM til Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FBib007%2FLTM-Local-Territory-Manager)

**[Hent til Mac og Windows](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/latest) · [Trin for trin](docs/INSTALL.md) · [Første gang med LTM](docs/FIRST-STEPS.md)**

Har du allerede LTM? Hent en privat sikkerhedskopi i appen, før du opdaterer, og følg [opdateringsvejledningen](docs/INSTALL.md). Bruger du prøveudgaven, har den sine egne data; de flyttes ikke automatisk til den stabile app.

## Dine registreringer bliver hos dig

Kort, forkyndere, IB, udleveringer og noter gemmes på den computer eller Home Assistant, hvor du kører LTM. Der kræves ingen LTM-konto eller abonnement, og appen sender ikke brugsstatistik til udvikleren.

Kortbaggrunde og adresseopslag bruger internettet. Du kan desuden vælge at dele et gennemgået kortbillede via Google Drive, så det kan åbnes med en QR-kode. Det er et tilvalg: databaser, forkyndere, IB-lister og udleveringshistorik sendes ikke med kortbilledet. Alle med et åbent billedlink kan se og videresende billedet.

**Tag sikkerhedskopier i selve LTM. Home Assistants almindelige backup indeholder ikke LTM's registreringer.**

[Privatliv og deling](docs/PRIVACY.md) · [Sikkerhedskopiering og flytning](docs/INSTALL.md#backup-flytning-og-tilbageførsel)

## Spørgsmål, før du går i gang

**Skal alle mine papirkort være lagt ind først?**

Nej. Start med kortnumrene og de kort, der allerede er udleveret. Adresser og korttegning kan komme senere.

**Skal jeg have Home Assistant?**

Nej. Du kan også bruge LTM på en Mac eller Windows-computer.

**Kan jeg bruge min telefon eller iPad?**

Ja, de kan åbne den samme installation på hjemmenetværket. Vil du bruge den udefra, kræver det en forbindelse til dit hjemmenetværk via din egen VPN. Se [vejledningen](docs/INSTALL.md#brug-mobilen-udefra).

**Kan jeg tage eksisterende oplysninger med?**

Du kan indlæse kort fra en Excel-liste og hente gennemgange og udleveringer fra de understøttede S-13-filer. Du ser og godkender oplysningerne, før de gemmes. [Kortimport](docs/KORTIMPORT.md) · [S-13-import](docs/DAILY-WORKSPACE.md).

**Findes LTM på engelsk?**

Dansk er hovedsproget. Du kan vælge engelsk i appen, men enkelte tekster og de originale formularer er fortsat danske.

## Har du en idé eller fundet en fejl?

Brug [Idéer og feedback](https://tally.so/r/KpY0ZV). Du behøver ingen konto eller e-mailadresse, og du kan vedhæfte billeder. Send kun opdigtede eksempler, uden rigtige personoplysninger, IB, sikkerhedskopier eller adgangskoder. Det, du selv indsender, gemmes hos Tally.

## Om projektet

LTM er et uofficielt projekt og er ikke udgivet eller godkendt af Jehovas Vidner, jw.org, JW HUB eller Home Assistant. Det udvikles med hjælp fra OpenAI Codex. Koden er frit tilgængelig; [licens](LICENSE) og [oplysninger om de medfølgende materialer](distrikt/THIRD-PARTY.md) kan læses her.

[English](README.en.md) · [Vejledninger og begrænsninger](docs/LIMITATIONS.md) · [Nyheder i 1.12.0](docs/RELEASE-NOTES.md) · [Billede til deling](assets/screenshots/deling.png) · [Bidrag til projektet](CONTRIBUTING.md)
