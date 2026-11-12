# Opdelingsforslag (udviklingsfunktion)

[English](SPLIT-SUGGESTIONS.en.md)

**Ikke udgivet i Stable.** På **Distriktskort** vises et aktuelt antal kort med kendte besøgstal over menighedens grænse. Grænsen indstilles i **Indstillinger → Menighed og mappe → Maksimalt antal besøg pr. distriktskort** (1–1.000). Den påvirker kun forslag; den ændrer hverken eksisterende kort, standarden for automatisk kortoprettelse eller udleveringer.

I opdelingsforslagene kan administrator vælge **Se bort fra forslag**, skrive en begrundelse (1–300 tegn) eller **Gendan forslag**. En ignoreret vurdering knyttes til kort-ID, kortnummer, aktuel grænse, besøgstal og sorteret adressetilknytning. Ændres disse forhold, tæller det nye forslag igen. Ikke-administratorer får ikke begrundelsen i deres profildata.

Listerne viser mulige adresseflytninger til egnede kort i samme område/type/vej samt opdeling til nyt kort med antal før/efter. Forslag anvendes aldrig automatisk; de eksisterende formularer, serverforhåndsvisninger og særskilte bekræftelser anvendes. Et fælles vejnavn beviser **ikke** fysisk geografisk sammenhæng; den skal kontrolleres manuelt før godkendelse.

## Afhængigheder og kontrol

Ændrer `settings.save`, nye mutationer `split.suggestion.ignore` og `split.suggestion.restore`, profilrettigheder, `split-suggestions.js`, `workspace.js` og `app.js`. Alt lagres i eksisterende lokale `settings` SQLite, ikke en global/cloud-tabel. `store.py` er delt konfliktpunkt med S-12-PR'en. Tests på fiktive data: `test_split_limit.py`, `test_split_limit.cjs` og eksisterende split-, geografi-, HTTP- og browserprøver. Kombination af udvalgte besøg fra to kilder til et nyt kort er ikke implementeret i denne PR.
