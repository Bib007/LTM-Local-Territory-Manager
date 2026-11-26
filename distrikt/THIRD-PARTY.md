# Medfølgende tredjepartskode

Leaflet: eksisterende lokalt bundlet kortbibliotek i app/vendor. BSD 2-Clause-licensen medfølger i app/vendor/Leaflet-LICENSE.txt. Bevar licens og copyrighttekst.

python-qrcode 8.2: https://pypi.org/project/qrcode/8.2/ — bundlet i app/vendor_py/qrcode til offline QR-matricer. BSD-licens medfølger i app/vendor_py/qrcode-8.2.dist-info/LICENSE. Ingen PIL/pypng kræves for appens SVG-QR-funktion. Koden er ikke en ekstern QR-tjeneste; QR-linket sendes ikke til en QR-udbyder.

## Lokal OCR i HA-betaen

HA-imaget installerer Tesseract OCR og danske/engelske sprogdata fra Alpine Linuxs pakkearkiv. Projekt: https://github.com/tesseract-ocr/tesseract. Tesseract og de valgte sprogdata bruger Apache-2.0; systempakkernes egne licenser og afhængigheder følger med i containerens pakkeoplysninger. Der medleveres ingen Tesseract-binærfil i desktop-ZIP'en. Ingen CDN, ekstern AI eller cloud-OCR bruges under genkendelse.

## Browser connection-backup fallback

`app/vendor/connection-crypto.js` bundles @noble/ciphers 2.4.0 (AES-GCM) and @noble/hashes 2.4.0 (PBKDF2-SHA256), MIT. License files accompany the bundle. Uses the existing v1 format, 600,000 iterations, 256-bit key, random 16-byte salt and 12-byte nonce. Native WebCrypto remains preferred. The fallback is local, including on private HTTP LAN access, and never sends the passphrase to the server. Browser `crypto.getRandomValues` remains mandatory.

Rebuild with Node 24: `npm ci --prefix scripts/connection-crypto`, then `scripts/connection-crypto/node_modules/.bin/esbuild scripts/connection-crypto/entry.js --bundle --format=iife --global-name=ConnectionCryptoFallback --target=es2020 --outfile=distrikt/app/vendor/connection-crypto.js`.

Upstream: https://github.com/paulmillr/noble-ciphers and https://github.com/paulmillr/noble-hashes.
