# LTM 1.12.32

Målrettet Stable-rettelse af tre fejl i redigeringen. Ændringer fra den særskilte, igangværende DAR-preview-PR er ikke med.

- **Gem kort og vejliste:** Bekræftelsesdialogen forsvinder efter validering og genåbnes ikke, mens gemningen færdiggøres.
- **Kortkontrol:** Forældede kontrol- og hentefejl forsvinder ved skift af kort, tegning og ændringer i adressevalget. Et forsinket gammelt svar viser ikke fejlen igen.
- **Manuelle vejlinjer:** Autosave bevarer det aktive tekstfelt og markørens placering, så indtastningen ikke utilsigtet fortsætter i distriktnummeret.

Gemmekø, revisionskontrol, profilrettigheder og beskyttelse mod tab af nyere kladder bevares. Prøverne anvender kun fiktive data.

## English

Focused Stable fix for three editor issues. The separate DAR preview isolation work is not included.

- **Save card and street list:** The confirmation dialog closes after validation instead of reopening during the pending save.
- **Map checks:** Obsolete download/check messages clear when switching cards, drawing or changing address selections. Late old responses cannot bring them back.
- **Manual street lines:** Autosave retains the active input and caret position instead of redirecting typing to the territory-number field.

The ordered write queue, revision checks, profile permissions and protection of newer drafts remain intact. Tests use only fictional data.
