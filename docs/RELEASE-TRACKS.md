# Independent release tracks

LTM has one source tree and one version number. A version may be released to
each of these tracks at different times:

1. Home Assistant
2. macOS app
3. macOS server
4. Windows app
5. Windows server

No normal merge publishes anything. A maintainer must manually select one
track from the **Stable release tracks** workflow on the exact `main` commit.
That run requires the full common checks and only the selected track's own
platform checks. Therefore Home Assistant never waits for an available Mac or
Windows runner, and an unavailable desktop runner never blocks a Home
Assistant update.

## Package format for the first independent releases

Until native installers have been designed and reviewed, every desktop track
is a reproducible, platform-labelled ZIP containing the shared Python app.
It is intentionally not presented as a DMG or EXE. macOS packages contain
only `.command` launchers; Windows packages contain only `.cmd` launchers.

- **App** packages start local-only use directly and keep their data outside
  the extracted program folder.
- **Server** packages guide the user through a private LAN/VPN address and
  server password. They do not open a public listener.
- **Home Assistant** is a source package for the existing add-on repository.
  It is not copied into an active installation by hand.

Every asset has its own adjacent SHA-256 file and an in-package `SHA256SUMS`
manifest. Existing release assets are immutable: a second upload with the
same name fails instead of replacing a file.

## Before a later release

1. Keep the version, app configuration and changelog synchronized in the
   common source.
2. Run the common checks on the precise `main` commit.
3. Run the selected track manually. Confirm its own platform result and
   publicly downloaded ZIP/checksum before reporting that track released.
4. For macOS, make a physical Apple Silicon launch/restart check before the
   first independent macOS publication. `macos-15-intel` remains the hosted
   Intel check only; it does not prove Apple Silicon behaviour.
5. Consider native DMG/EXE creation and in-app update notifications as a
   separate future design task. They are not implied by these ZIP packages.

## Dansk kort fortalt

Der er ét fælles versionsnummer, men fem pakker kan udkomme hver for sig.
Home Assistant behøver kun fælles prøver og sin egen HA-prøve. Mac og Windows
udkommer først efter deres egne prøver. De første særskilte desktoppakker er
ZIP-filer med Python, ikke DMG eller EXE; ægte Apple-Silicon-prøve kræves
før den første Mac-udgivelse.
