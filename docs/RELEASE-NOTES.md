# LTM 1.12.33

Målrettet Stable-rettelse af en scrollfejl under gemning. Øvrige udviklingsændringer, herunder den særskilte DAR-preview-PR, er ikke med.

- **Gemning og autosave:** Siden hopper ikke ned, og lange redigeringsdialoger mister ikke deres scrollposition, når gemningen skifter dialogen fra modal til ikke-modal. Det aktive tekstfelt og markøren bevares.
- **Test:** Browserregression med tilbageholdt gemmesvar kontrollerer både side- og dialogscroll, fokus og tekstmarkør med fiktive data.

Gemmekø, revisionskontrol, profilrettigheder og beskyttelse af nyere kladder er uændret. macOS-serverens særskilte fysiske testgate gælder fortsat.

## English

Focused Stable fix for a scroll jump during saving. Unrelated development work, including the separate DAR preview change, is excluded.

- **Save and autosave:** Preserve document and long-dialog scroll positions when switching a modal into a modeless background-save editor. Keep input focus and caret intact.
- **Testing:** Real-browser regression holds the save response and verifies both scroll positions and text focus with fictional data.

The ordered write queue, revision controls, permissions and protection of newer drafts remain unchanged. The separate physical macOS-server verification gate still applies.
