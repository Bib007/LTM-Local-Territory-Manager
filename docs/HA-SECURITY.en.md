# HA security · scoped review

17 October 2026 · source c0528c9 · [Dansk](HA-SIKKERHED.md)

This review covers the HA configuration, startup script, container and existing access controls. It uses public code and passing fictional program/LAN tests. The owner's installed Supervisor, network, accounts and data were not accessed. This is not an exhaustive vulnerability scan.

| Area | Current implementation |
| --- | --- |
| Host access | No host network, privileged capabilities, Docker socket, hardware devices or additional host directories. |
| HA APIs | Supervisor and Home Assistant APIs are disabled; no elevated API role. |
| Browser access | Private mapped port 8787, beta 8788, own LAN/VPN login, no ingress. Direct HTTP provides no transport encryption itself. |
| Confinement | No disabled AppArmor/protection mode; no app-specific AppArmor profile. Actual loading has not been inspected on the owner's HA. |
| Credentials | New HA passwords require 12 characters; local salted PBKDF2/SHA-256 verifier, private files and expiring sessions. A masked HA password option does not encrypt its options file against HA administrators. |
| HTTP controls | Private client ranges, Host/Origin checks, session and API token, HttpOnly/SameSite cookie and CSP; covered by existing HTTP/LAN tests. A private IP alone is not authentication. |
| Backups | Application data is excluded from HA backups; use the app's private backup. Portable backups omit credentials. |

The current official rating reference starts at 5 and adds bonuses for features such as ingress or a loaded custom AppArmor profile. LTM has a mapped port, its own login and no custom profile, so its **configuration calculates to 5 under the current formula**. The rating displayed by the owner's Supervisor was not read; older versions may present the scale differently. This calculation is not a complete application security assessment.

Next candidates are an app-specific AppArmor profile tested in an isolated HA beta, then a separately planned non-root process/data-ownership migration. A profile must cover Python, SQLite/WAL, program/template reads, app-data and temporary writes, network access, restore, QR/PDF and integrations. No untested profile has been enabled.

Ingress or HA authentication would change login, URLs, Origin/CSP checks and OAuth flows. These are larger changes requiring an owner agreement before implementation, while retaining desktop support and the agreed LAN/VPN behavior. HTTPS can be considered with that architecture; no internet exposure has been introduced.

This review changes no privileges, login architecture or data permissions. W06 remains open for a tested implementation. Publisher suggestions (W15) can proceed independently.

Primary references: [rating, updated 12 October 2026](https://contributors.home-assistant.io/apps/reference/security-rating/), [security guide](https://contributors.home-assistant.io/apps/guides/security/), [configuration defaults](https://contributors.home-assistant.io/apps/reference/configuration/).
