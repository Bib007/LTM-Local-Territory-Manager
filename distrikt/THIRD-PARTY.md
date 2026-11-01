# Medfølgende tredjepartskode

Leaflet: eksisterende lokalt bundlet kortbibliotek i app/vendor. BSD 2-Clause-licensen medfølger i app/vendor/Leaflet-LICENSE.txt. Bevar licens og copyrighttekst.

python-qrcode 8.2: https://pypi.org/project/qrcode/8.2/ — bundlet i app/vendor_py/qrcode til offline QR-matricer. BSD-licens medfølger i app/vendor_py/qrcode-8.2.dist-info/LICENSE. Ingen PIL/pypng kræves for appens SVG-QR-funktion. Koden er ikke en ekstern QR-tjeneste; QR-linket sendes ikke til en QR-udbyder.

## Lokal OCR i HA-betaen

HA-imaget installerer Tesseract OCR og danske/engelske sprogdata fra Alpine Linuxs pakkearkiv. Projekt: https://github.com/tesseract-ocr/tesseract. Tesseract og de valgte sprogdata bruger Apache-2.0; systempakkernes egne licenser og afhængigheder følger med i containerens pakkeoplysninger. Der medleveres ingen Tesseract-binærfil i desktop-ZIP'en. Ingen CDN, ekstern AI eller cloud-OCR bruges under genkendelse.
