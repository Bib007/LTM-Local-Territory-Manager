# Beta.78 · præcis verificering

31.10.2026 · [offentlig udgivelse](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/tag/v1.12.2-beta.78)

- Udgivelsescommit og tag: `e591b684854e58698df6dcd7e9ac83ba38356d5b`.
- Filtræ: `d38381a23cd1a6132ecb332e0b75192cdefcf1bc`.
- Checks: [41230111622](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41230111622), completed/success.
- Platformskontrol: [41230111642](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41230111642), completed/success.
- HA beta release: [41230111692](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41230111692), completed/success.
- Alle tre kørsler gælder samme præcise udgivelsescommit. Ingen kontrol er sprunget over. Den nye HA-blueprintkontrol er også et krav før publicering.

Python 3.9/3.12/3.13, JavaScript, Chromium/WebKit, Mac, Windows, HA, pakker, demo/designmanifest, arkivopstart og de sædvanlige statiske-/afhængighedskontroller består. 586 Python-prøver (én forventet overspringning), 16 pakkeprøver og fem betapakkeprøver består også lokalt. Home Assistant 2026.10.4's faktiske skemaer og skabeloner dækker begge kanaler, alle beskedtyper, bogstavelige egne noter og aktuelle/forældede/manglende livstegn. Codex Security er ikke kørt.

## Offentlige pakker

Begge filer er hentet fra udgivelsen og sammenlignet **byte for byte** med lokale bygninger fra det identiske filtræ. Begge offentlige kontrolsumfiler er også kontrolleret.

| Fil | Bytes | SHA-256 |
| --- | ---: | --- |
| LTM-HA-v1.12.2-beta.78.zip | 1261268 | `105b3a3b9b9acb8ba6fb023e38f84d7b3497266d11cd08e440108183ad5d6b79` |
| LTM-v1.12.2-beta.78.zip | 3659718 | `bfe77310181f596babc90732cf0d4fec85b4f5bfc3115ffde009a105ac52a3a0` |

Betakanalen er `43ad572653e41037556882550c09b3651f7e6112`; alle **146 filer** er sammenlignet byte for byte med den lokale kanalbygning fra udgivelseskilden. Stabil/main er fortsat `bd47cc824638e653522f2d2badef2da91b14f613`, version 1.12.1. Port 8787, stabilt login og stabile data er ikke opdateret af denne beta. Beta har fortsat port 8788, eget login og egne data.

## Faktisk leveret

W111: Hurtige begrænsede genforsøg, længere pauser efter gentagne afbrydelser, bevaret numerisk kildeventetid, genoptagelige længere arbejdsrunder, ressourcepause og synlige årsager/deltal. Ufuldstændige hentninger bliver ikke til automatisk sletning af adresser. Den konkrete årsag på ejerens installation er ikke udledt af det gamle skærmbillede.

W110: Begrænset lokal driftsstatus, adskilte kanaloplysninger, importklar HA-beskedopskrift, valg af telefon/noter i HA og en udtrykkelig, begrænset prøvevej. Normale pauser er ikke fejl. Manglende ressourcemålinger bliver ikke påstået sunde. [Opsætning, måling, ny Core-API-rettighed og begrænsninger](../HA-DRIFTSSTATUS.md).

Ejerens HA og telefon er ikke åbnet, og udviklingen har ikke sendt en besked til ejerens enhed. Den konkrete nye opsætning/prøve står klar i Dine svar og prøver. De allerede godkendte generelle HA-, Drive- og datagendannelsesprøver gentages ikke.

W110/W111 tæller nu som frigivet. W65 er fortsat åben til stabilslutkontrol. W106–W108 og W117 mangler før næste stabile. IB fra Excel er efterfølgende under udvikling; det er **ikke** med i beta.78. OCR, W16 og øvrige pause-/parkeringsaftaler er uændrede. Der er ikke publiceret en ny stabil version.
