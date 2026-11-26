# Run LTM on your own computer

Download the complete **LTM-v…zip** package from [the latest stable release](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/latest), then extract it into a normal local folder. Install Python 3.9+ with SQLite. No runtime pip installation is needed. For ordinary local use, Mac/Windows [native installers](NATIVE-INSTALLERS.md) include Python. This guide covers legacy Python packages and private servers.

## New installation

In the extracted **Distrikt-lokal** directory, open `Start-LTM.cmd` on Windows, `Start-LTM.command` on macOS, or run `sh Start-LTM.sh` on Linux. From a source checkout the folder is called `distrikt` instead.

The startup menu offers local computer use or a private-network server. Some launcher prompts remain Danish; the browser app defaults to English for a new browser and also offers Danish. The original printed forms remain Danish.

Local mode binds to this computer. Private-server mode needs your private address and a local password. It has its own data directory and must remain on your home/congregation network or your own VPN. Do not expose the application directly to the public internet.

## Update an existing installation

Download private backups first, including the separate account backup if profiles are enabled. Stop the existing app, extract the full replacement program and preserve the installation's existing data directory. Keep the previous program folder until the replacement has been checked.

Legacy `Start-Distrikt` launchers still use their existing data path. Do not switch launch methods or select a different data root during an update without understanding the difference: an empty new directory is a different installation, not proof that records were deleted.

## Stable and beta are separate

Use stable for ordinary work. The [beta guide](BETA.md) explains the separate preview channel, data directories and login. Never point a beta at production data. Opening the normal stable launcher is not the same as launching a separately configured beta.

## Data, accounts and connections

Records are kept in the selected installation's local data directory. Take your own private backups and retain a recovery plan. Territory-data ZIPs, account backups and provider connections have different scopes; see [accounts and roles](USERS.en.md) and [privacy](PRIVACY.en.md).

A normal update of the same installation preserves its records. A new computer, new data root or restore is a deliberate operation. Do not copy runtime credentials into the source repository or public website.
